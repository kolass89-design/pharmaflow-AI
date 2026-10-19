package com.nova.downloader

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.FolderOpen
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.nova.downloader.engine.DState
import com.nova.downloader.engine.DownloadItem
import com.nova.downloader.engine.DownloadRepository
import com.nova.downloader.engine.NovaPrefs
import com.nova.downloader.engine.Safety
import com.nova.downloader.engine.formatBytes
import com.nova.downloader.engine.formatEta
import com.nova.downloader.engine.formatSpeed
import com.nova.downloader.service.DownloadService
import com.nova.downloader.ui.PlayerScreen
import java.io.File

private val NovaViolet = Color(0xFF6D7CFF)
private val NovaCyan = Color(0xFF22C3E6)

class MainActivity : ComponentActivity() {
    private val repo: DownloadRepository get() = (application as NovaApp).repository
    private val _sharedText = mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestNotificationPermissionIfNeeded()
        handleIntent(intent)
        DownloadService.start(this)
        setContent { NovaRoot() }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        if (intent == null) return
        val text: String? = when (intent.action) {
            Intent.ACTION_SEND -> intent.getStringExtra(Intent.EXTRA_TEXT)
            Intent.ACTION_VIEW -> intent.dataString
            else -> null
        }
        val url = text?.split("\\s+".toRegex())?.firstOrNull { it.startsWith("http://") || it.startsWith("https://") }
        if (url != null) _sharedText.value = url
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            registerForActivityResult(ActivityResultContracts.RequestPermission()) {}.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    @Composable
    private fun NovaRoot() {
        val dark = isSystemInDarkTheme()
        MaterialTheme(
            colorScheme = if (dark) darkColorScheme(primary = NovaViolet, secondary = NovaCyan)
            else lightColorScheme(primary = NovaViolet, secondary = NovaCyan),
        ) {
            NovaAppUi(sharedText = _sharedText, repo = repo)
        }
    }
}

