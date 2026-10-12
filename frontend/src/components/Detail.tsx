import { useEffect, useRef } from "react";
import { ArrowDownToLine, X } from "lucide-react";
import type { Analysis } from "../lib/types";
import { download } from "../lib/api";
import { percent } from "../lib/format";
import { HealthReport } from "./HealthReport";
// Abre os detalhes com foco acessível
export function Detail({
  analysis,
  close,
}: {
  analysis: Analysis;
  close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  return (
    <dialog
      ref={dialog}
      onCancel={close}
      onClick={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <div className="dialog-head">
        <div>
          <span className="eyebrow">ANÁLISE DO SISTEMA</span>
          <h2>{analysis.host_name}</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Fechar detalhes"
          onClick={close}
        >
          <X size={20} />
        </button>
      </div>
      <div className="detail-meta">
        <span>{new Date(analysis.analyzed_at).toLocaleString("pt-BR")}</span>
        <span>{analysis.model}</span>
        <span>{(analysis.inference_ms / 1000).toFixed(1)}s de inferência</span>
      </div>
      <HealthReport analysis={analysis} />
      <dl>
        <dt>ID</dt>
        <dd>{analysis.analysis_id}</dd>
        <dt>CPU / memória / disco</dt>
        <dd>
          {percent(analysis.cpu_percent)}% / {percent(analysis.memory_percent)}%
          / {percent(analysis.disk_percent)}%
        </dd>
        <dt>Consumo confirmado</dt>
        <dd>
          {analysis.consumed_at
            ? new Date(analysis.consumed_at).toLocaleString("pt-BR")
            : "Aguardando consumidor"}
        </dd>
        <dt>Prompt</dt>
        <dd>{analysis.prompt_version}</dd>
      </dl>
      <button
        className="button secondary"
        onClick={() =>
          download(analysis, `occhio-${analysis.analysis_id}.json`)
        }
      >
        <ArrowDownToLine size={16} />
        Exportar análise
      </button>
    </dialog>
  );
}
