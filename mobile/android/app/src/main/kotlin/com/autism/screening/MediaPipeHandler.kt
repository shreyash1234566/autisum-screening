package com.autism.screening

import android.content.Context
import android.os.SystemClock
import android.util.Log
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facelandmarker.FaceLandmarker
import com.google.mediapipe.tasks.vision.facelandmarker.FaceLandmarkerOptions
import io.flutter.plugin.common.EventChannel
import kotlin.math.*

/**
 * MediaPipeHandler — wraps MediaPipe Face Landmarker (478-point mesh + irises).
 * Updated for Android 16 (API 36):
 *   - Replaced deprecated Handler(Looper.getMainLooper()).post with context.mainExecutor.execute
 *   - Uses MediaPipe 0.10.26 which ships 16 KB page-aligned .so files
 *
 * Landmark indices used (from MediaPipe Face Mesh topology):
 *   Left iris  : 468, 469, 470, 471, 472  (center + 4 edge points)
 *   Right iris : 473, 474, 475, 476, 477
 *   Eye corners: L-outer=33, L-inner=133, R-inner=362, R-outer=263
 *   Eyelids    : L-upper=159, L-lower=145, R-upper=386, R-lower=374
 *   Nose tip   : 1  (for head yaw estimation)
 *
 * Source: google-ai-edge/mediapipe, face_landmarker docs
 */
class MediaPipeHandler(private val context: Context) {

    companion object {
        private const val TAG = "MediaPipeHandler"
        private const val MODEL_ASSET = "face_landmarker.task"

        // Iris landmark indices
        private val LEFT_IRIS  = intArrayOf(468, 469, 470, 471, 472)
        private val RIGHT_IRIS = intArrayOf(473, 474, 475, 476, 477)

        // Eye corner indices
        private const val L_EYE_OUTER  = 33
        private const val L_EYE_INNER  = 133
        private const val R_EYE_INNER  = 362
        private const val R_EYE_OUTER  = 263

        // Eyelid indices for Eye Aspect Ratio (Soukupová & Čech 2016)
        private const val L_EYE_UPPER  = 159
        private const val L_EYE_LOWER  = 145
        private const val R_EYE_UPPER  = 386
        private const val R_EYE_LOWER  = 374

        // Nose tip for head yaw
        private const val NOSE_TIP = 1
        // Chin and forehead for pitch
        private const val CHIN     = 152
        private const val FOREHEAD = 10
    }

    private var faceLandmarker: FaceLandmarker? = null
    private var sink: EventChannel.EventSink? = null
    private var isRunning = false

    fun setSink(s: EventChannel.EventSink?) { sink = s }

    fun start() {
        if (isRunning) return
        isRunning = true
        buildLandmarker()
        Log.d(TAG, "MediaPipe face landmarker started (Android 16 compatible)")
    }

    fun stop() {
        isRunning = false
        faceLandmarker?.close()
        faceLandmarker = null
        Log.d(TAG, "MediaPipe stopped")
    }

    private fun buildLandmarker() {
        val baseOptions = BaseOptions.builder()
            .setModelAssetPath(MODEL_ASSET)
            .build()

        val options = FaceLandmarkerOptions.builder()
            .setBaseOptions(baseOptions)
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumFaces(1)
            .setMinFaceDetectionConfidence(0.5f)
            .setMinFacePresenceConfidence(0.5f)
            .setMinTrackingConfidence(0.5f)
            .setOutputFaceBlendshapes(false)  // not needed
            .setResultListener { result, _ ->
                if (!isRunning) return@setResultListener
                val ts = SystemClock.uptimeMillis()
                processFaceResult(result, ts)
            }
            .setErrorListener { err ->
                Log.e(TAG, "MediaPipe error: ${err.message}")
            }
            .build()

        faceLandmarker = FaceLandmarker.createFromOptions(context, options)
    }

    /** Called by CameraHandler on each frame — pass the MPImage here */
    fun processFrame(mpImage: com.google.mediapipe.framework.image.MPImage, timestampMs: Long) {
        if (!isRunning) return
        faceLandmarker?.detectAsync(mpImage, timestampMs)
    }

