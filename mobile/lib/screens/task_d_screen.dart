import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/task_config.dart';
import '../models/session.dart';

/// TASK D — Bubble Popping Game
/// Bubbles appear at random screen positions — child touches them.
/// Measures attention, motor coordination, intentional touch.
class TaskDScreen extends StatefulWidget {
  final void Function(List<BubbleTouchEvent> events) onComplete;
  const TaskDScreen({super.key, required this.onComplete});

  @override
  State<TaskDScreen> createState() => _TaskDScreenState();
}

class _Bubble {
  final String id;
  Offset position; // normalised 0-1
  double radius;
  Color color;
  bool popped;
  double scale;

  _Bubble({required this.id, required this.position,
    required this.radius, required this.color})
      : popped = false, scale = 0.0;
}

class _TaskDScreenState extends State<TaskDScreen> with TickerProviderStateMixin {
  final List<_Bubble> _bubbles = [];
  final List<BubbleTouchEvent> _touchEvents = [];
  final _rng = math.Random();
  int _secondsLeft = TaskConfig.taskDDurationSeconds;
  int _popped = 0;
  Timer? _timer;
  Timer? _spawnTimer;

  @override
  void initState() {
    super.initState();
    _spawnBubble();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() => _secondsLeft--);
      if (_secondsLeft <= 0) _finish();
    });
    // Spawn new bubble every 3 seconds
    _spawnTimer = Timer.periodic(const Duration(milliseconds: 3000), (_) {
      if (_bubbles.where((b) => !b.popped).length < 4) _spawnBubble();
    });
  }

  void _spawnBubble() {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    final color = AppColors.bubbleColors[_rng.nextInt(AppColors.bubbleColors.length)];
    setState(() {
      _bubbles.add(_Bubble(
        id: id,
        position: Offset(0.1 + _rng.nextDouble() * 0.8, 0.15 + _rng.nextDouble() * 0.65),
        radius: 35 + _rng.nextDouble() * 20,
        color: color,
      ));
    });
    // Animate in
    Future.delayed(const Duration(milliseconds: 50), () {
      if (!mounted) return;
      setState(() {
        final b = _bubbles.firstWhere((b) => b.id == id, orElse: () => _bubbles.first);
        b.scale = 1.0;
      });
    });
  }

  void _onTap(TapDownDetails details, Size size) {
    final tapNorm = Offset(
      details.localPosition.dx / size.width,
      details.localPosition.dy / size.height,
    );
    bool hit = false;
    for (final b in _bubbles.where((b) => !b.popped)) {
      final dist = (b.position - tapNorm).distance * size.width;
      if (dist < b.radius) {
        hit = true;
        setState(() { b.popped = true; b.scale = 0.0; });
        _popped++;
      }
    }
    _touchEvents.add(BubbleTouchEvent(
      timestampMs: DateTime.now().millisecondsSinceEpoch,
      screenX: tapNorm.dx, screenY: tapNorm.dy, hitBubble: hit,
    ));
  }

  void _finish() {
    _timer?.cancel();
    _spawnTimer?.cancel();
    widget.onComplete(_touchEvents);
  }

  @override
  void dispose() { _timer?.cancel(); _spawnTimer?.cancel(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A2E),
      body: Stack(children: [
        // Header
        Positioned(top: 40, left: 0, right: 0, child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.bubble_chart, color: Colors.white, size: 28),
            const SizedBox(width: 8),
            Text('Popped: $_popped   •   $_secondsLeft s',
                style: const TextStyle(color: Colors.white, fontSize: 18)),
          ],
        )),
        // Tap area
        GestureDetector(
          onTapDown: (d) => _onTap(d, size),
          child: Container(color: Colors.transparent, width: size.width, height: size.height),
        ),
        // Bubbles
        ..._bubbles.where((b) => !b.popped).map((b) => Positioned(
          left: b.position.dx * size.width - b.radius,
          top: b.position.dy * size.height - b.radius,
          child: AnimatedScale(
            scale: b.scale,
            duration: const Duration(milliseconds: 300),
            curve: Curves.elasticOut,
            child: _BubbleWidget(radius: b.radius, color: b.color),
          ),
        )),
      ]),
    );
  }
}

class _BubbleWidget extends StatelessWidget {
  final double radius;
  final Color color;
  const _BubbleWidget({required this.radius, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: radius * 2, height: radius * 2,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: [
          color.withOpacity(0.9),
          color.withOpacity(0.4),
        ], stops: const [0.4, 1.0]),
        border: Border.all(color: Colors.white.withOpacity(0.5), width: 2),
        boxShadow: [BoxShadow(color: color.withOpacity(0.4), blurRadius: 12, spreadRadius: 2)],
      ),
    );
  }
}
