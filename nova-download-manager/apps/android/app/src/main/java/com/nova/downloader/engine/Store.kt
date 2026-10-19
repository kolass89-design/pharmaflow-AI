package com.nova.downloader.engine

import android.content.Context
import org.json.JSONArray
import java.io.File

/** Atomic JSON persistence for download history (no Room — keeps the APK lean). */
class Store(context: Context) {
    private val file = File(context.filesDir, "downloads.json")
    private val tmp = File(context.cacheDir, "downloads.json.tmp")

    @Synchronized
    fun load(): List<DownloadItem> {
        return try {
            if (!file.exists()) return emptyList()
            val arr = JSONArray(file.readText())
            (0 until arr.length()).map { i ->
                DownloadItem.fromJson(arr.getJSONObject(i)).apply {
                    if (state == DState.DOWNLOADING) state = DState.PAUSED // crash recovery
                    speedBps = 0
                }
            }
        } catch (e: Exception) {
            emptyList()
        }
    }

    @Synchronized
    fun save(items: List<DownloadItem>) {
        try {
            val arr = JSONArray()
            items.forEach { arr.put(it.toJson()) }
            tmp.writeText(arr.toString())
            tmp.copyTo(file, overwrite = true)
            tmp.delete()
        } catch (e: Exception) {
            // Persistence is best-effort; downloads themselves are unaffected.
        }
    }
}
