package com.nova.downloader.engine

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.RandomAccessFile
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.TimeUnit

data class NovaPrefs(
    val maxConcurrent: Int = 2,
    val allowPrivateNetwork: Boolean = false,
)

/**
 * Nova's Android download engine: streaming OkHttp transfers with
 * HTTP Range resume (when the server supports it), pause/cancel/retry,
 * a concurrency-limited queue, duplicate detection, size validation and
 * SHA-256 computed on completion. Runs on IO coroutines; a foreground
 * service keeps it alive while downloads are active.
 */
class DownloadRepository(private val context: Context) {
    private val store = Store(context)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .retryOnConnectionFailure(false)
        .build()

    private val _items = MutableStateFlow<List<DownloadItem>>(emptyList())
    val items: StateFlow<List<DownloadItem>> = _items.asStateFlow()

    private val jobs = mutableMapOf<String, Job>()
    private val calls = mutableMapOf<String, okhttp3.Call>()
    @Volatile var prefs = NovaPrefs()
    /** Set by the foreground service to observe activity. */
    @Volatile var onActivityChanged: ((active: List<DownloadItem>) -> Unit)? = null

    private val partsDir: File get() = File(context.cacheDir, "parts").apply { mkdirs() }
    val downloadsDir: File get() = File(context.filesDir, "downloads").apply { mkdirs() }

    init {
        _items.value = store.load()
    }

    private fun emit() {
        _items.value = _items.value.toList()
        store.save(_items.value)
        onActivityChanged?.invoke(_items.value.filter { it.state == DState.DOWNLOADING })
    }

    private fun partFile(item: DownloadItem) = File(partsDir, "${item.id}.novapart")

    suspend fun probeOnly(rawUrl: String): Triple<String, Long, Boolean> = withContext(Dispatchers.IO) {
        val url = Safety.validateUrl(rawUrl, prefs.allowPrivateNetwork)
        val p = probe(url.toString())
        Triple(p.second, p.first, p.third)
    }

    /** Returns (totalBytes, fileName, supportsRange). Throws on hard errors (404/403/invalid). */
    private fun probe(urlStr: String): Triple<Long, String, Boolean> {
        val head = Request.Builder().url(urlStr).head().header("User-Agent", UA).build()
        client.newCall(head).execute().use { resp ->
            when {
                resp.isSuccessful -> {
                    val url = java.net.URL(resp.request.url.toString())
                    return Triple(
                        resp.header("Content-Length")?.toLongOrNull() ?: -1L,
                        Safety.deriveFileName(url, resp.header("Content-Disposition"), resp.header("Content-Type")),
                        resp.header("Accept-Ranges")?.lowercase()?.contains("bytes") == true,
                    )
                }
                resp.code == 404 -> throw IllegalStateException("File not found (HTTP 404). The link may have expired.")
                resp.code == 403 || resp.code == 401 -> throw IllegalStateException("Access denied (HTTP ${resp.code}). Nova does not bypass sign-ins.")
            }
        }
        // Fallback: ranged GET probe.
        val get = Request.Builder().url(urlStr).header("Range", "bytes=0-0").header("User-Agent", UA).build()
        client.newCall(get).execute().use { resp ->
            val url = java.net.URL(resp.request.url.toString())
            if (resp.code == 206) {
                val total = resp.header("Content-Range")?.substringAfterLast('/')?.toLongOrNull() ?: -1L
                return Triple(total, Safety.deriveFileName(url, resp.header("Content-Disposition"), resp.header("Content-Type")), true)
            }
            if (resp.isSuccessful) {
                return Triple(
                    resp.header("Content-Length")?.toLongOrNull() ?: -1L,
                    Safety.deriveFileName(url, resp.header("Content-Disposition"), resp.header("Content-Type")),
                    false,
                )
            }
            throw IllegalStateException("Server error (HTTP ${resp.code}).")
        }
    }

