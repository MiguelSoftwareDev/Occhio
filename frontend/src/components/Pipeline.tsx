import {
  Activity,
  ArrowRight,
  Cpu,
  Database,
  GitBranch,
  Radio,
} from "lucide-react";
import type { Health } from "../lib/types";
// Mostra a prontidão de cada etapa || Show readiness for each stage
export function Pipeline({ health }: { health: Health | null }) {
  const stages = [
    { name: "Coleta", sub: "psutil · host local", icon: Activity, ok: null },
    {
      name: "Transporte",
      sub: "gRPC · Protobuf",
      icon: GitBranch,
      ok: health?.grpc.available,
    },
    {
      name: "Análise local",
      sub: health?.ollama.model || "Ollama",
      icon: Cpu,
      ok: health?.ollama.model_available,
    },
    {
      name: "Mensageria",
      sub: "RabbitMQ · AMQP",
      icon: Radio,
      ok: health?.rabbitmq.available,
    },
    {
      name: "Persistência",
      sub: "Consumidor · SQLite",
      icon: Database,
      ok: health?.consumer,
    },
  ];
  return (
    <div className="pipeline">
      {stages.map((stage, i) => (
        <div className="pipeline-part" key={stage.name}>
          <div className="stage">
            <div className="stage-top">
              <stage.icon size={19} />
              <span
                className={`dot ${stage.ok === null ? "neutral" : stage.ok ? "green" : "amber"}`}
              />
            </div>
            <strong>{stage.name}</strong>
            <small>{stage.sub}</small>
          </div>
          {i < 4 && <ArrowRight size={15} className="stage-arrow" />}
        </div>
      ))}
    </div>
  );
}
