package com.nova.downloader

import android.app.Application
import com.nova.downloader.engine.DownloadRepository
import com.nova.downloader.engine.NovaPrefs
import com.nova.downloader.service.DownloadService

class NovaApp : Application() {
    lateinit var repository: DownloadRepository
        private set

    override fun onCreate() {
        super.onCreate()
        DownloadService.ensureChannel(this)
        val prefs = getSharedPreferences("nova", MODE_PRIVATE)
        repository = DownloadRepository(this).apply {
            this.prefs = NovaPrefs(
                maxConcurrent = prefs.getInt("maxConcurrent", 2),
                allowPrivateNetwork = prefs.getBoolean("allowPrivateNetwork", false),
            )
        }
    }

    fun updatePrefs(p: NovaPrefs) {
        repository.prefs = p
        getSharedPreferences("nova", MODE_PRIVATE).edit()
            .putInt("maxConcurrent", p.maxConcurrent)
            .putBoolean("allowPrivateNetwork", p.allowPrivateNetwork)
            .apply()
    }
}
