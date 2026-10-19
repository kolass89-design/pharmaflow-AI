/**
 * Saving files on every platform.
 *
 * In a browser (including the installed PWA) a blob download is used. Inside
 * the Tauri shell on Windows and Android the native Save As dialog is used,
 * so users choose the destination instead of relying on webview downloads.
 */

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
    __TAURI__?: unknown;
  }
}

export type SaveResult = "saved" | "cancelled";

export function isDesktopShell(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(window.__TAURI_INTERNALS__ || window.__TAURI__);
}

function browserDownload(blob: Blob, filename: string): SaveResult {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
  return "saved";
}

export async function saveBlob(blob: Blob, filename: string): Promise<SaveResult> {
  if (isDesktopShell()) {
    try {
      const [{ save }, { writeFile }] = await Promise.all([
        import("@tauri-apps/plugin-dialog"),
        import("@tauri-apps/plugin-fs"),
      ]);
      const extension = filename.split(".").pop()?.toLowerCase() ?? "";
      const filters = extension
        ? [{ name: extension.toUpperCase(), extensions: [extension] }]
        : undefined;
      const target = await save({ defaultPath: filename, filters });
      if (!target) return "cancelled";
      await writeFile(target, new Uint8Array(await blob.arrayBuffer()));
      return "saved";
    } catch {
      // Fall back to the browser flow if a plugin permission is unavailable.
    }
  }
  return browserDownload(blob, filename);
}
