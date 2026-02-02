package com.pupil_labs.gps_alpha_lab

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import java.io.File

class GpsRemoteReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        Log.d("GpsRemoteReceiver", "Received action: $action")

        when (action) {
            "com.pupil_labs.gps_alpha_lab.START_GPS" -> {
                Log.d("GpsRemoteReceiver", "Triggering GPS recording toggle via StateManager")
                RecordingStateManager.triggerToggle()
            }

            "com.pupil_labs.gps_alpha_lab.STOP_GPS" -> {
                Log.d("GpsRemoteReceiver", "Triggering GPS recording toggle via StateManager")
                RecordingStateManager.triggerToggle()
            }

            "com.pupil_labs.gps_alpha_lab.SEND_EVENT" -> {
                Log.d("GpsRemoteReceiver", "GPS EVENT marker received")

                val timestamp = System.currentTimeMillis()
                val fileName = "gps_marker_events.txt"
                val markerText = "MARKER,$timestamp\n"

                try {
                    val file = File(context.getExternalFilesDir(null), fileName)
                    file.appendText(markerText)
                    Log.d("GpsRemoteReceiver", "Marker saved: $markerText")
                } catch (e: Exception) {
                    Log.e("GpsRemoteReceiver", "Error writing marker", e)
                }
            }

            else -> {
                Log.w("GpsRemoteReceiver", "Unknown action: $action")
            }
        }
    }
}
