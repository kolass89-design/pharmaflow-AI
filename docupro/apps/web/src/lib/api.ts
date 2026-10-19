/**
 * Typed client for the DOCUPRO conversion API.
 *
 * All URLs are relative by default so the web app works on any origin. The
 * desktop and mobile builds can point at a remote service through the
 * VITE_API_BASE build variable or the "service URL" setting.
 */

export type OptionType = "select" | "number" | "boolean" | "text" | "password" | "pages";

export interface Choice {
  value: string;
  label: string;
}

export interface ToolOption {
  key: string;
  label: string;
  type: OptionType;
  default: string | number | boolean | null;
  choices?: Choice[];
  minimum?: number;
  maximum?: number;
  step?: number;
  help?: string;
  required?: boolean;
  placeholder?: string;
  advanced?: boolean;
}

export interface Tool {
  id: string;
  category: "pdf" | "word" | "image" | "other";
  title: string;
  subtitle: string;
  description: string;
  input: {
    extensions: string[];
    label: string;
    mediaTypes: string[];
    maxFiles: number | null;
    allowsBatch: boolean;
  };
  outputKind: string;
  outputLabel: string;
  outputExtension: string;
  engine: string;
  options: ToolOption[];
  minFiles: number;
  maxFiles: number;
  batch: boolean;
  zipMultiple: boolean;
  limitations: string[];
  keywords: string[];
  offlineCapable: boolean;
  estimatedSeconds: number;
  featured: boolean;
  available: boolean;
  unavailableReason: string | null;
}

export interface Category {
  id: Tool["category"];
  label: string;
  description: string;
}

export interface Catalog {
  tools: Tool[];
  categories: Category[];
}

export interface Artifact {
  id: string;
  name: string;
  mediaType: string;
  size: number;
  meta: Record<string, unknown>;
  primary: boolean;
  url: string;
}

export interface JobError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface Job {
  id: string;
  tool: string;
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled" | "expired";
  progress: number;
  message: string;
  createdAt: number;
  startedAt: number | null;
  finishedAt: number | null;
  expiresAt: number | null;
  expiresInSeconds: number | null;
  inputs: { name: string; size: number; pages: number | null; kind: string }[];
  artifacts: Artifact[];
  error: JobError | null;
  meta: Record<string, unknown>;
  warnings: string[];
  options: Record<string, unknown>;
}

export interface Capabilities {
  version: string;
  engines: {
    pdf: string;
    wordLayout: string;
    docxRender: string;
    libreoffice: boolean;
    ocr: string | null;
    ocrLanguages: Choice[];
    images: string;
    spreadsheets: string;
  };
  limits: {
    maxUploadBytes: number;
    maxJobBytes: number;
    maxFilesPerJob: number;
    maxPages: number;
    maxPixels: number;
    retentionMinutes: number;
    conversionTimeoutSeconds: number;
    maxConcurrentJobs: number;
  };
  queue: { jobs: Record<string, number>; concurrency: number };
  privacy: {
    retentionMinutes: number;
    deleteAfterDownloadSeconds: number;
    storage: string;
    training: string;
  };
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;
  retryAfter?: number;

  constructor(message: string, code = "request_failed", status = 0, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
    const retry = details?.retryAfterSeconds;
    if (typeof retry === "number") this.retryAfter = retry;
  }
}

const BASE_KEY = "docupro.apiBase";

export function getApiBase(): string {
  try {
    const override = localStorage.getItem(BASE_KEY);
    if (override && override.trim()) return override.trim().replace(/\/+$/, "");
  } catch {
    /* storage unavailable */
  }
  const buildTime = import.meta.env.VITE_API_BASE as string | undefined;
  if (buildTime && buildTime.trim()) return buildTime.trim().replace(/\/+$/, "");
  return "";
}

export function setApiBase(value: string): void {
  try {
    if (value.trim()) localStorage.setItem(BASE_KEY, value.trim().replace(/\/+$/, ""));
    else localStorage.removeItem(BASE_KEY);
  } catch {
    /* storage unavailable */
  }
}

