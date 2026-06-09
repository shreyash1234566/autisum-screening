import 'dart:async';
import 'package:flutter/services.dart';
import '../constants/task_config.dart';
import '../models/session.dart';

/// Communicates with the native Android MediaPipe Face Landmarker.
/// Native code lives in MediaPipeHandler.kt
class MediaPipeService {
  static const MethodChannel _channel =
      MethodChannel('autism_screening/mediapipe');
  static const EventChannel _gazeStream =
      EventChannel('autism_screening/gaze_stream');

  StreamController<GazeDataPoint>? _gazeController;
  Stream<GazeDataPoint>? _gazeStreamBroadcast;
  StreamSubscription? _nativeSub;

  bool _isRunning = false;
  final List<GazeDataPoint> _buffer = [];

  Future<void> startTracking() async {
    if (_isRunning) return;
    _isRunning = true;
    _buffer.clear();

    _gazeController = StreamController<GazeDataPoint>.broadcast();
    _gazeStreamBroadcast = _gazeController!.stream;

    _nativeSub = _gazeStream.receiveBroadcastStream().listen((dynamic raw) {
      final map = Map<String, dynamic>.from(raw as Map);
      final point = _parseGazePoint(map);
      _buffer.add(point);
      _gazeController?.add(point);
    });

    await _channel.invokeMethod('startTracking');
  }

  Future<void> stopTracking() async {
    if (!_isRunning) return;
    _isRunning = false;
    await _channel.invokeMethod('stopTracking');
    await _nativeSub?.cancel();
    _gazeController?.close();
  }

  List<GazeDataPoint> consumeBuffer() {
    final copy = List<GazeDataPoint>.from(_buffer);
    _buffer.clear();
    return copy;
  }

  Stream<GazeDataPoint>? get gazeStream => _gazeStreamBroadcast;

  // ─────────────────────────────────────────────────────────────────────────
  // Parse raw map from native MediaPipe Face Landmarker.
  //
  // Native side (Kotlin) sends a Map with keys:
  //   timestamp_ms, left_iris_x, left_iris_y, right_iris_x, right_iris_y,
  //   left_eye_outer_x, left_eye_inner_x, right_eye_inner_x, right_eye_outer_x,
  //   head_yaw, head_pitch, blink_ear
  //
  // Gaze ratio algorithm:
  //   iris_center_x = mean(left_iris_x, right_iris_x) in normalised [0,1]
  //   Horizontal: 0 = full left, 0.5 = center, 1 = full right
  //   Social content is on LEFT half of split screen (Task A)
  // ─────────────────────────────────────────────────────────────────────────
  GazeDataPoint _parseGazePoint(Map<String, dynamic> map) {
    final double leftIrisX  = (map['left_iris_x']  as num).toDouble();
    final double rightIrisX = (map['right_iris_x'] as num).toDouble();
    final double leftIrisY  = (map['left_iris_y']  as num).toDouble();
    final double rightIrisY = (map['right_iris_y'] as num).toDouble();

    // Average both eyes for stable estimate
    final double gazeH = (leftIrisX + rightIrisX) / 2.0;
    final double gazeV = (leftIrisY + rightIrisY) / 2.0;

    return GazeDataPoint(
      timestampMs: (map['timestamp_ms'] as int),
      gazeRatioHorizontal: gazeH,
      gazeRatioVertical: gazeV,
      headYawDegrees: (map['head_yaw'] as num).toDouble(),
      headPitchDegrees: (map['head_pitch'] as num).toDouble(),
      blinkEar: (map['blink_ear'] as num).toDouble(),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // SOCIAL PREFERENCE RATIO
  // Source: Perochon et al. 2023, NEJM Evidence — Table 2
  // social_ratio = frames_looking_left / total_frames
  // Left half of screen = social content (character face)
  // Typical mean: 0.61 (SD 0.12)
  // ASD mean:     0.38 (SD 0.14)
  // ─────────────────────────────────────────────────────────────────────────
  static double computeSocialPreferenceRatio(List<GazeDataPoint> taskAGaze) {
    if (taskAGaze.isEmpty) return 0.5;
    final social = taskAGaze
        .where((p) => p.gazeRatioHorizontal < 0.5)
        .length;
    return social / taskAGaze.length;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // NAME RESPONSE DETECTION
  // Head yaw change > 15 degrees toward center within 3-second window
  // Source: Bradshaw et al. 2018, Autism Research
  // ─────────────────────────────────────────────────────────────────────────
  static bool detectNameResponse({
    required List<GazeDataPoint> gazeData,
    required int nameCalledAtMs,
  }) {
    const int windowMs = TaskConfig.taskBResponseWindowSeconds * 1000;
    final windowPoints = gazeData.where((p) =>
        p.timestampMs >= nameCalledAtMs &&
        p.timestampMs <= nameCalledAtMs + windowMs);

    if (windowPoints.isEmpty) return false;

    final baselinePoints = gazeData.where((p) =>
        p.timestampMs >= nameCalledAtMs - 2000 &&
        p.timestampMs < nameCalledAtMs);

    if (baselinePoints.isEmpty) return false;

    final baselineYaw = baselinePoints
        .map((p) => p.headYawDegrees)
        .reduce((a, b) => a + b) / baselinePoints.length;

    // Detect any yaw change > 15° toward center (yaw moves toward 0)
    return windowPoints.any((p) =>
        (p.headYawDegrees - baselineYaw).abs() >
        TaskConfig.headOrientationThresholdDegrees);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // BLINK RATE (blinks per minute)
  // Eye Aspect Ratio threshold: 0.20 (Soukupová & Čech, 2016)
  // Typical: 15-20 bpm; ASD may differ
  // ─────────────────────────────────────────────────────────────────────────
  static double computeBlinkRate(List<GazeDataPoint> gazeData) {
    if (gazeData.length < 2) return 0;

    int blinkCount = 0;
    bool wasClosed = false;

    for (final p in gazeData) {
      final closed = p.blinkEar < TaskConfig.blinkEarThreshold;
      if (closed && !wasClosed) blinkCount++;
      wasClosed = closed;
    }

    final durationMs = gazeData.last.timestampMs - gazeData.first.timestampMs;
    final minutes = durationMs / 60000.0;
    return minutes > 0 ? blinkCount / minutes : 0;
  }
}
