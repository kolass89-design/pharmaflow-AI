package com.nova.downloader.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.nova.downloader.engine.DownloadItem
import java.io.File

private data class Playable(val uri: Uri, val name: String)

@Composable
fun PlayerScreen(completedMedia: List<DownloadItem>, onBack: () -> Unit) {
    val context = LocalContext.current
    val picked = remember { mutableStateListOf<Playable>() }
    var current by remember { mutableStateOf<Playable?>(null) }
    var errorMsg by remember { mutableStateOf<String?>(null) }
    var speed by remember { mutableStateOf(1.0f) }

    val playlist: List<Playable> = completedMedia.mapNotNull { item ->
        item.finalPath?.let { Playable(Uri.fromFile(File(it)), item.fileName) }
    } + picked

    val player = remember {
        ExoPlayer.Builder(context).build().apply {
            addListener(object : Player.Listener {
                override fun onPlayerError(error: PlaybackException) {
                    errorMsg = "This file could not be played (${error.errorCodeName}). " +
                        "Nova's player (Media3/ExoPlayer) supports MP4, WebM, MP3, M4A/AAC, OGG and other Android-supported formats. " +
                        "Some codecs (e.g. certain MKV/AVI/HEVC combinations) vary by device."
                }
            })
        }
    }
    DisposableEffect(player) { onDispose { player.release() } }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        var first: Playable? = null
        uris.forEach { uri ->
            runCatching {
                context.contentResolver.takePersistableUriPermission(uri, android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            val name = uri.lastPathSegment?.substringAfterLast('/') ?: "media"
            val p = Playable(uri, name)
            picked.add(p)
            if (first == null) first = p
        }
        if (current == null) first?.let { current = it }
    }

    fun play(p: Playable) {
        current = p
        errorMsg = null
        player.setMediaItem(MediaItem.fromUri(p.uri))
        player.playbackParameters = androidx.media3.common.PlaybackParameters(speed)
        player.prepare()
        player.playWhenReady = true
    }

    Column(Modifier.fillMaxSize()) {
        Row(Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            IconButton(onClick = onBack) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back") }
            Text("Media player", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 10.dp))
            IconButton(onClick = { picker.launch(arrayOf("video/*", "audio/*")) }) {
                Icon(Icons.Filled.Add, contentDescription = "Add files")
            }
        }

        AndroidView(
            modifier = Modifier.fillMaxWidth().aspectRatio(16f / 9f),
            factory = { ctx -> PlayerView(ctx).apply { this.player = player; useController = true } },
        )

        current?.let {
            Text(
                it.name,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            )
        }

        Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(0.5f, 0.75f, 1f, 1.25f, 1.5f, 2f).forEach { s ->
                OutlinedButton(onClick = {
                    speed = s
                    player.playbackParameters = androidx.media3.common.PlaybackParameters(s)
                }) { Text("${s}×") }
            }
        }

        Spacer(Modifier.height(8.dp))
        Text(
            "Playlist — completed Nova downloads plus files you add",
            style = MaterialTheme.typography.labelLarge,
            modifier = Modifier.padding(horizontal = 16.dp),
        )
        LazyColumn(Modifier.weight(1f)) {
            items(playlist) { p ->
                ListItem(
                    headlineContent = { Text(p.name, maxLines = 1) },
                    supportingContent = { if (p == current) Text("Now playing") },
                    modifier = Modifier.clickable { play(p) },
                )
            }
        }
        if (playlist.isEmpty()) {
            Text(
                "No media yet. Finish a video/audio download, or tap + to play files already on this device.",
                modifier = Modifier.padding(16.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }

    errorMsg?.let { msg ->
        AlertDialog(
            onDismissRequest = { errorMsg = null },
            title = { Text("Playback problem") },
            text = { Text(msg) },
            confirmButton = { TextButton(onClick = { errorMsg = null }) { Text("OK") } },
        )
    }
}
