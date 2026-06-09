import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/app_strings.dart';
import '../models/child.dart';
import '../models/questionnaire.dart';

/// Questionnaire screen — adapts based on child age:
///   16–30 months → M-CHAT-R  (binary yes/no)
///   > 30 months  → AIIMS INDT-ASD (5-point Likert scale)
class QuestionnaireScreen extends StatefulWidget {
  final Child child;
  final AppStrings strings;
  final void Function(Map<String, dynamic> result) onComplete;

  const QuestionnaireScreen({
    super.key,
    required this.child,
    required this.strings,
    required this.onComplete,
  });

  @override
  State<QuestionnaireScreen> createState() => _QuestionnaireScreenState();
}

class _QuestionnaireScreenState extends State<QuestionnaireScreen> {
  // M-CHAT-R answers: questionId → true/false
  final Map<int, bool> _mchatAnswers = {};
  // INDT-ASD answers: questionId → 0-4
  final Map<int, int> _indtAnswers = {};

  int _currentIndex = 0;
  late bool _isMchat;

  @override
  void initState() {
    super.initState();
    _isMchat = widget.child.useMchatR;
  }

  int get _total => _isMchat ? mchatRQuestions.length : indtAsdQuestions.length;
  bool get _currentAnswered {
    if (_isMchat) {
      return _mchatAnswers.containsKey(mchatRQuestions[_currentIndex].id);
    } else {
      return _indtAnswers.containsKey(indtAsdQuestions[_currentIndex].id);
    }
  }

  void _next() {
    if (!_currentAnswered) return;
    if (_currentIndex < _total - 1) {
      setState(() => _currentIndex++);
    } else {
      _submit();
    }
  }

  void _submit() {
    if (_isMchat) {
      final result = QuestionnaireScorer.scoreMchatR(_mchatAnswers);
      widget.onComplete({
        'type': 'mchat_r',
        'answers': Map<String, dynamic>.fromEntries(
            _mchatAnswers.entries.map((e) => MapEntry(e.key.toString(), e.value))),
        ...result,
      });
    } else {
      final result = QuestionnaireScorer.scoreIndtAsd(_indtAnswers);
      widget.onComplete({
        'type': 'indt_asd',
        'answers': Map<String, dynamic>.fromEntries(
            _indtAnswers.entries.map((e) => MapEntry(e.key.toString(), e.value))),
        ...result,
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isHindi = widget.child.language == 'hi';
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        title: Text(widget.strings.questionnaireTitle,
            style: const TextStyle(color: Colors.white)),
        elevation: 0,
      ),
      body: Column(
        children: [
          // Progress bar
          LinearProgressIndicator(
            value: (_currentIndex + 1) / _total,
            backgroundColor: AppColors.divider,
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
            minHeight: 6,
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('${_currentIndex + 1} / $_total',
                  style: const TextStyle(color: AppColors.textSecondary)),
              Text(_isMchat ? 'M-CHAT-R' : 'INDT-ASD',
                  style: const TextStyle(color: AppColors.textSecondary,
                      fontWeight: FontWeight.w600)),
            ]),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: _isMchat
                  ? _MchatQuestion(
                      item: mchatRQuestions[_currentIndex],
                      isHindi: isHindi,
                      answer: _mchatAnswers[mchatRQuestions[_currentIndex].id],
                      onAnswer: (v) => setState(
                          () => _mchatAnswers[mchatRQuestions[_currentIndex].id] = v),
                    )
                  : _IndtQuestion(
                      item: indtAsdQuestions[_currentIndex],
                      isHindi: isHindi,
                      answer: _indtAnswers[indtAsdQuestions[_currentIndex].id],
                      onAnswer: (v) => setState(
                          () => _indtAnswers[indtAsdQuestions[_currentIndex].id] = v),
                    ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Row(children: [
              if (_currentIndex > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => setState(() => _currentIndex--),
                    child: Text(widget.strings.back),
                  ),
                ),
              if (_currentIndex > 0) const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton(
                  onPressed: _currentAnswered ? _next : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    disabledBackgroundColor: AppColors.divider,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: Text(
                    _currentIndex == _total - 1
                        ? widget.strings.submit
                        : widget.strings.next,
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

// ── M-CHAT-R binary widget ───────────────────────────────────────────────────
class _MchatQuestion extends StatelessWidget {
  final QuestionItem item;
  final bool isHindi;
  final bool? answer;
  final void Function(bool) onAnswer;

  const _MchatQuestion({
    required this.item, required this.isHindi,
    required this.answer, required this.onAnswer,
  });

  @override
  Widget build(BuildContext context) {
    final question = isHindi ? item.questionHi : item.questionEn;
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (item.isCritical)
          Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.accent.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('Key question', style: TextStyle(
                color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        Text(question, style: const TextStyle(fontSize: 18, height: 1.5,
            color: AppColors.textPrimary)),
        const SizedBox(height: 32),
        Row(children: [
          Expanded(child: _AnswerButton(
            label: isHindi ? 'हाँ' : 'Yes',
            selected: answer == true,
            color: AppColors.riskLow,
            onTap: () => onAnswer(true),
          )),
          const SizedBox(width: 16),
          Expanded(child: _AnswerButton(
            label: isHindi ? 'नहीं' : 'No',
            selected: answer == false,
            color: AppColors.riskHigh,
            onTap: () => onAnswer(false),
          )),
        ]),
      ],
    );
  }
}

// ── INDT-ASD Likert widget ───────────────────────────────────────────────────
class _IndtQuestion extends StatelessWidget {
  final LikertItem item;
  final bool isHindi;
  final int? answer;
  final void Function(int) onAnswer;

  const _IndtQuestion({
    required this.item, required this.isHindi,
    required this.answer, required this.onAnswer,
  });

  static const labels = ['Never', 'Rarely', 'Sometimes', 'Often', 'Always'];
  static const labelsHi = ['कभी नहीं', 'कभी-कभी', 'कभी-कभी', 'अक्सर', 'हमेशा'];

  @override
  Widget build(BuildContext context) {
    final question = isHindi ? item.questionHi : item.questionEn;
    final lLabels = isHindi ? labelsHi : labels;
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(item.domain.toUpperCase(),
              style: const TextStyle(color: AppColors.primary,
                  fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
        ),
        Text(question, style: const TextStyle(fontSize: 17, height: 1.5,
            color: AppColors.textPrimary)),
        const SizedBox(height: 28),
        ...List.generate(5, (i) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _AnswerButton(
            label: '${i} — ${lLabels[i]}',
            selected: answer == i,
            color: Color.lerp(AppColors.riskLow, AppColors.riskHigh, i / 4)!,
            onTap: () => onAnswer(i),
          ),
        )),
      ],
    );
  }
}

class _AnswerButton extends StatelessWidget {
  final String label;
  final bool selected;
  final Color color;
  final VoidCallback onTap;

  const _AnswerButton({
    required this.label, required this.selected,
    required this.color, required this.onTap,
  });

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: onTap,
    child: AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      decoration: BoxDecoration(
        color: selected ? color : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: selected ? color : AppColors.divider, width: 2),
        boxShadow: selected ? [BoxShadow(color: color.withOpacity(0.3),
            blurRadius: 8, offset: const Offset(0, 3))] : [],
      ),
      child: Text(label, textAlign: TextAlign.center,
          style: TextStyle(color: selected ? Colors.white : AppColors.textPrimary,
              fontSize: 15, fontWeight: FontWeight.w600)),
    ),
  );
}
