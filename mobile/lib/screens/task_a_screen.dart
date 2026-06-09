import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/task_config.dart';
import '../models/session.dart';
import '../services/mediapipe_service.dart';
import '../widgets/animated_character.dart';

/// TASK A — Social Preference Test (60 seconds)
/// Split screen: social face LEFT / spinning toy RIGHT
/// Source: Perochon et al. 2023 (SenseToKnow protocol)
class TaskAScreen extends StatefulWidget {
  final MediaPipeService mediaPipeService;
  final void Function(List<GazeDataPoint> gazeData) onComplete;
  const TaskAScreen({super.key, required this.mediaPipeService, required this.onComplete});

  @override
  State<TaskAScreen> createState() => _TaskAScreenState();
}

class _TaskAScreenState extends State<TaskAScreen> with TickerProviderStateMixin {
  late AnimationController _spinCtrl;
  late AnimationController _colorCtrl;
  late Animation<double> _spinAnim;
  late Animation<Color?> _colorAnim;

  int _secondsLeft = TaskConfig.taskADurationSeconds;
  Timer? _timer;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _spinCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))..repeat();
    _spinAnim = Tween<double>(begin: 0, end: 1).animate(_spinCtrl);
    _colorCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 2000))..repeat(reverse: true);
    _colorAnim = ColorTween(begin: const Color(0xFFFF6B6B), end: const Color(0xFF4ECDC4)).animate(_colorCtrl);
  }

  void _start() {
    setState(() => _started = true);
    widget.mediaPipeService.startTracking();
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return;
      setState(() => _secondsLeft--);
      if (_secondsLeft <= 0) { t.cancel(); _finish(); }
    });
  }

  void _finish() {
    widget.mediaPipeService.stopTracking();
    widget.onComplete(widget.mediaPipeService.consumeBuffer());
  }

  @override
  void dispose() { _timer?.cancel(); _spinCtrl.dispose(); _colorCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    if (!_started) {
      return Scaffold(
        backgroundColor: AppColors.background,
        body: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const AnimatedCharacter(state: CharacterState.happy, size: 150),
          const SizedBox(height: 20),
          const Text('Watch Together', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 40),
            child: Text('Let your child watch the screen. Do not point or guide.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 15, color: AppColors.textSecondary)),
          ),
          const SizedBox(height: 30),
          ElevatedButton(
            onPressed: _start,
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 16)),
            child: const Text('Start', style: TextStyle(fontSize: 18, color: Colors.white)),
          ),
        ])),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(children: [
        Row(children: [
          // LEFT — social (character face)
          Expanded(child: Container(
            color: const Color(0xFFFFF8F0),
            child: Center(child: AnimatedCharacter(
              state: CharacterState.happy,
              size: MediaQuery.of(context).size.height * 0.55)),
          )),
          Container(width: 3, color: Colors.grey.shade600),
          // RIGHT — non-social (spinning star)
          Expanded(child: Container(
            color: const Color(0xFF0D0D2E),
            child: Center(child: AnimatedBuilder(
              animation: Listenable.merge([_spinAnim, _colorAnim]),
              builder: (_, __) => Transform.rotate(
                angle: _spinAnim.value * 2 * math.pi,
                child: _StarWidget(color: _colorAnim.value ?? Colors.red, size: 200),
              ),
            )),
          )),
        ]),
        // Countdown
        Positioned(top: 16, left: 0, right: 0, child: Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
            decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
            child: Text('$_secondsLeft s', style: const TextStyle(color: Colors.white, fontSize: 20)),
          ),
        )),
        // Gaze indicator dot
        Positioned(bottom: 20, right: 20, child: StreamBuilder<GazeDataPoint>(
          stream: widget.mediaPipeService.gazeStream,
          builder: (_, snap) {
            final x = (snap.data?.gazeRatioHorizontal ?? 0.5).clamp(0.0, 1.0);
            return Container(
              width: 80, height: 14,
              decoration: BoxDecoration(color: Colors.grey.shade800, borderRadius: BorderRadius.circular(7)),
              child: Align(
                alignment: Alignment(x * 2 - 1, 0),
                child: Container(width: 14, height: 14,
                    decoration: const BoxDecoration(color: Colors.greenAccent, shape: BoxShape.circle)),
              ),
            );
          },
        )),
      ]),
    );
  }
}

class _StarWidget extends StatelessWidget {
  final Color color;
  final double size;
  const _StarWidget({required this.color, required this.size});

  @override
  Widget build(BuildContext context) {
    return SizedBox(width: size, height: size,
      child: CustomPaint(painter: _StarPainter(color: color)));
  }
}

class _StarPainter extends CustomPainter {
  final Color color;
  const _StarPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color;
    final cx = size.width / 2; final cy = size.height / 2;
    final path = Path();
    const int spikes = 6;
    const double outer = 85.0; const double inner = 40.0;
    for (int i = 0; i < spikes * 2; i++) {
      final angle = (i * math.pi / spikes) - math.pi / 2;
      final r = i.isEven ? outer : inner;
      final x = cx + r * math.cos(angle);
      final y = cy + r * math.sin(angle);
      i == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
    }
    path.close();
    canvas.drawPath(path, paint);
    // Highlight
    canvas.drawPath(path, Paint()..color = Colors.white.withOpacity(0.15)
      ..style = PaintingStyle.stroke ..strokeWidth = 3);
  }

  @override
  bool shouldRepaint(_StarPainter o) => o.color != color;
}