    private fun processFaceResult(
        result: com.google.mediapipe.tasks.vision.facelandmarker.FaceLandmarkerResult,
        timestampMs: Long
    ) {
        if (result.faceLandmarks().isEmpty()) return
        val lm = result.faceLandmarks()[0]  // first face only

        // ── Iris gaze ratio ─────────────────────────────────────────────────
        val leftIrisX  = LEFT_IRIS.map { lm[it].x() }.average().toFloat()
        val leftIrisY  = LEFT_IRIS.map { lm[it].y() }.average().toFloat()

        val rightIrisX = RIGHT_IRIS.map { lm[it].x() }.average().toFloat()
        val rightIrisY = RIGHT_IRIS.map { lm[it].y() }.average().toFloat()

        val leftEyeWidth  = abs(lm[L_EYE_INNER].x() - lm[L_EYE_OUTER].x())
        val rightEyeWidth = abs(lm[R_EYE_OUTER].x() - lm[R_EYE_INNER].x())

        val leftGazeNorm = if (leftEyeWidth > 0.001f)
            (leftIrisX - lm[L_EYE_OUTER].x()) / leftEyeWidth else 0.5f

        val rightGazeNorm = if (rightEyeWidth > 0.001f)
            (rightIrisX - lm[R_EYE_INNER].x()) / rightEyeWidth else 0.5f

        val gazeH = ((leftGazeNorm + rightGazeNorm) / 2f).coerceIn(0f, 1f)
        val gazeV = ((leftIrisY + rightIrisY) / 2f).coerceIn(0f, 1f)

        // ── Eye Aspect Ratio (blink detection) ──────────────────────────────
        val leftVertical  = dist(lm[L_EYE_UPPER], lm[L_EYE_LOWER])
        val rightVertical = dist(lm[R_EYE_UPPER], lm[R_EYE_LOWER])
        val leftHoriz     = dist(lm[L_EYE_OUTER], lm[L_EYE_INNER])
        val rightHoriz    = dist(lm[R_EYE_OUTER], lm[R_EYE_INNER])
        val ear = if (leftHoriz + rightHoriz > 0.001f)
            (leftVertical + rightVertical) / (leftHoriz + rightHoriz) else 1.0f

        // ── Head yaw (horizontal head rotation) ─────────────────────────────
        val eyeMidX = (lm[L_EYE_OUTER].x() + lm[R_EYE_OUTER].x()) / 2f
        val noseX   = lm[NOSE_TIP].x()
        val yawApprox = (noseX - eyeMidX) * 200f

        val faceVertMid = (lm[FOREHEAD].y() + lm[CHIN].y()) / 2f
        val pitchApprox = (lm[NOSE_TIP].y() - faceVertMid) * 200f

        // ── Send to Flutter ─────────────────────────────────────────────────
        // Android 16 change: replaced deprecated Handler(Looper.getMainLooper()).post
        // with context.mainExecutor.execute — same semantics, no deprecation warning.
        val data: Map<String, Any> = mapOf(
            "timestamp_ms"   to timestampMs,
            "left_iris_x"    to leftIrisX.toDouble(),
            "left_iris_y"    to leftIrisY.toDouble(),
            "right_iris_x"   to rightIrisX.toDouble(),
            "right_iris_y"   to rightIrisY.toDouble(),
            "gaze_h"         to gazeH.toDouble(),
            "gaze_v"         to gazeV.toDouble(),
            "head_yaw"       to yawApprox.toDouble(),
            "head_pitch"     to pitchApprox.toDouble(),
            "blink_ear"      to ear.toDouble()
        )

        context.mainExecutor.execute {
            sink?.success(data)
        }
    }

    private fun dist(
        a: com.google.mediapipe.tasks.components.containers.NormalizedLandmark,
        b: com.google.mediapipe.tasks.components.containers.NormalizedLandmark
    ): Float {
        val dx = a.x() - b.x()
        val dy = a.y() - b.y()
        return sqrt(dx * dx + dy * dy)
    }
}
