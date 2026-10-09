import { Pipeline } from "../components/Pipeline";
import type { Health, Progress } from "../lib/types";
interface Props {
  h: Health | null;
  progress: Progress;
  health: { refresh: () => void };
}

export function PipelinePage({ h, health, progress }: Props) {
  return (
    <>
      <section className="panel pipeline-panel">
        <div className="panel-heading">
          <div>
            <h2>Estado dos serviços</h2>
            <p>
              As verificações indicam disponibilidade; uma análise confirma o
              fluxo completo.
            </p>
          </div>
          <button className="button secondary" onClick={health.refresh}>
            Verificar agora
          </button>
        </div>
        <Pipeline health={h} progress={progress} />
      </section>
      <div className="service-grid">
        {[
          {
            title: "Ollama",
            ok: h?.ollama.model_available,
            value: h?.ollama.model || "Modelo local",
            desc:
              h?.ollama.available && !h.ollama.model_available
                ? "O serviço responde, mas o modelo configurado não está instalado."
                : "Gera a análise em texto a partir de métricas reais. Não utiliza API de IA externa.",
          },
          {
            title: "gRPC",
            ok: h?.grpc.available,
            value: "Unary + bidirectional streaming",
            desc: "AnalyzeSnapshot processa uma coleta. StreamSnapshots recebe e responde a múltiplas coletas pelo contrato .proto.",
          },
          {
            title: "RabbitMQ",
            ok: h?.rabbitmq.available,
            value: `${h?.rabbitmq.queued_messages ?? "—"} na fila · ${h?.rabbitmq.failed_messages ?? "—"} rejeitadas`,
            desc: "Publicação persistente com confirmação. Mensagens inválidas seguem para a fila de falhas.",
          },
          {
            title: "Consumidor",
            ok: h?.consumer,
            value: `${h?.rabbitmq.consumers ?? "—"} consumidor(es) conectado(s)`,
            desc: "Processo separado. Confirma a mensagem depois da gravação no SQLite; duplicatas não criam registros novos.",
          },
        ].map((service) => (
          <article className="panel service" key={service.title}>
            <div>
              <h2>{service.title}</h2>
              <span className={`dot ${service.ok ? "green" : "amber"}`} />
            </div>
            <strong>{service.value}</strong>
            <p>{service.desc}</p>
            <small>
              {service.ok
                ? "Disponível"
                : "Verifique a configuração e o processo"}
            </small>
          </article>
        ))}
      </div>
      <div className="notice">
        O percentual representa etapas confirmadas, não o tempo restante. Uma
        mensagem publicada pode aguardar na fila até o consumidor gravá-la no
        SQLite.
      </div>
    </>
  );
}
