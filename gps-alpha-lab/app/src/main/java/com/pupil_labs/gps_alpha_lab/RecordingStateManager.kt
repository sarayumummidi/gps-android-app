package com.pupil_labs.gps_alpha_lab

import android.util.Log

/**
 * Singleton to manage recording state and allow remote triggers to
 * communicate with the ViewModel.
 */
object RecordingStateManager {
    private var onToggleRecordingCallback: (() -> Unit)? = null

    /**
     * Register a callback that will be invoked when remote toggle is requested.
     * This should be called by the ViewModel during initialization.
     */
    fun registerToggleCallback(callback: () -> Unit) {
        onToggleRecordingCallback = callback
        Log.d("RecordingStateManager", "Toggle callback registered")
    }

    /**
     * Unregister the callback (call when ViewModel is destroyed).
     */
    fun unregisterToggleCallback() {
        onToggleRecordingCallback = null
        Log.d("RecordingStateManager", "Toggle callback unregistered")
    }

    /**
     * Called by GpsRemoteReceiver to trigger recording toggle.
     * This will invoke the ViewModel's startStopGpsRecording through the callback.
     */
    fun triggerToggle() {
        Log.d("RecordingStateManager", "Toggle triggered from remote")
        onToggleRecordingCallback?.invoke()
            ?: Log.w("RecordingStateManager", "No callback registered - is the app running?")
    }
}