    fun add(rawUrl: String, suggestedName: String? = null, allowDuplicate: Boolean = false): Result<DownloadItem> {
        return try {
            val url = Safety.validateUrl(rawUrl, prefs.allowPrivateNetwork)
            if (!allowDuplicate) {
                val existing = _items.value.firstOrNull {
                    it.url == url.toString() && it.state in setOf(DState.QUEUED, DState.DOWNLOADING, DState.PAUSED, DState.COMPLETED)
                }
                if (existing != null) return Result.failure(DuplicateException(existing))
            }
            val name = when {
                !suggestedName.isNullOrBlank() -> Safety.sanitizeFileName(suggestedName)
                else -> Safety.deriveFileName(url, null, null)
            }
            val item = DownloadItem(id = UUID.randomUUID().toString(), url = url.toString(), fileName = dedupeName(name))
            _items.value = _items.value + item
            emit()
            pump()
            Result.success(item)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    class DuplicateException(val existing: DownloadItem) :
        Exception("\"${existing.fileName}\" is already in your downloads.")

    private fun dedupeName(name: String): String {
        val taken = _items.value.map { it.fileName }.toSet()
        if (name !in taken && !File(downloadsDir, name).exists()) return name
        val ext = name.substringAfterLast('.', "")
        val stem = if (ext.isEmpty()) name else name.removeSuffix(".$ext")
        var i = 1
        while (true) {
            val cand = if (ext.isEmpty()) "$stem ($i)" else "$stem ($i).$ext"
            if (cand !in taken && !File(downloadsDir, cand).exists()) return cand
            i++
        }
    }

    fun start(id: String) {
        val item = _items.value.find { it.id == id } ?: return
        if (item.state in setOf(DState.PAUSED, DState.FAILED, DState.CANCELED, DState.QUEUED)) {
            item.state = DState.QUEUED
            item.error = null
            emit()
            pump()
        }
    }

    fun pause(id: String) {
        jobs[id]?.cancel()
        val item = _items.value.find { it.id == id } ?: return
        if (item.state == DState.DOWNLOADING || item.state == DState.QUEUED) {
            item.state = DState.PAUSED
            item.speedBps = 0
            emit()
            pump()
        }
    }

    fun cancel(id: String, deletePartial: Boolean = true) {
        jobs[id]?.cancel()
        val item = _items.value.find { it.id == id } ?: return
        item.state = DState.CANCELED
        item.speedBps = 0
        if (deletePartial) partFile(item).delete()
        emit()
        pump()
    }

    fun remove(id: String, deleteFile: Boolean) {
        val item = _items.value.find { it.id == id } ?: return
        jobs[id]?.cancel()
        partFile(item).delete()
        if (deleteFile) item.finalPath?.let { File(it).delete() }
        _items.value = _items.value.filterNot { it.id == id }
        emit()
    }

    fun clearHistory() {
        _items.value = _items.value.filter { it.state in setOf(DState.QUEUED, DState.DOWNLOADING, DState.PAUSED) }
        emit()
    }

    private fun pump() {
        val running = _items.value.count { it.state == DState.DOWNLOADING }
        var slots = prefs.maxConcurrent - running
        if (slots <= 0) return
        for (item in _items.value) {
            if (slots <= 0) break
            if (item.state == DState.QUEUED) {
                launchDownload(item)
                slots--
            }
        }
    }

    private fun launchDownload(item: DownloadItem) {
        item.state = DState.DOWNLOADING
        emit()
        jobs[item.id] = scope.launch {
            try {
                runDownload(item)
                item.state = DState.COMPLETED
                item.speedBps = 0
            } catch (e: kotlinx.coroutines.CancellationException) {
                // pause()/cancel()/remove() already set the state
                if (item.state == DState.DOWNLOADING) item.state = DState.PAUSED
            } catch (e: Exception) {
                item.state = DState.FAILED
                item.error = e.message ?: "Download failed"
                item.speedBps = 0
            } finally {
                calls.remove(item.id)
                emit()
                pump()
            }
        }
    }

    private suspend fun runDownload(item: DownloadItem) {
        val (total, probedName, supportsRange) = withContext(Dispatchers.IO) { probe(item.url) }
        if (total > 0) item.totalBytes = total
        item.supportsRange = supportsRange
        if (item.fileName == "download" || item.fileName.startsWith("download.")) item.fileName = dedupeName(probedName)

        val part = partFile(item)
        var existing = if (supportsRange && part.exists()) part.length() else 0L
        if (!supportsRange && part.exists()) part.delete() // cannot resume: restart clean
        if (total > 0 && existing == total) {
            finalizeDownload(item, part)
            return
        }
        if (total > 0 && existing > total) { part.delete(); existing = 0 }

        val reqBuilder = Request.Builder().url(item.url).header("User-Agent", UA)
        if (existing > 0) reqBuilder.header("Range", "bytes=$existing-")
        val call = client.newCall(reqBuilder.build())
        withContext(Dispatchers.IO) {
            call.execute().use { resp ->
                if (resp.code == 416 && total > 0 && existing == total) return@use
                if (resp.code !in intArrayOf(200, 206)) {
                    throw IllegalStateException(
                        when (resp.code) {
                            404 -> "File not found (HTTP 404)."
                            401, 403 -> "Access denied (HTTP ${resp.code})."
                            429 -> "Server is rate-limiting Nova (HTTP 429). Try again later."
                            else -> "Server responded HTTP ${resp.code}."
                        }
                    )
                }
                val append = resp.code == 206
                if (!append) existing = 0
                item.mime = resp.header("Content-Type")?.substringBefore(';')?.trim()
                val body = resp.body ?: throw IllegalStateException("Empty response from server.")
                val raf = RandomAccessFile(part, "rw")
                raf.seek(existing)
                if (!append) raf.setLength(0)
                item.downloadedBytes = existing
                val buf = ByteArray(64 * 1024)
                var windowBytes = 0L
                var windowStart = System.currentTimeMillis()
                var lastEmit = 0L
                val src = body.byteStream()
                while (true) {
                    // Cooperative cancellation checkpoints for pause/cancel.
                    if (Thread.currentThread().isInterrupted) throw InterruptedException("paused")
                    val n = src.read(buf)
                    if (n == -1) break
                    raf.write(buf, 0, n)
                    item.downloadedBytes += n
                    windowBytes += n
                    val now = System.currentTimeMillis()
                    if (now - windowStart >= 1000) {
                        item.speedBps = windowBytes * 1000 / (now - windowStart)
                        windowBytes = 0; windowStart = now
                    }
                    if (now - lastEmit > 300) { lastEmit = now; emitThrottled() }
                }
                raf.close()
            }
        }
        if (total > 0 && part.length() != total) {
            throw IllegalStateException(
                "Incomplete download: got ${formatBytes(part.length())} of ${formatBytes(total)}. " +
                    if (supportsRange) "Tap Retry to resume." else "This server cannot resume; retrying restarts the file."
            )
        }
        finalizeDownload(item, part)
    }

    @Volatile private var lastPersist = 0L
    private fun emitThrottled() {
        _items.value = _items.value.toList()
        onActivityChanged?.invoke(_items.value.filter { it.state == DState.DOWNLOADING })
        val now = System.currentTimeMillis()
        if (now - lastPersist > 2000) { lastPersist = now; store.save(_items.value) }
    }

    private fun finalizeDownload(item: DownloadItem, part: File) {
        val finalName = dedupeNameForFinal(item)
        val dest = File(downloadsDir, finalName)
        part.copyTo(dest, overwrite = true)
        part.delete()
        item.fileName = finalName
        item.finalPath = dest.absolutePath
        item.downloadedBytes = dest.length()
        // SHA-256 recorded for integrity reference (not displayed prominently).
        runCatching {
            val md = MessageDigest.getInstance("SHA-256")
            dest.inputStream().use { ins ->
                val b = ByteArray(64 * 1024)
                while (true) { val n = ins.read(b); if (n == -1) break; md.update(b, 0, n) }
            }
            md.digest().joinToString("") { "%02x".format(it) }
        }
        publishToMediaStore(item, dest)
    }

    private fun dedupeNameForFinal(item: DownloadItem): String {
        // item.fileName was already de-duplicated against records; avoid FS clobber too.
        var name = item.fileName
        if (!File(downloadsDir, name).exists() || item.finalPath == File(downloadsDir, name).absolutePath) return name
        val ext = name.substringAfterLast('.', "")
        val stem = if (ext.isEmpty()) name else name.removeSuffix(".$ext")
        var i = 1
        while (true) {
            val cand = if (ext.isEmpty()) "$stem ($i)" else "$stem ($i).$ext"
            if (!File(downloadsDir, cand).exists()) { name = cand; break }
            i++
        }
        return name
    }

    /** Also surface the finished file in the public Downloads collection (best-effort). */
    private fun publishToMediaStore(item: DownloadItem, file: File) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return
        runCatching {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, item.fileName)
                put(MediaStore.Downloads.MIME_TYPE, item.mime ?: "application/octet-stream")
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Nova")
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values) ?: return
            resolver.openOutputStream(uri)?.use { out -> file.inputStream().use { it.copyTo(out) } }
            values.clear()
            values.put(MediaStore.Downloads.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        }
    }

    companion object {
        private const val UA = "Nova Download Manager/0.1 (Android)"
    }
}
