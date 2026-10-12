import type { Analysis } from "../lib/types";
import { percent } from "../lib/format";

export function HealthReport({ analysis }: { analysis: Analysis }) {
  const metrics = [
    {
      name: "CPU",
      value: analysis.cpu_percent,
      warning: 80,
      description: "Utilização do processador",
    },
    {
      name: "Memória",
      value: analysis.memory_percent,
      warning: 80,
      description: `${(Number(analysis.memory_used_bytes) / 1024 ** 3).toFixed(2)} de ${(Number(analysis.memory_total_bytes) / 1024 ** 3).toFixed(2)} GiB em uso`,
    },
    {
      name: "Disco principal",
      value: analysis.disk_percent,
      warning: 85,
      description: "Espaço ocupado no volume principal",
    },
  ].map((metric) => ({
    ...metric,
    level: metric.value >= 95 ? 2 : metric.value >= metric.warning ? 1 : 0,
  }));
  const level = Math.max(...metrics.map((metric) => metric.level));
  const labels = ["Bom", "Atenção", "Crítico"];
  const tones = ["good", "warning", "critical"];
  const problems = metrics.filter((metric) => metric.level > 0);
  const processes = analysis.top_processes ?? [];
  const cpuLeader = [...processes]
    .filter((p) => p.cpu_measured)
    .sort((a, b) => b.cpu_percent - a.cpu_percent)[0];
  const memoryLeader = [...processes].sort(
    (a, b) => Number(b.memory_bytes) - Number(a.memory_bytes),
  )[0];
  const findings: string[] = [];
  if (analysis.cpu_percent >= 80)
    findings.push(
      cpuLeader && cpuLeader.cpu_percent > 0
        ? `${cpuLeader.name} (PID ${cpuLeader.pid}) é o maior consumidor de CPU entre os processos coletados: ${percent(cpuLeader.cpu_percent)}% da capacidade total. Pode estar contribuindo para a carga elevada.`
        : "A CPU apresenta carga elevada, mas não há uma amostra válida por processo para identificar um contribuinte.",
    );
  if (analysis.memory_percent >= 80)
    findings.push(
      memoryLeader
        ? `${memoryLeader.name} (PID ${memoryLeader.pid}) tem o maior RSS entre os processos coletados: ${(Number(memoryLeader.memory_bytes) / 1024 ** 3).toFixed(2)} GiB (${percent(memoryLeader.memory_percent)}% da RAM). Pode estar contribuindo para a pressão de memória; RSS inclui páginas que podem ser compartilhadas.`
        : "A memória apresenta ocupação elevada, mas esta análise não contém dados por processo.",
    );
  if (analysis.disk_percent >= 85)
    findings.push(
      "O volume principal está com pouco espaço livre. Esta coleta não identifica quais arquivos ou programas ocupam o disco; não é possível atribuir a causa a um processo.",
    );
  const text = analysis.analysis_text
    .replace(/\*\*/g, "")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/<think>[\s\S]*?<\/think>/g, "")
    .trim();
  return (
    <section
      className="health-report"
      aria-label="Relatório de saúde do sistema"
    >
      <div className={`report-summary ${tones[level]}`}>
        <span className="report-label">
          ESTADO DA COLETA <b>{labels[level]}</b>
        </span>
        <h3>
          {level === 0
            ? "Nada a se preocupar nesta coleta."
            : level === 2
              ? "O sistema apresenta um indicador crítico."
              : "Alguns recursos precisam de atenção."}
        </h3>
        <p>
          {level === 0
            ? "CPU, memória e espaço em disco estão abaixo dos limites de alerta. Nenhuma sobrecarga foi identificada nesses indicadores."
            : `${problems.map((metric) => `${metric.name}: ${percent(metric.value)}% (${labels[metric.level].toLowerCase()})`).join(" · ")}. Confira as evidências antes de tomar uma ação.`}
        </p>
      </div>
      <div className="report-metrics">
        {metrics.map((metric) => (
          <article
            className={`report-card ${tones[metric.level]}`}
            key={metric.name}
          >
            <div>
              <h4>{metric.name}</h4>
              <span className="report-status">{labels[metric.level]}</span>
            </div>
            <strong>
              {percent(metric.value)}
              <small>%</small>
            </strong>
            <p>{metric.description}</p>
            <meter
              min="0"
              max="100"
              value={metric.value}
              aria-label={`${metric.name}: ${percent(metric.value)}%`}
            />
          </article>
        ))}
      </div>
      {findings.length > 0 && (
        <div className="report-section">
          <h3>Evidências e possíveis contribuintes</h3>
          {findings.map((finding) => (
            <p key={finding}>{finding}</p>
          ))}
          <small>
            Uma coleta isolada não confirma causalidade nem sobrecarga
            persistente.
          </small>
        </div>
      )}
      <div className="report-section">
        <h3>Próxima ação</h3>
        <p>
          {level === 0
            ? "Continue o monitoramento e compare novas coletas se perceber lentidão."
            : "Faça uma nova coleta para verificar se o comportamento persiste."}
        </p>
        {analysis.cpu_percent >= 80 && (
          <p>
            Revise as tarefas dos processos com maior CPU; evite encerrar
            serviços do sistema.
          </p>
        )}
        {analysis.memory_percent >= 80 && (
          <p>
            Revise aplicativos e abas sem uso e compare o consumo antes e
            depois.
          </p>
        )}
        {analysis.disk_percent >= 85 && (
          <p>
            Verifique os arquivos maiores e libere espaço com segurança no
            volume principal.
          </p>
        )}
      </div>
      <details className="report-details">
        <summary>Análise detalhada do modelo</summary>
        <div className="analysis-text">
          {text
            .split(/\n\s*\n/)
            .filter(Boolean)
            .map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
        </div>
      </details>
      <small className="report-method">
        Critérios desta interface: CPU e memória ≥80% em atenção e ≥95%
        críticos; disco ≥85% em atenção e ≥95% crítico. A classificação descreve
        esta coleta, sem prever falhas.
      </small>
    </section>
  );
}
