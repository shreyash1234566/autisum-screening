package com.autism.screening

import android.os.Bundle
import androidx.core.view.WindowCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val METHOD_CH = "autism_screening/mediapipe"
    private val EVENT_CH  = "autism_screening/gaze_stream"

    private lateinit var handler: MediaPipeHandler

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Android 16: edge-to-edge is now enforced for apps targeting API 36.
        // setDecorFitsSystemWindows(false) lets Flutter own the full screen area
        // and handle WindowInsets via its built-in padding/MediaQuery logic.
        WindowCompat.setDecorFitsSystemWindows(window, false)
    }

    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)

        handler = MediaPipeHandler(this)

        // Method channel — start / stop tracking
        MethodChannel(engine.dartExecutor.binaryMessenger, METHOD_CH)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "startTracking" -> { handler.start(); result.success(null) }
                    "stopTracking"  -> { handler.stop();  result.success(null) }
                    else -> result.notImplemented()
                }
            }

        // Event channel — stream gaze data to Flutter
        EventChannel(engine.dartExecutor.binaryMessenger, EVENT_CH)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(args: Any?, sink: EventChannel.EventSink) {
                    handler.setSink(sink)
                }
                override fun onCancel(args: Any?) {
                    handler.setSink(null)
                }
            })
    }
}
