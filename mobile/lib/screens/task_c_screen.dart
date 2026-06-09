import 'dart:async';
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/task_config.dart';
import '../models/session.dart';
import '../services/mediapipe_service.dart';
import '../services/tts_service.dart';
import '../widgets/animated_character.dart';

/// TASK C — Imitation Test
/// Character waves → waits 5s → character claps → waits 5s
/// Camera records whether child copies the movement
class TaskCScreen extends StatefulWidget {
  final String languageCode;
  final MediaPipeService mediaPipeService;
  final TtsService ttsService;
  final void Function(List<GazeDataPoint> gazeData) onComplete;

  const TaskCScreen({
    super.key,
    required this.languageCode,
    required this.mediaPipeService,
    required this.ttsService,
    required this.onComplete,
  });

  @override
  State<TaskCScreen> createState() => _TaskCScreenState();
}

class _TaskCScreenState extends State<TaskCScreen> {
  _ImitPhase _phase = _ImitPhase.intro;
  CharacterState _charState = CharacterState.idle;
  String _instruction = 'Watch what the character does!';

  @override
  void initState() {
    super.initState();
    widget.mediaPipeService.startTracking();
    _runSequence();
  }

  Future<void> _runSequence() async {
    // Intro pause
    await Future.delayed(const Duration(seconds: 2));
    if (!mounted) return;

    // WAVE
    setState(() { _phase = _ImitPhase.wave; _charState = CharacterState.waving;
      _instruction = widget.languageCode == 'hi' ? 'हाथ हिलाओ!' : 'Wave your hand!'; });
    await widget.ttsService.speak(
        widget.languageCode == 'hi' ? 'हाथ हिलाओ' : 'Wave your hand');
    await Future.delayed(Duration(seconds: TaskConfig.taskCWaitAfterActionSeconds));
    if (!mounted) return;

    // Transition
    setState(() { _charState = CharacterState.idle; _instruction = 'Watch...'; });
    await Future.delayed(const Duration(seconds: 2));
    if (!mounted) return;

    // CLAP
    setState(() { _phase = _ImitPhase.clap; _charState = CharacterState.clapping;
      _instruction = widget.languageCode == 'hi' ? 'ताली बजाओ!' : 'Clap your hands!'; });
    await widget.ttsService.speak(
        widget.languageCode == 'hi' ? 'ताली बजाओ' : 'Clap your hands');
    await Future.delayed(Duration(seconds: TaskConfig.taskCWaitAfterActionSeconds));
    if (!mounted) return;

    // Done
    _finish();
  }

  void _finish() {
    widget.mediaPipeService.stopTracking();
    final data = widget.mediaPipeService.consumeBuffer();
    widget.onComplete(data);
  }

  @override
  void dispose() {
    widget.mediaPipeService.stopTracking();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('Copy Me!',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 30),
          AnimatedCharacter(state: _charState, size: 200),
          const SizedBox(height: 30),
          Text(_instruction,
              style: const TextStyle(fontSize: 20, color: AppColors.primary,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 16),
          // Phase indicator
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            _PhaseChip(label: 'Wave', done: _phase.index > 0),
            const SizedBox(width: 12),
            _PhaseChip(label: 'Clap', done: _phase.index > 1),
          ]),
        ],
      ),
    );
  }
}

enum _ImitPhase { intro, wave, clap }

class _PhaseChip extends StatelessWidget {
  final String label;
  final bool done;
  const _PhaseChip({required this.label, required this.done});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
    decoration: BoxDecoration(
      color: done ? AppColors.riskLow : AppColors.divider,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Text(label, style: TextStyle(
        color: done ? Colors.white : AppColors.textSecondary,
        fontWeight: FontWeight.w600)),
  );
}