export function apiUrl(path: string): string {
  return `${getApiBase()}${path}`;
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: { error?: JobError } | null = null;
  try {
    payload = (await response.json()) as { error?: JobError };
  } catch {
    /* non-JSON response */
  }
  const error = payload?.error;
  return new ApiError(
    error?.message ?? `The server returned ${response.status}.`,
    error?.code ?? "request_failed",
    response.status,
    (error?.details as Record<string, unknown>) ?? {},
  );
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), { signal, headers: { Accept: "application/json" } });
  } catch (error) {
    if ((error as Error)?.name === "AbortError") throw error;
    throw new ApiError(
      "The conversion service is unreachable. Check your connection and try again.",
      "network_error",
    );
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export const fetchCatalog = (signal?: AbortSignal) => getJson<Catalog>("/api/tools", signal);
export const fetchCapabilities = (signal?: AbortSignal) => getJson<Capabilities>("/api/capabilities", signal);

export interface CreateJobInput {
  tool: string;
  files: File[];
  options: Record<string, string | number | boolean | null>;
  order?: string;
  onUploadProgress?: (percent: number) => void;
  signal?: AbortSignal;
}

/** Upload files and start a conversion, reporting real upload progress. */
export function createJob(input: CreateJobInput): Promise<Job> {
  return new Promise<Job>((resolve, reject) => {
    const form = new FormData();
    form.append("tool", input.tool);
    form.append("options", JSON.stringify(input.options ?? {}));
    if (input.order) form.append("order", input.order);
    for (const file of input.files) form.append("files", file, file.name);

    const request = new XMLHttpRequest();
    request.open("POST", apiUrl("/api/jobs"));
    request.responseType = "json";
    request.setRequestHeader("Accept", "application/json");

    const abort = () => request.abort();
    input.signal?.addEventListener("abort", abort, { once: true });

    request.upload.onprogress = (event) => {
      if (event.lengthComputable && input.onUploadProgress) {
        input.onUploadProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)));
      }
    };
    request.onerror = () => {
      input.signal?.removeEventListener("abort", abort);
      reject(new ApiError("The upload failed. Check your connection and try again.", "network_error"));
    };
    request.onabort = () => {
      input.signal?.removeEventListener("abort", abort);
      reject(new ApiError("The upload was cancelled.", "cancelled"));
    };
    request.onload = () => {
      input.signal?.removeEventListener("abort", abort);
      const status = request.status;
      const body = request.response as
        | (Job & { error?: JobError })
        | { error?: JobError }
        | null;
      if (status >= 200 && status < 300) {
        resolve(body as Job);
        return;
      }
      const error = (body as { error?: JobError } | null)?.error;
      reject(
        new ApiError(
          error?.message ?? "The conversion could not be started.",
          error?.code ?? "request_failed",
          status,
          (error?.details as Record<string, unknown>) ?? {},
        ),
      );
    };
    request.send(form);
  });
}

export const getJob = (id: string, signal?: AbortSignal) => getJson<Job>(`/api/jobs/${id}`, signal);

export async function cancelJob(id: string): Promise<Job> {
  const response = await fetch(apiUrl(`/api/jobs/${id}/cancel`), { method: "POST" });
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as Job;
}

export async function deleteJob(id: string): Promise<void> {
  const response = await fetch(apiUrl(`/api/jobs/${id}`), { method: "DELETE" });
  if (!response.ok && response.status !== 404) throw await parseError(response);
}

/** Download an artifact as a Blob (keeps capability tokens out of new tabs). */
export async function fetchArtifact(url: string): Promise<{ blob: Blob; filename: string | null }> {
  const response = await fetch(apiUrl(url));
  if (!response.ok) throw await parseError(response);
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = /filename\*=UTF-8''([^;]+)/i.exec(disposition) ?? /filename="([^"]+)"/i.exec(disposition);
  const filename = match ? decodeURIComponent(match[1]) : null;
  return { blob: await response.blob(), filename };
}

export async function saveArtifact(
  url: string,
  fallbackName: string,
): Promise<"saved" | "cancelled"> {
  const { blob, filename } = await fetchArtifact(url);
  const { saveBlob } = await import("./save");
  return saveBlob(blob, filename ?? fallbackName);
}

export async function checkHealth(base?: string): Promise<{ ok: boolean; version?: string; message?: string }> {
  try {
    const response = await fetch(`${base ? base.replace(/\/+$/, "") : getApiBase()}/api/health`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return { ok: false, message: `HTTP ${response.status}` };
    const data = (await response.json()) as { status: string; version: string };
    return { ok: data.status === "ok", version: data.version };
  } catch (error) {
    return { ok: false, message: (error as Error).message };
  }
}
