import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/app_strings.dart';

class ConsentScreen extends StatefulWidget {
  final AppStrings strings;
  final VoidCallback onAccepted;
  const ConsentScreen({super.key, required this.strings, required this.onAccepted});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  bool _scrolledToEnd = false;
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(() {
      if (_scrollCtrl.offset >= _scrollCtrl.position.maxScrollExtent - 50) {
        setState(() => _scrolledToEnd = true);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        title: Text(widget.strings.consentTitle,
            style: const TextStyle(color: Colors.white)),
      ),
      body: Column(children: [
        Expanded(child: SingleChildScrollView(
          controller: _scrollCtrl,
          padding: const EdgeInsets.all(24),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Icon(Icons.shield_outlined, size: 48, color: AppColors.primary),
            const SizedBox(height: 16),
            Text(widget.strings.consentTitle,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Text(widget.strings.consentBody,
                style: const TextStyle(fontSize: 15, height: 1.7,
                    color: AppColors.textPrimary)),
            const SizedBox(height: 24),
            _ConsentPoint(icon: Icons.videocam_outlined,
                text: 'Video of your child\'s face is recorded during tasks'),
            _ConsentPoint(icon: Icons.lock_outline,
                text: 'All data is encrypted before leaving your device'),
            _ConsentPoint(icon: Icons.local_hospital_outlined,
                text: 'Only your registered doctor can review the results'),
            _ConsentPoint(icon: Icons.info_outline,
                text: 'This is a screening tool — NOT a diagnosis'),
            _ConsentPoint(icon: Icons.stop_circle_outlined,
                text: 'You can stop the session at any time'),
            const SizedBox(height: 30),
            if (!_scrolledToEnd)
              const Center(child: Text('↓ Please scroll to read fully',
                  style: TextStyle(color: AppColors.textSecondary))),
          ]),
        )),
        Padding(
          padding: const EdgeInsets.all(20),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _scrolledToEnd ? widget.onAccepted : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                disabledBackgroundColor: AppColors.divider,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(widget.strings.consentAccept,
                  style: const TextStyle(fontSize: 16, color: Colors.white,
                      fontWeight: FontWeight.w600)),
            ),
          ),
        ),
      ]),
    );
  }
}

class _ConsentPoint extends StatelessWidget {
  final IconData icon;
  final String text;
  const _ConsentPoint({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(icon, color: AppColors.primary, size: 22),
      const SizedBox(width: 12),
      Expanded(child: Text(text, style: const TextStyle(fontSize: 14, height: 1.5))),
    ]),
  );
}
