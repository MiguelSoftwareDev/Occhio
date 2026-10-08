import type { Snapshot } from "../lib/types";

// Desenha a série coletada nesta sessão || Draw this session's collected series
export function MetricChart({ samples }: { samples: Snapshot[] }) {
  const width = 800,
    height = 190;
  const points = (key: "cpu_percent" | "memory_percent") =>
    samples
      .map(
        (s, i) =>
          `${(i / Math.max(samples.length - 1, 1)) * width},${height - (s[key] / 100) * height}`,
      )
      .join(" ");
  return (
    <div
      className="chart"
      role="img"
      aria-label={`CPU e memória nas últimas ${samples.length} coletas. Escala de 0 a 100%.`}
    >
      <div className="chart-labels">
        <span>100%</span>
        <span>75%</span>
        <span>50%</span>
        <span>25%</span>
        <span>0%</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="cpuFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#b8ef77" stopOpacity=".15" />
            <stop offset="100%" stopColor="#b8ef77" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 25, 50, 75, 100].map((n) => (
          <line
            key={n}
            x1="0"
            x2={width}
            y1={(height * n) / 100}
            y2={(height * n) / 100}
            stroke="#2a3034"
            strokeDasharray="3 6"
          />
        ))}
        {samples.length > 1 && (
          <>
            <polygon
              points={`0,${height} ${points("cpu_percent")} ${width},${height}`}
              fill="url(#cpuFill)"
            />
            <polyline
              points={points("memory_percent")}
              fill="none"
              stroke="#9a9ded"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
            <polyline
              points={points("cpu_percent")}
              fill="none"
              stroke="#b8ef77"
              strokeWidth="2.5"
              vectorEffect="non-scaling-stroke"
            />
          </>
        )}
      </svg>
      {samples.length < 2 && (
        <p className="chart-empty">
          Aguardando duas coletas para desenhar a série…
        </p>
      )}
      <div className="chart-time">
        <span>
          {samples[0]
            ? new Date(samples[0].captured_at).toLocaleTimeString("pt-BR")
            : "—"}
        </span>
        <span>Coleta a cada ~3 segundos · sessão atual</span>
        <span>agora</span>
      </div>
    </div>
  );
}
