import type { Analysis } from "./types";

// Consulta a API local
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Falha HTTP ${response.status}`);
  }
  return response.json();
}

// Lê resultados incrementais
export async function streamAnalyses(
  count: number,
  onResult: (value: Analysis) => void,
  signal: AbortSignal,
  onProgress?: (event: import("./types").LiveEvent) => void,
) {
  const response = await fetch(
    `/api/analyze/stream?count=${count}&with_progress=true`,
    {
      method: "POST",
      signal,
    },
  );
  if (!response.ok) {
    const body = await response.json();
    throw new Error(body.detail || "Não foi possível abrir o streaming.");
  }
  if (!response.body)
    throw new Error("Streaming não disponível neste navegador.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let complete = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        if (event.type === "result") onResult(event.result);
        if (event.type === "progress") onProgress?.(event);
        if (event.type === "error") throw new Error(event.detail);
        if (event.type === "complete") complete = true;
      }
      if (done) break;
    }
    if (!complete)
      throw new Error("Conexão interrompida antes de concluir o streaming.");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

// Exporta dados consumidos
export function download(value: unknown, filename: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

// Recebe eventos confirmados pelos serviços
export async function liveAnalysis(
  onEvent: (event: import("./types").LiveEvent) => void,
  signal: AbortSignal,
) {
  const response = await fetch("/api/analyze/live", { method: "POST", signal });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Falha HTTP ${response.status}`);
  }
  if (!response.body)
    throw new Error("O navegador não disponibilizou o fluxo.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let complete = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      if (done && buffer.trim()) lines.push(buffer);
      for (const line of lines) {
        if (!line.trim()) continue;
        const event: import("./types").LiveEvent = JSON.parse(line);
        onEvent(event);
        if (event.type === "error") throw new Error(event.detail);
        if (event.type === "complete") complete = true;
      }
      if (done) break;
    }
    if (!complete)
      throw new Error("Conexão interrompida antes da confirmação.");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
