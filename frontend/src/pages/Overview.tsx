import {
  Activity,
  ArrowRight,
  Check,
  Clock3,
  Cpu,
  Eye,
  HardDrive,
  LoaderCircle,
  MemoryStick,
  Play,
  Server,
  Square,
} from "lucide-react";
import { Metric } from "../components/Metric";
import { MetricChart } from "../components/MetricChart";
import { Pipeline } from "../components/Pipeline";
import { percent, time } from "../lib/format";
import type { Analysis, Health, Snapshot, View } from "../lib/types";
interface Props {
  m: Snapshot | null;
  h: Health | null;
  samples: Snapshot[];
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
  samples,
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
  return (
    <>
      <div className="host-strip">
        <span>
          <Server size={16} />
          <strong>{m?.host_name || "Conectando ao host"}</strong>
          <span className="host-tag">HOST LOCAL</span>
        </span>
        <small>
          <Clock3 size={13} />
          {m
            ? `Ligado há ${Math.floor(Number(m.uptime_seconds) / 3600)}h`
            : "—"}
          <i />
          Última coleta {time(m?.captured_at)}
        </small>
      </div>
      <section className="metrics-grid" aria-label="Indicadores do sistema">
        <Metric
          label="Uso de CPU"
          value={percent(m?.cpu_percent)}
          progress={m?.cpu_percent}
          sub="Utilização no intervalo de coleta"
          icon={Cpu}
        />
        <Metric
          label="Memória RAM"
          value={percent(m?.memory_percent)}
          progress={m?.memory_percent}
          sub={
            m
              ? `${(Number(m.memory_used_bytes) / 2 ** 30).toFixed(1)} de ${(Number(m.memory_total_bytes) / 2 ** 30).toFixed(1)} GiB em uso`
              : "Aguardando coleta"
          }
          icon={MemoryStick}
          tone="violet"
        />
        <Metric
          label="Armazenamento"
          value={percent(m?.disk_percent)}
          progress={m?.disk_percent}
          sub="Ocupação do volume principal"
          icon={HardDrive}
          tone="blue"
        />
        <Metric
          label="Processos ativos"
          value={m?.process_count.toString() || "—"}
          sub="Processos identificados pelo SO"
          icon={Activity}
          tone="gray"
        />
      </section>
      <div className="dashboard-grid">
        <section className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h2>Atividade do sistema</h2>
              <p>Uma leitura contínua dos recursos do host.</p>
            </div>
            <span className="soft-tag">
              <span className={`dot ${m ? "green" : "amber"}`} />
              {m ? "Ao vivo" : "Sem conexão"}
            </span>
          </div>
          <div className="chart-legend">
            <span>
              <i className="lime-bg" />
              CPU <strong>{percent(m?.cpu_percent)}%</strong>
            </span>
            <span>
              <i className="violet-bg" />
              Memória <strong>{percent(m?.memory_percent)}%</strong>
            </span>
            <small>Últimas 60 coletas</small>
          </div>
          <MetricChart samples={samples} />
        </section>
        <section className="panel run-panel">
          <div className="run-icon">
            <Eye size={22} />
          </div>
          <span className="eyebrow">INTELIGÊNCIA LOCAL</span>
          <h2>Entenda o que está acontecendo.</h2>
          <p>
            Envie uma coleta para o Ollama e receba uma análise contextual do
            sistema.
          </p>
          <div className="segmented" aria-label="Modo de análise">
            <button
              aria-pressed={mode === "once"}
              disabled={busy}
              className={mode === "once" ? "selected" : ""}
              onClick={() => setMode("once")}
            >
              Análise única
            </button>
            <button
              aria-pressed={mode === "stream"}
              disabled={busy}
              className={mode === "stream" ? "selected" : ""}
              onClick={() => setMode("stream")}
            >
              Streaming
            </button>
          </div>
          {mode === "stream" && (
            <label className="count-label">
              Quantidade de coletas
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
          <button
            className="button primary"
            disabled={
              busy ||
              !m ||
              !h?.ollama.model_available ||
              !h?.grpc.available ||
              !h?.rabbitmq.available
            }
            onClick={() => void analyze()}
          >
            {busy ? (
              <LoaderCircle className="spin" size={17} />
            ) : (
              <Play size={16} />
            )}{" "}
            {busy
              ? mode === "stream"
                ? `Analisando · ${received}/${count}`
                : "Analisando…"
              : mode === "once"
                ? "Analisar agora"
                : "Iniciar streaming"}
            {!busy && <ArrowRight size={16} />}
          </button>
          {busy && (
            <button className="cancel" onClick={() => cancel()}>
              <Square size={12} />
              Cancelar solicitação
            </button>
          )}
          <small className="model-caption">
            {h?.ollama.model || "Ollama"} · execução no seu computador
          </small>
          {!h?.ok && (
            <small className="setup-hint">
              Confira os serviços na aba Pipeline.
            </small>
          )}
        </section>
      </div>
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
          <div>
            <h2>Pipeline de processamento</h2>
            <p>Uma arquitetura local, da coleta à persistência.</p>
          </div>
          <button className="text-button" onClick={() => setView("pipeline")}>
            Ver serviços
            <ArrowRight size={15} />
          </button>
        </div>
        <Pipeline health={h} />
      </section>
      <section className="panel latest-panel">
        <div className="panel-heading">
          <div>
            <h2>Última análise</h2>
            <p>
              {latest
                ? `${latest.model} · ${time(latest.analyzed_at)}`
                : "O próximo passo é executar sua primeira análise."}
            </p>
          </div>
          {latest && (
            <span className={`soft-tag ${latest.consumed_at ? "success" : ""}`}>
              {latest.consumed_at ? <Check size={13} /> : <Clock3 size={13} />}{" "}
              {latest.consumed_at
                ? "Consumo confirmado"
                : "Publicada · aguardando consumo"}
            </span>
          )}
        </div>
        {latest ? (
          <>
            <p className="analysis-preview">{latest.analysis_text}</p>
            <button className="text-button" onClick={() => setSelected(latest)}>
              Abrir análise completa
              <ArrowRight size={15} />
            </button>
          </>
        ) : (
          <div className="empty-state">
            <span>
              <Eye size={23} />
            </span>
            <div>
              <strong>Os números contam uma história.</strong>
              <p>
                Clique em “Analisar agora” para obter a primeira leitura do
                modelo local.
              </p>
            </div>
          </div>
        )}
      </section>
    </>
  );
}
