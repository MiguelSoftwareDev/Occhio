import { Cpu } from "lucide-react";
// Exibe um indicador do host
export function Metric({
  label,
  value,
  sub,
  icon: Icon,
  tone = "lime",
  progress,
  onClick,
}: {
  label: string;
  value: string;
  sub: string;
  icon: typeof Cpu;
  tone?: string;
  progress?: number;
  onClick?: () => void;
}) {
  return (
    <article className={`metric ${tone}`}>
      <div className="metric-label">
        {label}
        {onClick ? (
          <button
            className="icon-button"
            onClick={onClick}
            aria-label="Ver todos os discos"
          >
            <Icon size={20} />
          </button>
        ) : (
          <Icon size={17} />
        )}
      </div>
      <div className="metric-value">
        {value}
        {progress !== undefined && <span>%</span>}
      </div>
      <div className="meter">
        <i style={{ width: `${progress ?? 0}%` }} />
      </div>
      <small>{sub}</small>
    </article>
  );
}
