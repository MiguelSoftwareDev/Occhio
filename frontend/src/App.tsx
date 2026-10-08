import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ChevronRight,
  CircleHelp,
  Eye,
  GitBranch,
  History as HistoryIcon,
  LayoutDashboard,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { Detail } from "./components/Detail";
import { Overview } from "./pages/Overview";
import { HistoryPage } from "./pages/HistoryPage";
import { PipelinePage } from "./pages/PipelinePage";
import { GuidePage } from "./pages/GuidePage";
import { usePolling } from "./hooks/usePolling";
import { request, streamAnalyses } from "./lib/api";
import type { Analysis, Health, History, Snapshot, View } from "./lib/types";

const nav = [
  { id: "overview", title: "Visão geral", icon: LayoutDashboard },
  { id: "history", title: "Histórico", icon: HistoryIcon },
  { id: "pipeline", title: "Pipeline", icon: GitBranch },
  { id: "guide", title: "Guia de execução", icon: BookOpen },
] as const;
// Coordena o console e as requisições || Coordinate the console and requests
export default function App() {
  const [view, setView] = useState<View>("overview");
  const [offset, setOffset] = useState(0);
  const metrics = usePolling<Snapshot>("/metrics", 2500);
  const health = usePolling<Health>("/health", 10000);
  const history = usePolling<History>(
    `/history?limit=10&offset=${offset}`,
    4000,
  );
  const [samples, setSamples] = useState<Snapshot[]>([]);
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
  useEffect(() => {
    if (metrics.data)
      setSamples((values) => [...values, metrics.data!].slice(-60));
  }, [metrics.data]);
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
        if (active) setConfirmed(result);
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

  // Executa o pipeline solicitado || Run the requested pipeline
  async function analyze() {
    setBusy(true);
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
        const result = await request<Analysis>("/analyze/once", {
          method: "POST",
          signal: controller.signal,
        });
        setPublished(result);
        setReceived(1);
      } else
        await streamAnalyses(
          count,
          (result) => {
            setPublished(result);
            setReceived((value) => value + 1);
          },
          controller.signal,
        );
      setMessage(
        "Publicação confirmada pelo broker. O consumo é verificado separadamente.",
      );
      history.refresh();
    } catch (err) {
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
          <span className="brand-symbol">
            <Eye size={26} />
          </span>
          occhio<span className="brand-dot">.</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">
            <Terminal size={16} />
          </span>
          <div>
            <strong>Local workspace</strong>
            <small>Observabilidade de sistemas</small>
          </div>
          <span className="version">v2</span>
        </div>
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
          <div className="local-card">
            <ShieldCheck size={21} />
            <strong>Seus dados ficam aqui.</strong>
            <p>
              Inferência local. Sem enviar métricas para serviços de IA na
              nuvem.
            </p>
          </div>
          <button className="help-link" onClick={() => setView("guide")}>
            <CircleHelp size={16} />
            Como executar o Occhio
            <ArrowRight size={14} />
          </button>
          <div className="profile">
            <span>OC</span>
            <div>
              <strong>Occhio Console</strong>
              <small>Projeto de sistemas · Tema 2</small>
            </div>
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
            Ambiente local
          </span>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <span className="eyebrow">OBSERVE. ENTENDA. ACOMPANHE.</span>
              <h1>
                {view === "overview"
                  ? "Seu sistema, em perspectiva."
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
                      : "Execute o ambiente e demonstre o fluxo completo do Tema 2."}
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
              m={m}
              h={h}
              samples={samples}
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
          {view === "pipeline" && <PipelinePage h={h} health={health} />}
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
