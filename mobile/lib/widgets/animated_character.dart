import 'dart:math';
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

/// Animated character widget.
/// Guide: "gender-neutral, large simple eyes, slight smile, non-threatening.
///         calm, simple, warm colors"
/// Built with CustomPainter + AnimationController — no external dependencies.
class AnimatedCharacter extends StatefulWidget {
  final CharacterState state;
  final double size;

  const AnimatedCharacter({
    super.key,
    this.state = CharacterState.idle,
    this.size = 200,
  });

  @override
  State<AnimatedCharacter> createState() => _AnimatedCharacterState();
}

enum CharacterState {
  idle,
  talking,
  waving,
  clapping,
  happy,
}

class _AnimatedCharacterState extends State<AnimatedCharacter>
    with TickerProviderStateMixin {
  late AnimationController _blinkCtrl;
  late AnimationController _bobCtrl;
  late AnimationController _mouthCtrl;
  late AnimationController _waveCtrl;

  late Animation<double> _blinkAnim;
  late Animation<double> _bobAnim;
  late Animation<double> _mouthAnim;
  late Animation<double> _waveAnim;

  @override
  void initState() {
    super.initState();

    // Natural idle blink every ~4 seconds
    _blinkCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 150),
    );
    _blinkAnim = Tween<double>(begin: 1.0, end: 0.05).animate(_blinkCtrl);

    // Gentle vertical bob
    _bobCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _bobAnim = Tween<double>(begin: -4.0, end: 4.0).animate(
      CurvedAnimation(parent: _bobCtrl, curve: Curves.easeInOut),
    );

    // Mouth open/close for talking
    _mouthCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _mouthAnim = Tween<double>(begin: 0.0, end: 1.0).animate(_mouthCtrl);

    // Wave arm animation
    _waveCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _waveAnim = Tween<double>(begin: -0.2, end: 0.5).animate(
      CurvedAnimation(parent: _waveCtrl, curve: Curves.easeInOut),
    );

    _startBlinkTimer();
    _applyState(widget.state);
  }

  void _startBlinkTimer() {
    Future.delayed(const Duration(seconds: 4), () {
      if (!mounted) return;
      _blinkCtrl.forward().then((_) => _blinkCtrl.reverse()).then((_) {
        if (mounted) _startBlinkTimer();
      });
    });
  }

  void _applyState(CharacterState s) {
    switch (s) {
      case CharacterState.talking:
        _mouthCtrl.repeat(reverse: true);
        break;
      case CharacterState.waving:
        _waveCtrl.repeat(reverse: true);
        break;
      case CharacterState.clapping:
        _waveCtrl.repeat(reverse: true);
        break;
      case CharacterState.happy:
        _mouthCtrl.forward();
        break;
      default:
        _mouthCtrl.stop();
        _waveCtrl.stop();
    }
  }

  @override
  void didUpdateWidget(AnimatedCharacter old) {
    super.didUpdateWidget(old);
    if (old.state != widget.state) _applyState(widget.state);
  }

  @override
  void dispose() {
    _blinkCtrl.dispose();
    _bobCtrl.dispose();
    _mouthCtrl.dispose();
    _waveCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_blinkAnim, _bobAnim, _mouthAnim, _waveAnim]),
      builder: (_, __) {
        return Transform.translate(
          offset: Offset(0, _bobAnim.value),
          child: CustomPaint(
            size: Size(widget.size, widget.size * 1.2),
            painter: _CharacterPainter(
              blinkScale: _blinkAnim.value,
              mouthOpen: _mouthAnim.value,
              armAngle: _waveAnim.value,
              state: widget.state,
            ),
          ),
        );
      },
    );
  }
}

class _CharacterPainter extends CustomPainter {
  final double blinkScale;
  final double mouthOpen;
  final double armAngle;
  final CharacterState state;

  _CharacterPainter({
    required this.blinkScale,
    required this.mouthOpen,
    required this.armAngle,
    required this.state,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final headR = size.width * 0.38;
    final headCY = headR + size.height * 0.05;

    // ── Body ────────────────────────────────────────────────────────────────
    final bodyPaint = Paint()..color = AppColors.primary.withOpacity(0.9);
    final bodyRect = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(cx, headCY + headR + size.height * 0.18),
        width: size.width * 0.55,
        height: size.height * 0.30,
      ),
      const Radius.circular(20),
    );
    canvas.drawRRect(bodyRect, bodyPaint);

