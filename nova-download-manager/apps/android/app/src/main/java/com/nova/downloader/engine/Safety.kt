package com.nova.downloader.engine

import java.net.URL
import java.net.URLDecoder

/** Mirrors the desktop core's URL safety + filename rules. */
object Safety {

    fun validateUrl(raw: String, allowPrivate: Boolean): URL {
        val url = try {
            URL(raw.trim())
        } catch (e: Exception) {
            throw IllegalArgumentException("Invalid URL")
        }
        if (url.protocol != "http" && url.protocol != "https") {
            throw IllegalArgumentException("Unsupported protocol \"${url.protocol}\" — only HTTP/HTTPS.")
        }
        if (!allowPrivate) {
            val host = url.host.lowercase()
            if (host == "localhost" || host.endsWith(".local")) {
                throw IllegalArgumentException("Localhost downloads are blocked in Settings.")
            }
            if (isPrivateIp(host)) {
                throw IllegalArgumentException("Private/local network downloads are blocked in Settings.")
            }
        }
        return url
    }

    private fun isPrivateIp(host: String): Boolean {
        if (host == "::1" || host == "[::1]") return true
        val parts = host.split(".").mapNotNull { it.toIntOrNull() }
        if (parts.size != 4) return false
        val (a, b) = parts[0] to parts[1]
        return a == 10 || a == 127 || (a == 172 && b in 16..31) || (a == 192 && b == 168) ||
            (a == 169 && b == 254) || a == 0 || (a == 100 && b in 64..127)
    }

    private val reserved = Regex("^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\\..*)?$", RegexOption.IGNORE_CASE)

    fun sanitizeFileName(name: String?, fallback: String = "download"): String {
        var base = (name ?: "").replace("\\", "/").substringAfterLast("/")
        base = base.replace(Regex("[<>:\"|?*\\p{Cntrl}]"), "_")
        base = base.replace(Regex("\\s+"), " ").trim().trimEnd('.', ' ')
        base = base.replace(Regex("^\\.+"), "_")
        if (base.isEmpty()) base = fallback
        if (reserved.matches(base)) base = "_$base"
        if (base.length > 200) {
            val dot = base.lastIndexOf('.')
            val ext = if (dot > 0 && base.length - dot <= 12) base.substring(dot) else ""
            base = base.take(200 - ext.length) + ext
        }
        return base
    }

    fun fileNameFromContentDisposition(header: String?): String? {
        if (header == null) return null
        val star = Regex("""filename\*\s*=\s*[^']*'[^']*'([^;]+)""", RegexOption.IGNORE_CASE).find(header)
        if (star != null) {
            return runCatching { sanitizeFileName(URLDecoder.decode(star.groupValues[1].trim(), "UTF-8")) }.getOrNull()
        }
        val plain = Regex("""filename\s*=\s*("[^"]*"|[^;]+)""", RegexOption.IGNORE_CASE).find(header) ?: return null
        var v = plain.groupValues[1].trim().trim('"')
        v = runCatching { URLDecoder.decode(v, "UTF-8") }.getOrDefault(v)
        return sanitizeFileName(v)
    }

    private val mimeExt = mapOf(
        "application/pdf" to ".pdf", "application/zip" to ".zip", "image/jpeg" to ".jpg",
        "image/png" to ".png", "video/mp4" to ".mp4", "video/webm" to ".webm",
        "audio/mpeg" to ".mp3", "audio/mp4" to ".m4a", "audio/ogg" to ".ogg",
        "application/vnd.android.package-archive" to ".apk",
    )

    fun deriveFileName(url: URL, contentDisposition: String?, mime: String?): String {
        fileNameFromContentDisposition(contentDisposition)?.let { if (it != "download") return it }
        val seg = runCatching { URLDecoder.decode(url.path.split("/").last { it.isNotEmpty() }, "UTF-8") }
            .getOrDefault("download")
        var name = sanitizeFileName(seg)
        if (!name.contains('.')) {
            mime?.substringBefore(';')?.trim()?.lowercase()?.let { m ->
                mimeExt[m]?.let { ext -> if (!name.lowercase().endsWith(ext)) name += ext }
            }
        }
        return name
    }

    private val execExts = setOf("apk", "exe", "msi", "jar", "deb", "rpm")
    fun isExecutable(fileName: String): Boolean =
        fileName.substringAfterLast('.', "").lowercase() in execExts
}
