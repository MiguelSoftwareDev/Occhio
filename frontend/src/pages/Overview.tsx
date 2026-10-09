import { useState } from "react";
import { StorageDialog } from "../components/StorageDialog";
import {
  Activity,
  ArrowRight,
  Clock3,
  Cpu,
  HardDrive,
  MemoryStick,
  Play,
  Server,
  Square,
} from "lucide-react";
import { Metric } from "../components/Metric";
import { Pipeline } from "../components/Pipeline";
import { ProcessRadar, memorySize } from "../components/ProcessRadar";
import { percent, time } from "../lib/format";
import type {
  Analysis,
  Health,
  Snapshot,
  View,
  Progress,
  RuntimeInfo,
} from "../lib/types";
interface Props {
  m: Snapshot | null;
  h: Health | null;
  runtime: RuntimeInfo | null;
  progress: Progress;
  mode: "once" | "stream";
  setMode: (v: "once" | "stream") => void;
  busy: boolean;
  count: number;
  setCount: (v: number) => void;
  received: number;
  analyze: () => Promise<void>;
  cancel: () => void;
  message: string;
  failure: string;
  latest?: Analysis;
  setView: (v: View) => void;
  setSelected: (v: Analysis) => void;
}
export function Overview({
  m,
  h,
  runtime,
  progress,
  mode,
  setMode,
  busy,
  count,
  setCount,
  received,
  analyze,
  cancel,
  message,
  failure,
  latest,
  setView,
  setSelected,
}: Props) {
  const [storageOpen, setStorageOpen] = useState(false);
  const missing = [
    !h?.ollama.model_available && "Ollama/modelo",
    !h?.grpc.available && "gRPC",
    !h?.rabbitmq.available && "RabbitMQ",
  ]
    .filter(Boolean)
    .join(", ");
  const available =
    !!m &&
    !!h?.ollama.model_available &&
    !!h?.grpc.available &&
    !!h?.rabbitmq.available;
  return (
    <>
      <div className="host-strip">
        <span>
          <Server size={16} />
          <strong>
            {m?.host_name || runtime?.host_name || "Identificando host…"}
          </strong>
          <span className="host-tag">{runtime?.os || "—"}</span>
        </span>
        <small>
          <Clock3 size={14} />
          Última coleta {time(m?.captured_at)}
        </small>
      </div>
      <section className="metrics-grid" aria-label="Indicadores do sistema">
        <Metric
          label="CPU"
          value={percent(m?.cpu_percent)}
          progress={m?.cpu_percent}
          sub="Uso total da máquina"
          icon={Cpu}
        />
        <Metric
          label="Memória"
          value={percent(m?.memory_percent)}
          progress={m?.memory_percent}
          sub={
            m
              ? `${memorySize(Number(m.memory_used_bytes))} de ${memorySize(Number(m.memory_total_bytes))}`
              : "Aguardando coleta"
          }
          icon={MemoryStick}
        />
        <Metric
          label="Armazenamento"
          value={percent(m?.disk_percent)}
          progress={m?.disk_percent}
          sub="Volume do sistema · clique no ícone para ver todos"
          onClick={() => setStorageOpen(true)}
          icon={HardDrive}
        />
        <Metric
          label="Processos"
          value={m?.process_count.toString() || "—"}
          sub="Identificados pelo sistema"
          icon={Activity}
          tone="gray"
        />
      </section>
      <div className="radar-top">
        <section className="panel radar-heading">
          <h2>
            Radar de processos{" "}
            <span className="slashes" aria-hidden="true">
              ///
            </span>
          </h2>
          <div className="memory-summary">
            <MemoryStick size={18} />
            <span>
              Total{" "}
              <strong>
                {m ? memorySize(Number(m.memory_total_bytes)) : "—"}
              </strong>
            </span>
            <span>
              Em uso{" "}
              <strong>
                {m ? memorySize(Number(m.memory_used_bytes)) : "—"}
              </strong>
            </span>
            <strong>{percent(m?.memory_percent)}%</strong>
          </div>
        </section>
        <div className="panel action-box">
          <button
            className="button primary"
            disabled={busy || !available}
            onClick={() => void analyze()}
            title={
              !available ? "Verifique os serviços na aba Pipeline" : undefined
            }
          >
            <Play size={17} />
            {busy
              ? "Analisando…"
              : mode === "stream"
                ? "Iniciar streaming"
                : "Analisar agora"}
          </button>
        </div>
      </div>
      <p className="monitor-caption">
        Monitoramento ao vivo · A análise por IA só começa quando você solicita.
      </p>
      <ProcessRadar />
      {storageOpen && <StorageDialog close={() => setStorageOpen(false)} />}
      {!available && (
        <div className="setup-line">
          {!m
            ? "Aguardando métricas da máquina monitorada."
            : `Análise manual indisponível: ${missing}. Abra o Guia para iniciar os serviços.`}
          <button className="text-button" onClick={() => setView("pipeline")}>
            Ver serviços <ArrowRight size={14} />
          </button>
        </div>
      )}
      {(message || failure) && (
        <div
          className={`notice ${failure ? "error" : ""}`}
          role={failure ? "alert" : "status"}
        >
          {failure || message}
        </div>
      )}
      <section className="panel pipeline-panel">
        <div className="panel-heading">
          <h2>
            Pipeline de processamento{" "}
            <span className="slashes" aria-hidden="true">
              ///
            </span>
          </h2>
          <button className="text-button" onClick={() => setView("pipeline")}>
            Serviços <ArrowRight size={14} />
          </button>
        </div>
        <Pipeline health={h} progress={progress} />
      </section>
      <details className="analysis-options">
        <summary>
          Opções de análise{" "}
          {busy && mode === "stream" ? `· ${received}/${count}` : ""}
        </summary>
        <div>
          <label>
            Modo{" "}
            <select
              disabled={busy}
              value={mode}
              onChange={(e) => setMode(e.target.value as "once" | "stream")}
            >
              <option value="once">Análise única</option>
              <option value="stream">Streaming gRPC</option>
            </select>
          </label>
          {mode === "stream" && (
            <label>
              Coletas{" "}
              <select
                disabled={busy}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
              >
                {[2, 3, 5, 10].map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
          )}
          <small>{h?.ollama.model || "Ollama"}</small>
        </div>
      </details>
      {busy && (
        <button className="button secondary cancel" onClick={cancel}>
          <Square size={12} />
          Cancelar solicitação
        </button>
      )}
      <section className="panel latest-panel">
        <div className="panel-heading">
          <h2>Última análise</h2>
          {latest && (
            <span className="soft-tag">
              {latest.consumed_at ? "Salva no histórico" : "Aguardando consumo"}
            </span>
          )}
        </div>
        {latest ? (
          <>
            <p className="analysis-preview">{latest.analysis_text}</p>
            <button className="text-button" onClick={() => setSelected(latest)}>
              Abrir análise completa <ArrowRight size={14} />
            </button>
          </>
        ) : (
          <p>Os resultados aparecerão aqui depois da primeira análise.</p>
        )}
      </section>
    </>
  );
}
