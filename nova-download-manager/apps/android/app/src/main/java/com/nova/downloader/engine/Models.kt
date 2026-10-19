package com.nova.downloader.engine

import org.json.JSONObject

enum class DState { QUEUED, DOWNLOADING, PAUSED, COMPLETED, FAILED, CANCELED }

data class DownloadItem(
    val id: String,
    val url: String,
    var fileName: String,
    var totalBytes: Long = -1L,
    var downloadedBytes: Long = 0L,
    var state: DState = DState.QUEUED,
    var supportsRange: Boolean = false,
    var mime: String? = null,
    var finalPath: String? = null,
    var error: String? = null,
    var speedBps: Long = 0L,
    val createdAt: Long = System.currentTimeMillis(),
) {
    val category: String get() = categorize(fileName, mime)
    val progressFraction: Float
        get() = if (totalBytes > 0) (downloadedBytes.toFloat() / totalBytes).coerceIn(0f, 1f) else 0f

    fun toJson(): JSONObject = JSONObject().apply {
        put("id", id); put("url", url); put("fileName", fileName)
        put("totalBytes", totalBytes); put("downloadedBytes", downloadedBytes)
        put("state", state.name); put("supportsRange", supportsRange)
        put("mime", mime ?: JSONObject.NULL); put("finalPath", finalPath ?: JSONObject.NULL)
        put("error", error ?: JSONObject.NULL); put("createdAt", createdAt)
    }

    companion object {
        fun fromJson(o: JSONObject): DownloadItem = DownloadItem(
            id = o.getString("id"),
            url = o.getString("url"),
            fileName = o.getString("fileName"),
            totalBytes = o.optLong("totalBytes", -1L),
            downloadedBytes = o.optLong("downloadedBytes", 0L),
            state = runCatching { DState.valueOf(o.optString("state", "QUEUED")) }.getOrDefault(DState.QUEUED),
            supportsRange = o.optBoolean("supportsRange", false),
            mime = o.optString("mime").takeIf { it.isNotEmpty() && it != "null" },
            finalPath = o.optString("finalPath").takeIf { it.isNotEmpty() && it != "null" },
            error = o.optString("error").takeIf { it.isNotEmpty() && it != "null" },
            createdAt = o.optLong("createdAt", System.currentTimeMillis()),
        )
    }
}

private val VIDEO = setOf("mp4", "mkv", "webm", "mov", "avi", "m4v")
private val AUDIO = setOf("mp3", "m4a", "aac", "ogg", "opus", "wav", "flac")
private val DOCS = setOf("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "epub", "csv")
private val ARCH = setOf("zip", "7z", "rar", "tar", "gz", "bz2", "xz", "iso")
private val IMGS = setOf("jpg", "jpeg", "png", "gif", "webp", "bmp", "svg")
private val APPS = setOf("apk", "exe", "msi", "deb", "rpm", "jar")

fun categorize(fileName: String, mime: String?): String {
    val ext = fileName.substringAfterLast('.', "").lowercase()
    return when {
        ext in VIDEO -> "video"
        ext in AUDIO -> "audio"
        ext in DOCS -> "documents"
        ext in ARCH -> "archives"
        ext in IMGS -> "images"
        ext in APPS -> "applications"
        mime?.startsWith("video/") == true -> "video"
        mime?.startsWith("audio/") == true -> "audio"
        mime?.startsWith("image/") == true -> "images"
        mime == "application/pdf" -> "documents"
        else -> "other"
    }
}

fun formatBytes(n: Long): String {
    if (n < 0) return "Unknown size"
    if (n < 1024) return "$n B"
    val units = listOf("KB", "MB", "GB", "TB")
    var v = n / 1024.0
    var i = 0
    while (v >= 1024 && i < units.lastIndex) { v /= 1024; i++ }
    return if (v >= 100) "%.0f %s".format(v, units[i]) else "%.1f %s".format(v, units[i])
}

fun formatSpeed(bps: Long): String = "${formatBytes(bps)}/s"

fun formatEta(item: DownloadItem): String {
    if (item.totalBytes <= 0 || item.speedBps <= 0) return ""
    val s = (item.totalBytes - item.downloadedBytes) / item.speedBps
    return when {
        s < 60 -> "${s}s left"
        s < 3600 -> "${s / 60}m ${s % 60}s left"
        else -> "${s / 3600}h ${(s % 3600) / 60}m left"
    }
}
