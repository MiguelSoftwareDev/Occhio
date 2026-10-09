import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { Health, Progress } from "../lib/types";
import { emptyProgress, stageIds } from "../lib/types";
const names = ["Coleta", "gRPC", "Ollama", "RabbitMQ", "SQLite"];
const labels = {
  idle: "Aguardando",
  running: "Processando",
  done: "Concluído",
  waiting: "Aguardando consumo",
  error: "Falhou",
  cancelled: "Interrompido",
};
export function Pipeline({
  health,
  progress = emptyProgress(),
}: {
  health: Health | null;
  progress?: Progress;
}) {
  const completed = stageIds.filter((id) => progress[id] === "done").length;
  const active = stageIds.findIndex((id) =>
    ["running", "waiting", "error", "cancelled"].includes(progress[id]),
  );
  const target =
    active >= 0
      ? active
      : Math.max(
          0,
          stageIds.reduce(
            (last, id, i) => (progress[id] === "done" ? i : last),
            0,
          ),
        );
  const previous = useRef(target);
  const [walking, setWalking] = useState(false);
  const [duration, setDuration] = useState(0);
  useEffect(() => {
    const distance = Math.abs(target - previous.current);
    previous.current = target;
    if (!distance) return;
    const ms = 650 * distance;
    setDuration(ms);
    setWalking(true);
    const timer = setTimeout(() => setWalking(false), ms);
    return () => clearTimeout(timer);
  }, [target]);
  const working =
    active >= 0 &&
    ["running", "waiting"].includes(progress[stageIds[active]]) &&
    !walking;
  const ready = [
    true,
    health?.grpc.available,
    health?.ollama.model_available,
    health?.rabbitmq.available,
    health?.consumer,
  ];
  return (
    <div className="journey">
      <div className="journey-summary">
        <div
          className="pixel-meter"
          role="progressbar"
          aria-label="Etapas concluídas"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={completed * 20}
        >
          <i style={{ width: `${completed * 20}%` }} />
        </div>
        <strong>{completed * 20}%</strong>
        <small>{completed}/5 etapas confirmadas</small>
      </div>
      <div
        className="village-scroll"
        tabIndex={0}
        aria-label="Pipeline com cinco estações e caminho do pinguim"
      >
        <div className="village">
          <div className="stations">
            {stageIds.map((id, i) => (
              <div
                key={id}
                className={`station ${progress[id]} ${active === i ? "current" : ""}`}
              >
                <div
                  className="house-art"
                  style={{ "--house": i } as CSSProperties}
                  role="img"
                  aria-label={`Estação ${names[i]}`}
                />
                <strong>{names[i]}</strong>
                <div className={`stage-progress ${progress[id]}`}>
                  <i />
                </div>
                <small>
                  {progress[id] === "idle" && !ready[i]
                    ? "Serviço indisponível"
                    : labels[progress[id]]}
                </small>
              </div>
            ))}
          </div>
          <div className="walkway">
            <div className="road" />
            <div
              className={`traveler ${walking ? "walking" : working ? "working" : "resting"}`}
              style={{
                left: `${10 + target * 20}%`,
                transitionDuration: `${duration}ms`,
              }}
              aria-label={
                walking
                  ? `Pinguim indo para ${names[target]}`
                  : working
                    ? `Pinguim programando em ${names[target]}`
                    : "Pinguim aguardando"
              }
            >
              <div className="penguin-sprite" />
              <div className="penguin-foot left-foot" />
              <div className="penguin-foot right-foot" />
            </div>
          </div>
        </div>
      </div>
      <p className="journey-caption" aria-live="polite">
        {completed === 5
          ? "Resultado consumido e salvo. Percurso concluído."
          : active >= 0
            ? `${names[active]} · ${labels[progress[stageIds[active]]]}`
            : "Pronto para iniciar o percurso."}
      </p>
    </div>
  );
}
