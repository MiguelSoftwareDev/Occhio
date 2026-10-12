export interface Snapshot {
  host_name: string;
  captured_at: string;
  cpu_percent: number;
  memory_percent: number;
  memory_used_bytes: number | string;
  memory_total_bytes: number | string;
  disk_percent: number;
  process_count: number;
  uptime_seconds: number | string;
  top_processes?: {
    pid: number;
    name: string;
    cpu_percent: number;
    cpu_measured: boolean;
    memory_bytes: number | string;
    memory_percent: number;
  }[];
}
export interface Analysis extends Snapshot {
  analysis_id: string;
  analyzed_at: string;
  model: string;
  analysis_text: string;
  inference_ms: number;
  prompt_version: string;
  consumed_at?: string;
}
export interface Health {
  ok: boolean;
  ollama: { available: boolean; model: string; model_available: boolean };
  grpc: { available: boolean };
  rabbitmq: {
    available: boolean;
    consumers: number;
    queued_messages: number;
    failed_messages: number;
  };
  consumer: boolean;
}
export interface History {
  items: Analysis[];
  total: number;
  offset: number;
  limit: number;
}
export type View = "overview" | "history" | "pipeline" | "guide";

export interface RuntimeInfo {
  host_name: string;
  os: string;
  os_release: string;
  environment: string;
  scope: string;
}
export interface ProcessInfo {
  pid: number;
  name: string;
  started_at: number;
  cpu_percent: number | null;
  memory_bytes: number;
  memory_percent: number;
  icon_url: string | null;
}
export interface ProcessSnapshot {
  items: ProcessInfo[];
  captured_at: string;
  inaccessible: number;
}
export const stageIds = [
  "collect",
  "grpc",
  "ollama",
  "rabbitmq",
  "sqlite",
] as const;
export type StageId = (typeof stageIds)[number];
export type StageStatus =
  | "idle"
  | "running"
  | "done"
  | "waiting"
  | "error"
  | "cancelled";
export type Progress = Record<StageId, StageStatus>;
export const emptyProgress = (): Progress => ({
  collect: "idle",
  grpc: "idle",
  ollama: "idle",
  rabbitmq: "idle",
  sqlite: "idle",
});
export type LiveEvent =
  | { type: "progress"; stage: StageId; status: StageStatus }
  | { type: "result"; result: Analysis }
  | { type: "complete" }
  | { type: "error"; detail: string };
