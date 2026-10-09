import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { usePolling } from "../hooks/usePolling";
import type { ProcessInfo, ProcessSnapshot } from "../lib/types";
import { percent } from "../lib/format";
export function memorySize(bytes: number) {
  const gb = bytes / 2 ** 30;
  return gb >= 1
    ? `${gb.toLocaleString("pt-BR", { maximumFractionDigits: 2 })} GiB`
    : `${(bytes / 2 ** 20).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MiB`;
}
function AppIcon({ process }: { process: ProcessInfo }) {
  const [failed, setFailed] = useState(false);
  return process.icon_url && !failed ? (
    <img
      className="process-icon"
      src={process.icon_url}
      alt=""
      loading="lazy"
      onError={() => setFailed(true)}
    />
  ) : (
    <span
      className="missing-icon"
      title="O sistema não forneceu ícone para este processo"
      aria-label="Ícone indisponível"
    >
      —
    </span>
  );
}
export function ProcessRadar() {
  const { data, error } = usePolling<ProcessSnapshot>("/processes", 3000);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("memory");
  const items = useMemo(
    () =>
      (data?.items || [])
        .filter(
          (p) =>
            p.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()) ||
            String(p.pid).includes(search),
        )
        .sort((a, b) =>
          sort === "cpu"
            ? (b.cpu_percent ?? -1) - (a.cpu_percent ?? -1)
            : sort === "name"
              ? a.name.localeCompare(b.name)
              : b.memory_bytes - a.memory_bytes,
        ),
    [data, search, sort],
  );
  return (
    <section
      className="panel process-panel"
      aria-label="Processos reais do sistema"
    >
      <div className="process-tools">
        <label className="search-field">
          <Search size={15} />
          <input
            aria-label="Buscar processo ou PID"
            placeholder="Buscar processo ou PID…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label className="sort-field">
          Ordenar{" "}
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="memory">Memória</option>
            <option value="cpu">CPU</option>
            <option value="name">Nome</option>
          </select>
        </label>
      </div>
      {error && (
        <div className="notice error" role="alert">
          Não foi possível atualizar os processos.{" "}
          {data ? "Dados anteriores exibidos." : "Verifique a conexão."}
        </div>
      )}
      <div
        className="process-scroll"
        tabIndex={0}
        aria-label="Lista de processos; role para ver mais"
      >
        <table className="process-table">
          <thead>
            <tr>
              <th>Processo</th>
              <th>CPU</th>
              <th>Memória</th>
              <th>Uso da RAM total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={`${p.pid}:${p.started_at}`}>
                <td>
                  <div className="process-name">
                    <AppIcon key={p.icon_url} process={p} />
                    <div>
                      <strong title={p.name}>{p.name}</strong>
                      <small>PID {p.pid}</small>
                    </div>
                  </div>
                </td>
                <td>
                  {p.cpu_percent === null ? (
                    <span title="Aguardando a segunda amostra">—</span>
                  ) : (
                    `${percent(p.cpu_percent)}%`
                  )}
                </td>
                <td>{memorySize(p.memory_bytes)}</td>
                <td>
                  <div className="resource-use">
                    <div
                      className="pixel-meter"
                      role="meter"
                      aria-label={`Memória de ${p.name}`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={p.memory_percent}
                    >
                      <i
                        style={{ width: `${Math.min(100, p.memory_percent)}%` }}
                      />
                    </div>
                    <span>{percent(p.memory_percent)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <div className="empty-state">
            {!data ? "Coletando processos…" : "Nenhum processo encontrado."}
          </div>
        )}
      </div>
      <div className="process-foot">
        <span>
          {data ? `${items.length} processos visíveis` : "Aguardando o coletor"}
          {!!data?.inaccessible && ` · ${data.inaccessible} sem acesso`}
        </span>
      </div>
    </section>
  );
}