    // ── Right arm (waving) ─────────────────────────────────────────────────
    if (state == CharacterState.waving || state == CharacterState.clapping) {
      canvas.save();
      canvas.translate(cx + size.width * 0.27, headCY + headR + size.height * 0.10);
      canvas.rotate(armAngle);
      final armPaint = Paint()
        ..color = AppColors.characterSkin
        ..strokeWidth = size.width * 0.06
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke;
      canvas.drawLine(
        Offset.zero,
        Offset(size.width * 0.18, -size.height * 0.16),
        armPaint,
      );
      canvas.restore();
    }

    // Left arm (static)
    final armPaint = Paint()
      ..color = AppColors.characterSkin
      ..strokeWidth = size.width * 0.06
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    canvas.drawLine(
      Offset(cx - size.width * 0.27, headCY + headR + size.height * 0.10),
      Offset(cx - size.width * 0.45, headCY + headR + size.height * 0.22),
      armPaint,
    );

    // ── Face ─────────────────────────────────────────────────────────────
    final facePaint = Paint()..color = AppColors.characterSkin;
    canvas.drawCircle(Offset(cx, headCY), headR, facePaint);

    // Cheek blush
    final blushPaint = Paint()..color = const Color(0xFFFFB3BA).withOpacity(0.4);
    canvas.drawCircle(Offset(cx - headR * 0.5, headCY + headR * 0.25),
        headR * 0.20, blushPaint);
    canvas.drawCircle(Offset(cx + headR * 0.5, headCY + headR * 0.25),
        headR * 0.20, blushPaint);

    // ── Eyes ─────────────────────────────────────────────────────────────
    _drawEye(canvas, Offset(cx - headR * 0.35, headCY - headR * 0.10),
        headR * 0.22, blinkScale);
    _drawEye(canvas, Offset(cx + headR * 0.35, headCY - headR * 0.10),
        headR * 0.22, blinkScale);

    // ── Mouth ─────────────────────────────────────────────────────────────
    _drawMouth(canvas, cx, headCY, headR, mouthOpen, state);
  }

  void _drawEye(Canvas canvas, Offset center, double radius, double blinkScale) {
    // White sclera
    final whitePaint = Paint()..color = Colors.white;
    canvas.drawOval(
      Rect.fromCenter(
          center: center,
          width: radius * 2,
          height: radius * 2 * blinkScale),
      whitePaint,
    );
    // Iris
    if (blinkScale > 0.3) {
      final irisPaint = Paint()..color = AppColors.characterEye;
      canvas.drawCircle(center, radius * 0.65 * blinkScale, irisPaint);
      // Pupil
      final pupilPaint = Paint()..color = const Color(0xFF1A1A2E);
      canvas.drawCircle(center, radius * 0.35 * blinkScale, pupilPaint);
      // Catchlight
      final catchPaint = Paint()..color = Colors.white;
      canvas.drawCircle(
        Offset(center.dx + radius * 0.20, center.dy - radius * 0.20),
        radius * 0.12,
        catchPaint,
      );
    }
  }

  void _drawMouth(Canvas canvas, double cx, double cy, double headR,
      double openAmount, CharacterState state) {
    final mouthPaint = Paint()
      ..color = const Color(0xFFC0392B)
      ..strokeWidth = headR * 0.06
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final mouthY = cy + headR * 0.38;
    final mouthW = headR * 0.50;

    if (state == CharacterState.happy || openAmount > 0.5) {
      // Big happy smile
      final path = Path()
        ..moveTo(cx - mouthW, mouthY)
        ..quadraticBezierTo(cx, mouthY + headR * 0.25, cx + mouthW, mouthY);
      canvas.drawPath(path, mouthPaint);
      // Lip fill
      final fillPaint = Paint()
        ..color = const Color(0xFFC0392B).withOpacity(0.3)
        ..style = PaintingStyle.fill;
      final fillPath = Path()
        ..moveTo(cx - mouthW, mouthY)
        ..quadraticBezierTo(cx, mouthY + headR * 0.25 + headR * 0.15 * openAmount,
            cx + mouthW, mouthY)
        ..close();
      canvas.drawPath(fillPath, fillPaint);
    } else {
      // Gentle closed smile
      final path = Path()
        ..moveTo(cx - mouthW * 0.7, mouthY)
        ..quadraticBezierTo(cx, mouthY + headR * 0.12, cx + mouthW * 0.7, mouthY);
      canvas.drawPath(path, mouthPaint);
    }
  }

  @override
  bool shouldRepaint(_CharacterPainter old) =>
      old.blinkScale != blinkScale ||
      old.mouthOpen != mouthOpen ||
      old.armAngle != armAngle ||
      old.state != state;
}
