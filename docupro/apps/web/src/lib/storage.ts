/** Safe localStorage access (private mode and quota errors never break the UI). */

const PREFIX = "docupro.";

export function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeJson(key: string, value: unknown): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* quota exceeded or storage disabled */
  }
}

export function removeKey(key: string): void {
  try {
    localStorage.removeItem(PREFIX + key);
  } catch {
    /* storage disabled */
  }
}

export function storageEstimate(): number {
  try {
    let total = 0;
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      if (!key) continue;
      total += key.length + (localStorage.getItem(key)?.length ?? 0);
    }
    return total * 2; // UTF-16 characters
  } catch {
    return 0;
  }
}
