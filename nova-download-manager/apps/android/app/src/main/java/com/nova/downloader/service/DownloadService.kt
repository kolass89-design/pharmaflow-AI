package com.nova.downloader.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.nova.downloader.MainActivity
import com.nova.downloader.NovaApp
import com.nova.downloader.engine.DState
import com.nova.downloader.engine.DownloadItem
import com.nova.downloader.engine.formatBytes
import com.nova.downloader.engine.formatSpeed
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Foreground service that keeps downloads alive while the app is in the
 * background, per Android's rules (visible notification, dataSync type).
 * It stops itself as soon as no download is active to save battery.
 */
class DownloadService : Service() {
    private val scope = CoroutineScope(Dispatchers.Main + Job())
    private var lastCompletedCount = 0

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        ensureChannel(this)
        startForegroundCompat(buildNotification(active = emptyList()))
        val repo = (application as NovaApp).repository
        scope.launch {
            repo.items.collectLatest { items ->
                val active = items.filter { it.state == DState.DOWNLOADING }
                val completed = items.count { it.state == DState.COMPLETED }
                if (completed > lastCompletedCount) {
                    lastCompletedCount = completed
                    notifyCompleted(items.lastOrNull { it.state == DState.COMPLETED })
                }
                if (active.isEmpty()) {
                    stopForeground(STOP_FOREGROUND_REMOVE)
                    stopSelf()
                } else {
                    startForegroundCompat(buildNotification(active))
                }
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private fun startForegroundCompat(n: Notification) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIF_ID, n)
        }
    }

    private fun openAppIntent(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        return PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
    }

    private fun buildNotification(active: List<DownloadItem>): Notification {
        val title = when {
            active.isEmpty() -> "Nova is ready"
            active.size == 1 -> active[0].fileName
            else -> "${active.size} downloads in progress"
        }
        val text = if (active.size == 1) {
            val a = active[0]
            "${formatBytes(a.downloadedBytes)}${if (a.totalBytes > 0) " of ${formatBytes(a.totalBytes)}" else ""} · ${formatSpeed(a.speedBps)}"
        } else {
            "Total ${formatSpeed(active.sumOf { it.speedBps })}"
        }
        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentTitle(title)
            .setContentText(text)
            .setContentIntent(openAppIntent())
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setSilent(true)
        if (active.size == 1 && active[0].totalBytes > 0) {
            val a = active[0]
            builder.setProgress(1000, (a.progressFraction * 1000).toInt(), false)
        } else {
            builder.setProgress(0, 0, active.isNotEmpty())
        }
        return builder.build()
    }

    private fun notifyCompleted(item: DownloadItem?) {
        if (item == null) return
        val n = NotificationCompat.Builder(this, CHANNEL_ID_DONE)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle("Download complete")
            .setContentText(item.fileName)
            .setContentIntent(openAppIntent())
            .setAutoCancel(true)
            .build()
        getSystemService(NotificationManager::class.java)?.notify(item.id.hashCode(), n)
    }

    companion object {
        const val CHANNEL_ID = "nova_downloads"
        const val CHANNEL_ID_DONE = "nova_downloads_done"
        const val NOTIF_ID = 4711

        fun ensureChannel(ctx: Context) {
            val nm = ctx.getSystemService(NotificationManager::class.java) ?: return
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL_ID, "Downloads", NotificationManager.IMPORTANCE_LOW).apply {
                    description = "Progress of active downloads"
                }
            )
            nm.createNotificationChannel(
                NotificationChannel(CHANNEL_ID_DONE, "Download finished", NotificationManager.IMPORTANCE_DEFAULT).apply {
                    description = "When a download completes"
                }
            )
        }

        fun start(ctx: Context) {
            val intent = Intent(ctx, DownloadService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(intent)
            else ctx.startService(intent)
        }
    }
}