private enum class Tab(val label: String) { DOWNLOADS("Downloads"), PLAYER("Player"), SETTINGS("Settings") }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun NovaAppUi(sharedText: androidx.compose.runtime.MutableState<String?>, repo: DownloadRepository) {
    val context = LocalContext.current
    val app = context.applicationContext as NovaApp
    var tab by remember { mutableStateOf(Tab.DOWNLOADS) }
    val items by repo.items.collectAsState()
    var showAdd by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf("") }
    var filter by remember { mutableStateOf("all") }

    // A link arrived via the share sheet -> open the add dialog pre-filled (never auto-download).
    val shared = sharedText.value
    var pendingUrl by remember { mutableStateOf("") }
    if (shared != null) {
        pendingUrl = shared
        sharedText.value = null
        showAdd = true
    }

    fun toast(msg: String) = Toast.makeText(context, msg, Toast.LENGTH_LONG).show()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("⬇️ Nova Download Manager") },
                actions = {
                    IconButton(onClick = { tab = Tab.SETTINGS }) { Icon(Icons.Filled.Settings, "Settings") }
                },
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected = tab == Tab.DOWNLOADS, onClick = { tab = Tab.DOWNLOADS }, icon = { Icon(Icons.Filled.PlayArrow, null) }, label = { Text("Downloads") })
                NavigationBarItem(selected = tab == Tab.PLAYER, onClick = { tab = Tab.PLAYER }, icon = { Icon(Icons.Filled.FolderOpen, null) }, label = { Text("Player") })
                NavigationBarItem(selected = tab == Tab.SETTINGS, onClick = { tab = Tab.SETTINGS }, icon = { Icon(Icons.Filled.Settings, null) }, label = { Text("Settings") })
            }
        },
        floatingActionButton = {
            if (tab == Tab.DOWNLOADS) {
                FloatingActionButton(onClick = { pendingUrl = ""; showAdd = true }) { Icon(Icons.Filled.Add, "Add download") }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (tab) {
                Tab.DOWNLOADS -> DownloadsTab(items, query, { query = it }, filter, { filter = it }, repo)
                Tab.PLAYER -> PlayerScreen(
                    completedMedia = items.filter { it.state == DState.COMPLETED && (it.category == "video" || it.category == "audio") },
                    onBack = { tab = Tab.DOWNLOADS },
                )
                Tab.SETTINGS -> SettingsTab(app, repo)
            }
        }
    }

    if (showAdd) {
        AddDialog(
            initialUrl = pendingUrl,
            onDismiss = { showAdd = false },
            onAdd = { url, name ->
                repo.add(url, name).onFailure { e ->
                    if (e is DownloadRepository.DuplicateException) {
                        toast("Duplicate: ${e.message} It was not added again.")
                    } else toast(e.message ?: "Could not add download")
                }.onSuccess { toast("Downloading ${it.fileName}") }
                showAdd = false
            },
            onAddBatch = { text ->
                var added = 0; var failed = 0
                text.split("\n", ",").map { it.trim() }.filter { it.isNotEmpty() }.forEach { line ->
                    repo.add(line).onSuccess { added++ }.onFailure { failed++ }
                }
                toast("Batch: $added added, $failed skipped")
                showAdd = false
            },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DownloadsTab(
    items: List<DownloadItem>,
    query: String,
    setQuery: (String) -> Unit,
    filter: String,
    setFilter: (String) -> Unit,
    repo: DownloadRepository,
) {
    val filtered = items.filter { item ->
        val matchesFilter = when (filter) {
            "all" -> true
            "active" -> item.state in setOf(DState.DOWNLOADING, DState.QUEUED, DState.PAUSED)
            "done" -> item.state == DState.COMPLETED
            "failed" -> item.state == DState.FAILED || item.state == DState.CANCELED
            else -> item.category == filter
        }
        matchesFilter && (query.isEmpty() || item.fileName.contains(query, true) || item.url.contains(query, true))
    }
    Column(Modifier.fillMaxSize()) {
        OutlinedTextField(
            value = query, onValueChange = setQuery,
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            placeholder = { Text("Search downloads") },
            leadingIcon = { Icon(Icons.Filled.Search, null) },
            singleLine = true,
        )
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            listOf("all" to "All", "active" to "Active", "done" to "Done", "failed" to "Failed", "video" to "Video", "audio" to "Audio").forEach { (key, label) ->
                FilterChip(selected = filter == key, onClick = { setFilter(key) }, label = { Text(label) })
            }
        }
        Spacer(Modifier.height(6.dp))
        if (filtered.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(
                    if (items.isEmpty()) "No downloads yet.\nTap + to add a direct file link,\nor share a link to Nova from any app."
                    else "Nothing matches this filter.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        } else {
            LazyColumn(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(filtered, key = { it.id }) { item -> DownloadCard(item, repo) }
            }
        }
    }
}

@Composable
private fun DownloadCard(item: DownloadItem, repo: DownloadRepository) {
    val context = LocalContext.current
    var menuOpen by remember { mutableStateOf(false) }
    var warnExec by remember { mutableStateOf(false) }

    fun openFile() {
        val path = item.finalPath ?: return
        if (Safety.isExecutable(item.fileName)) { warnExec = true; return }
        openWithSystem(context, File(path), item.mime)
    }

    Card(
        Modifier.fillMaxWidth().padding(horizontal = 12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainer),
    ) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(categoryIcon(item.category), modifier = Modifier.padding(end = 8.dp))
                Column(Modifier.weight(1f)) {
                    Text(item.fileName, maxLines = 1, overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.titleSmall)
                    Text(
                        statusLine(item),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                    )
                }
                when (item.state) {
                    DState.DOWNLOADING -> IconButton(onClick = { repo.pause(item.id) }) { Icon(Icons.Filled.Pause, "Pause") }
                    DState.PAUSED, DState.QUEUED -> IconButton(onClick = { repo.start(item.id) }) { Icon(Icons.Filled.PlayArrow, "Resume") }
                    DState.FAILED -> IconButton(onClick = { repo.start(item.id) }) { Icon(Icons.Filled.Refresh, "Retry") }
                    DState.COMPLETED -> IconButton(onClick = { openFile() }) { Icon(Icons.Filled.FolderOpen, "Open") }
                    DState.CANCELED -> IconButton(onClick = { repo.start(item.id) }) { Icon(Icons.Filled.Refresh, "Restart") }
                }
                Box {
                    IconButton(onClick = { menuOpen = true }) { Icon(Icons.Filled.MoreVert, "More") }
                    DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                        if (item.state in setOf(DState.DOWNLOADING, DState.QUEUED, DState.PAUSED)) {
                            DropdownMenuItem(text = { Text("Cancel download") }, onClick = { menuOpen = false; repo.cancel(item.id) }, leadingIcon = { Icon(Icons.Filled.Close, null) })
                        }
                        if (item.state == DState.COMPLETED) {
                            DropdownMenuItem(text = { Text("Open") }, onClick = { menuOpen = false; openFile() }, leadingIcon = { Icon(Icons.Filled.FolderOpen, null) })
                        }
                        DropdownMenuItem(text = { Text("Remove from list") }, onClick = { menuOpen = false; repo.remove(item.id, false) }, leadingIcon = { Icon(Icons.Filled.Delete, null) })
                        if (item.state == DState.COMPLETED) {
                            DropdownMenuItem(text = { Text("Delete file") }, onClick = { menuOpen = false; repo.remove(item.id, true) }, leadingIcon = { Icon(Icons.Filled.Delete, null) })
                        }
                    }
                }
            }
            if (item.state != DState.COMPLETED) {
                Spacer(Modifier.height(8.dp))
                LinearProgressIndicator(
                    progress = { if (item.totalBytes > 0) item.progressFraction else 0f },
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            item.error?.let {
                Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(top = 6.dp))
                if (!item.supportsRange) {
                    Text("This server doesn't support resume; retrying restarts the file.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }

    if (warnExec) {
        AlertDialog(
            onDismissRequest = { warnExec = false },
            title = { Text("This is a program file") },
            text = { Text("\"${item.fileName}\" can run code on your device. Only open it if you trust the source and expected this file. Nova never opens downloads automatically.") },
            confirmButton = {
                TextButton(onClick = {
                    warnExec = false
                    item.finalPath?.let { openWithSystem(context, File(it), item.mime ?: "application/vnd.android.package-archive") }
                }) { Text("I trust it — open") }
            },
            dismissButton = { TextButton(onClick = { warnExec = false }) { Text("Cancel") } },
        )
    }
}

private fun openWithSystem(context: android.content.Context, file: File, mime: String?) {
    runCatching {
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, mime ?: "*/*")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
    }.onFailure { Toast.makeText(context, "No app can open this file.", Toast.LENGTH_LONG).show() }
}

private fun categoryIcon(category: String): String = when (category) {
    "video" -> "🎬"
    "audio" -> "🎵"
    "documents" -> "📄"
    "archives" -> "🗜️"
    "images" -> "🖼️"
    "applications" -> "💿"
    else -> "📦"
}

private fun statusLine(item: DownloadItem): String {
    val sizes = "${formatBytes(item.downloadedBytes)}${if (item.totalBytes > 0) " of ${formatBytes(item.totalBytes)}" else ""}"
    val pct = if (item.totalBytes > 0) " · %.0f%%".format(item.progressFraction * 100) else ""
    return when (item.state) {
        DState.DOWNLOADING -> "Downloading · $sizes$pct · ${formatSpeed(item.speedBps)} ${formatEta(item)}".trim()
        DState.QUEUED -> "Queued · $sizes"
        DState.PAUSED -> "Paused · $sizes$pct" + if (item.supportsRange) "" else " (server cannot resume)"
        DState.COMPLETED -> "Completed · ${formatBytes(item.totalBytes.coerceAtLeast(item.downloadedBytes))}"
        DState.FAILED -> "Failed · $sizes"
        DState.CANCELED -> "Canceled · $sizes"
    }
}

@Composable
private fun AddDialog(
    initialUrl: String,
    onDismiss: () -> Unit,
    onAdd: (url: String, name: String?) -> Unit,
    onAddBatch: (text: String) -> Unit,
) {
    var url by remember { mutableStateOf(initialUrl) }
    var name by remember { mutableStateOf("") }
    var batchMode by remember { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (batchMode) "Batch download" else "Add download") },
        text = {
            Column {
                if (batchMode) {
                    OutlinedTextField(
                        value = url, onValueChange = { url = it },
                        label = { Text("One URL per line") },
                        modifier = Modifier.fillMaxWidth(), minLines = 4,
                    )
                } else {
                    OutlinedTextField(
                        value = url, onValueChange = { url = it },
                        label = { Text("File URL (HTTP/HTTPS)") },
                        placeholder = { Text("https://example.com/file.mp4") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true,
                    )
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(
                        value = name, onValueChange = { name = it },
                        label = { Text("Save as (optional)") },
                        modifier = Modifier.fillMaxWidth(), singleLine = true,
                    )
                }
                TextButton(onClick = { batchMode = !batchMode }) {
                    Text(if (batchMode) "Single URL instead" else "Add many URLs at once")
                }
                Text(
                    "Nova downloads direct files. Streaming/DRM-protected media is not bypassed.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = url.isNotBlank(),
                onClick = { if (batchMode) onAddBatch(url) else onAdd(url.trim(), name.trim().ifEmpty { null }) },
            ) { Text("Download") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}

@Composable
private fun SettingsTab(app: NovaApp, repo: DownloadRepository) {
    var prefs by remember { mutableStateOf(repo.prefs) }
    fun update(p: NovaPrefs) { prefs = p; app.updatePrefs(p) }
    var confirmClear by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Settings", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        Text("Maximum simultaneous downloads: ${prefs.maxConcurrent}")
        Slider(
            value = prefs.maxConcurrent.toFloat(),
            onValueChange = { update(prefs.copy(maxConcurrent = it.toInt().coerceIn(1, 5))) },
            valueRange = 1f..5f, steps = 3,
        )
        Row(
            Modifier.fillMaxWidth().clickable { update(prefs.copy(allowPrivateNetwork = !prefs.allowPrivateNetwork)) }.padding(vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("Allow private/local network downloads")
                Text(
                    "Off (recommended) blocks localhost/LAN addresses so shared links can't probe your network.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Switch(checked = prefs.allowPrivateNetwork, onCheckedChange = { update(prefs.copy(allowPrivateNetwork = it)) })
        }
        Spacer(Modifier.height(8.dp))
        Text("Storage", style = MaterialTheme.typography.titleMedium)
        Text(
            "Files are saved to Nova's folder and also published to Downloads/Nova in the Files app. Partial (.novapart) files are removed when you cancel a download.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(12.dp))
        TextButton(onClick = { confirmClear = true }) { Text("Clear finished history") }
        Spacer(Modifier.height(20.dp))
        Text("About", style = MaterialTheme.typography.titleMedium)
        Text(
            "Nova Download Manager 0.1.0 (Android). No accounts, no telemetry. Downloads use pause/resume when the server supports it and are size-validated before being marked complete. Downloaded programs are never opened automatically.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text("Clear finished history?") },
            text = { Text("Downloaded files stay on your device; only the list entries are removed.") },
            confirmButton = { TextButton(onClick = { repo.clearHistory(); confirmClear = false }) { Text("Clear") } },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } },
        )
    }
}
