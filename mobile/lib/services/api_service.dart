import 'dart:convert';
import 'package:dio/dio.dart';
import '../models/session.dart';

class ApiService {
  static const String _baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 60),
  ));

  Future<Map<String, dynamic>> registerChild(Map<String, dynamic> data) async {
    final resp = await _dio.post('/children', data: data);
    return Map<String, dynamic>.from(resp.data as Map);
  }

  Future<Map<String, dynamic>> uploadSession({
    required SessionData session,
    required String videoPath,
    void Function(int sent, int total)? onProgress,
  }) async {
    final formData = FormData.fromMap({
      'session_json': MultipartFile.fromString(
        jsonEncode(session.toJson()),
        filename: 'session.json',
      ),
      'video': await MultipartFile.fromFile(
        videoPath,
        filename: 'session_video.mp4',
      ),
    });
    final resp = await _dio.post(
      '/sessions/upload',
      data: formData,
      onSendProgress: onProgress,
    );
    return Map<String, dynamic>.from(resp.data as Map);
  }
}
