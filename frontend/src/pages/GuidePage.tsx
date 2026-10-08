import { ArrowRight } from "lucide-react";

export function GuidePage() {
  return (
    <div className="guide-grid">
      <section className="panel guide">
        <h2>Comece pelo ambiente local</h2>
        <p>
          O backend coleta o computador em que está rodando. Em uma VM, as
          métricas pertencem à VM.
        </p>
        {[
          {
            n: "01",
            title: "Prepare as dependências",
            text: "Python 3.12, Docker e Ollama. O frontend compilado já acompanha o projeto.",
            code: "python -m venv .venv\n# Ative o ambiente virtual\npip install -r requirements.lock.txt",
          },
          {
            n: "02",
            title: "Instale o modelo e inicie o broker",
            text: "Copie .env.example para .env. O download do modelo exige internet; a inferência roda localmente.",
            code: "ollama pull qwen3:1.7b\ndocker compose up -d rabbitmq",
          },
          {
            n: "03",
            title: "Inicie o console",
            text: "Mantenha o Ollama em execução. Este comando inicia gRPC, consumidor e API em processos distintos.",
            code: "python -m backend.generate_proto\npython backend/run_all.py",
          },
        ].map((step) => (
          <article className="guide-step" key={step.n}>
            <span>{step.n}</span>
            <div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
              <pre>{step.code}</pre>
            </div>
          </article>
        ))}
      </section>
      <section className="panel guide">
        <span className="eyebrow">DEMONSTRAÇÃO · TEMA 2</span>
        <h2>O que mostrar ao professor</h2>
        <ol>
          <li>Métricas reais do sistema variando.</li>
          <li>Análise unária feita pelo Ollama local.</li>
          <li>Streaming com múltiplas coletas e respostas.</li>
          <li>Publicação no RabbitMQ e consumo em outro processo.</li>
          <li>Histórico persistido e evidência exportada.</li>
        </ol>
        <div className="notice">
          A análise é uma interpretação das métricas, não uma prova da causa de
          lentidão. Confira as hipóteses do modelo.
        </div>
        <p>
          Consulte <code>docs/DEMONSTRACAO.md</code> para o roteiro e{" "}
          <code>docs/REQUISITOS.md</code> para a matriz de atendimento.
        </p>
        <a
          className="text-button"
          href="/openapi.json"
          target="_blank"
          rel="noreferrer"
        >
          Contrato da API (JSON)
          <ArrowRight size={15} />
        </a>
      </section>
    </div>
  );
}
