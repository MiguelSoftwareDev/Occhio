import {
  ArrowDownToLine,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  History as HistoryIcon,
} from "lucide-react";
import { download } from "../lib/api";
import { percent } from "../lib/format";
import type { Analysis, History } from "../lib/types";
import type { Dispatch, SetStateAction } from "react";
interface Props {
  history: { data: History | null };
  offset: number;
  setOffset: Dispatch<SetStateAction<number>>;
  setSelected: (v: Analysis) => void;
}

export function HistoryPage({
  history,
  offset,
  setOffset,
  setSelected,
}: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>
            Análises consumidas{" "}
            <span className="number-badge">{history.data?.total ?? "—"}</span>
          </h2>
          <p>
            Selecione um resultado para consultar as métricas e exportar a
            evidência.
          </p>
        </div>
        <button
          className="button secondary"
          disabled={!history.data?.items.length}
          onClick={() => download(history.data, "occhio-historico-pagina.json")}
        >
          <ArrowDownToLine size={16} />
          Exportar página
        </button>
      </div>
      {history.data?.items.length ? (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Coleta / host</th>
                  <th>CPU</th>
                  <th>Memória</th>
                  <th>Modelo</th>
                  <th>Inferência</th>
                  <th>Resultado</th>
                </tr>
              </thead>
              <tbody>
                {history.data.items.map((item) => (
                  <tr key={item.analysis_id}>
                    <td>
                      <strong>
                        {new Date(item.analyzed_at).toLocaleString("pt-BR")}
                      </strong>
                      <small>{item.host_name}</small>
                    </td>
                    <td>{percent(item.cpu_percent)}%</td>
                    <td>{percent(item.memory_percent)}%</td>
                    <td>{item.model}</td>
                    <td>{(item.inference_ms / 1000).toFixed(1)}s</td>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => setSelected(item)}
                      >
                        Consultar
                        <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>
              {offset + 1}–{offset + history.data.items.length} de{" "}
              {history.data.total}
            </span>
            <div>
              <button
                aria-label="Página anterior"
                disabled={offset === 0}
                onClick={() => setOffset((value) => Math.max(0, value - 10))}
              >
                <ChevronLeft size={18} />
              </button>
              <button
                aria-label="Próxima página"
                disabled={offset + 10 >= history.data.total}
                onClick={() => setOffset((value) => value + 10)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <HistoryIcon />
          <div>
            <strong>Nenhuma análise nesta página.</strong>
            <p>
              Os resultados aparecem aqui após o consumidor confirmar a
              gravação.
            </p>
            {offset > 0 && (
              <button className="text-button" onClick={() => setOffset(0)}>
                Voltar ao início
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
