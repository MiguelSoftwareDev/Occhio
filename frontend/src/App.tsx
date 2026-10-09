import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ChevronRight,
  Eye,
  GitBranch,
  History as HistoryIcon,
  LayoutDashboard,
} from "lucide-react";
import { Detail } from "./components/Detail";
import { Overview } from "./pages/Overview";
import { HistoryPage } from "./pages/HistoryPage";
import { PipelinePage } from "./pages/PipelinePage";
import { GuidePage } from "./pages/GuidePage";
import { usePolling } from "./hooks/usePolling";
import { request, streamAnalyses, liveAnalysis } from "./lib/api";
import { emptyProgress } from "./lib/types";
import eye from "./assets/eye-blue.png";
import type {
  Progress,
  RuntimeInfo,
  Analysis,
  Health,
  History,
  Snapshot,
  View,
} from "./lib/types";

const nav = [
  { id: "overview", title: "Visão geral", icon: LayoutDashboard },
  { id: "history", title: "Histórico", icon: HistoryIcon },
  { id: "pipeline", title: "Pipeline", icon: GitBranch },
  { id: "guide", title: "Guia", icon: BookOpen },
] as const;
// Coordena o console e as requisições
export default function App() {
  const [view, setView] = useState<View>("overview");
  const [offset, setOffset] = useState(0);
  const runtime = usePolling<RuntimeInfo>("/runtime", 30000);
  const [progress, setProgress] = useState<Progress>(emptyProgress);
  const metrics = usePolling<Snapshot>("/metrics", 1000);
  const health = usePolling<Health>("/health", 10000);
  const history = usePolling<History>(
    `/history?limit=10&offset=${offset}`,
    4000,
  );
  const [selected, setSelected] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"once" | "stream">("once");
  const [count, setCount] = useState(3);
  const [received, setReceived] = useState(0);
  const [message, setMessage] = useState("");
  const [failure, setFailure] = useState("");
  const [published, setPublished] = useState<Analysis | null>(null);
  const abort = useRef<AbortController | null>(null);
  const [confirmed, setConfirmed] = useState<Analysis | null>(null);
  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => {
    if (!published) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function check() {
      try {
        const result = await request<Analysis>(
          `/history/${published!.analysis_id}`,
          { signal: controller.signal },
        );
        if (active) {
          setConfirmed(result);
          setProgress((p) => ({ ...p, sqlite: "done" }));
        }
      } catch {
        if (active) timer = setTimeout(check, 2000);
      }
    }
    void check();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [published]);
  const latest = published
    ? confirmed?.analysis_id === published.analysis_id
      ? confirmed
      : published
    : history.data?.items[0];
  const m = metrics.error ? null : metrics.data;
  const h = health.error ? null : health.data;

  // Executa o pipeline solicitado
  async function analyze() {
    setBusy(true);
    setProgress(emptyProgress());
    setPublished(null);
    setConfirmed(null);
    setFailure("");
    setReceived(0);
    setMessage(
      mode === "stream"
        ? "Streaming aberto. Aguardando a primeira análise…"
        : "Analisando as métricas no modelo local…",
    );
    const controller = new AbortController();
    abort.current = controller;
    try {
      if (mode === "once") {
        await liveAnalysis((event) => {
          if (event.type === "progress")
            setProgress((p) => ({ ...p, [event.stage]: event.status }));
          if (event.type === "result") {
            setPublished(event.result);
            setReceived(1);
          }
        }, controller.signal);
      } else
        await streamAnalyses(
          count,
          (result) => {
            setProgress({
              collect: "done",
              grpc: "done",
              ollama: "done",
              rabbitmq: "done",
              sqlite: "waiting",
            });
            setPublished(result);
            setReceived((value) => value + 1);
          },
          controller.signal,
          (event) => {
            if (event.type !== "progress") return;
            if (event.stage === "collect") {
              setPublished(null);
              setConfirmed(null);
              setProgress({ ...emptyProgress(), collect: event.status });
            } else setProgress((p) => ({ ...p, [event.stage]: event.status }));
          },
        );
      setMessage(
        "Publicação confirmada pelo broker. O consumo é verificado separadamente.",
      );
      history.refresh();
    } catch (err) {
      setProgress(
        (p) =>
          Object.fromEntries(
            Object.entries(p).map(([id, status]) => [
              id,
              status === "running"
                ? controller.signal.aborted
                  ? "cancelled"
                  : "error"
                : status,
            ]),
          ) as Progress,
      );
      if (controller.signal.aborted)
        setMessage(
          "Solicitação cancelada. Resultados já publicados continuam no pipeline.",
        );
      else {
        setFailure(err instanceof Error ? err.message : "Falha na análise");
        setMessage("");
      }
    } finally {
      setBusy(false);
      abort.current = null;
    }
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Pular para o conteúdo
      </a>
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("overview");
          }}
        >
          <img className="brand-eye" src={eye} alt="" />
          <span>Occhio</span>
        </a>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Menu principal">
          {nav.map((item) => (
            <button
              key={item.id}
              aria-label={item.title}
              aria-current={view === item.id ? "page" : undefined}
              className={view === item.id ? "active" : ""}
              onClick={() => {
                setView(item.id);
                setOffset(0);
              }}
            >
              <item.icon size={18} />
              {item.title}
              {view === item.id && <span className="nav-active" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="host-card">
            <span className={`dot ${runtime.data ? "green" : "amber"}`} />
            <strong>{runtime.data?.host_name || "Conectando…"}</strong>
            <small>
              {[runtime.data?.os, runtime.data?.environment]
                .filter(
                  (value, index, values) =>
                    value && values.indexOf(value) === index,
                )
                .join(" · ") || "Aguardando ambiente"}
            </small>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>{nav.find((n) => n.id === view)?.title}</strong>
          </div>
          <span className="local-badge">
            <span className="dot green" />
            {runtime.error
              ? "Ambiente indisponível"
              : runtime.data?.environment || "Identificando ambiente"}
          </span>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <span className="eyebrow">OBSERVE. ENTENDA. ACOMPANHE.</span>
              <h1>
                {view === "overview"
                  ? "Visão do sistema"
                  : view === "history"
                    ? "Histórico de análises."
                    : view === "pipeline"
                      ? "Do sistema à análise."
                      : "Pronto para observar."}
              </h1>
              <p>
                {view === "overview"
                  ? "Métricas reais e inteligência local, em um único lugar."
                  : view === "history"
                    ? "Resultados recebidos pela fila e persistidos pelo consumidor."
                    : view === "pipeline"
                      ? "Acompanhe os serviços que conectam cada etapa do processamento."
                      : "Prepare os serviços e explore o fluxo de análise."}
              </p>
            </div>
            <div className={`status-pill ${h?.ok ? "ok" : ""}`}>
              <span className={`dot ${h?.ok ? "green" : "amber"}`} />
              {h?.ok
                ? "Pipeline operacional"
                : health.data || health.error
                  ? "Pipeline indisponível"
                  : "Verificando serviços"}
            </div>
          </div>
          {(metrics.error || health.error || history.error) && (
            <div className="notice error" role="alert">
              Conexão com a API interrompida. Os dados anteriores podem estar
              desatualizados. Verifique os processos locais.
            </div>
          )}
          {view === "overview" && (
            <Overview
              runtime={runtime.data}
              progress={progress}
              m={m}
              h={h}
              mode={mode}
              setMode={setMode}
              busy={busy}
              count={count}
              setCount={setCount}
              received={received}
              analyze={analyze}
              cancel={() => abort.current?.abort()}
              message={message}
              failure={failure}
              latest={latest}
              setView={setView}
              setSelected={setSelected}
            />
          )}
          {view === "history" && (
            <HistoryPage
              history={history}
              offset={offset}
              setOffset={setOffset}
              setSelected={setSelected}
            />
          )}
          {view === "pipeline" && (
            <PipelinePage h={h} health={health} progress={progress} />
          )}
          {view === "guide" && <GuidePage />}
          <footer>
            <span>
              <Eye size={14} /> OCCHIO <i /> Observabilidade com inteligência
              local
            </span>
            <span>CPU · memória · processos · análise</span>
          </footer>
        </main>
      </div>
      {selected && (
        <Detail analysis={selected} close={() => setSelected(null)} />
      )}
    </div>
  );
}
