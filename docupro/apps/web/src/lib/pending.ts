/** In-memory hand-off of picked files from the home screen to a tool page. */

let pendingFiles: File[] | null = null;

export function setPendingFiles(files: File[]): void {
  pendingFiles = files.length ? files : null;
}

export function takePendingFiles(): File[] | null {
  const files = pendingFiles;
  pendingFiles = null;
  return files;
}

export function peekPendingFiles(): File[] | null {
  return pendingFiles;
}
