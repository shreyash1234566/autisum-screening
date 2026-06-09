import 'package:flutter_tts/flutter_tts.dart';

/// Text-to-speech service for name calling and task instructions.
/// Uses Google TTS — free API.
class TtsService {
  final FlutterTts _tts = FlutterTts();
  bool _isInitialised = false;

  Future<void> init(String languageCode) async {
    await _tts.setLanguage(languageCode == 'hi' ? 'hi-IN' : 'en-IN');
    await _tts.setSpeechRate(0.45); // slower for children
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.1);       // slightly higher, friendlier
    _isInitialised = true;
  }

  /// Calls the child's name — core Task B behaviour.
  /// Parent enters name at registration; we TTS it for each trial.
  Future<void> callName(String childName, {String languageCode = 'en'}) async {
    if (!_isInitialised) await init(languageCode);
    final text = languageCode == 'hi' ? '$childName!' : '$childName!';
    await _tts.speak(text);
  }

  Future<void> speak(String text) async {
    await _tts.speak(text);
  }

  Future<void> stop() async {
    await _tts.stop();
  }

  Future<void> dispose() async {
    await _tts.stop();
  }
}
