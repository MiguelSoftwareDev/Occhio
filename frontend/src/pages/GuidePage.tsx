import { useState } from "react";
const systems = {
  Windows: {
    python: ".\\.venv\\Scripts\\python.exe",
    create: "py -3.12 -m venv .venv",
    copy: "if (!(Test-Path .env)) { Copy-Item .env.example .env }",
    start: "powershell -ExecutionPolicy Bypass -File .\\scripts\\start.ps1",
    docker: "https://docs.docker.com/desktop/setup/install/windows-install/",
    note: "Instale Python 3.12, Docker Desktop e Ollama para Windows. Abra o Docker Desktop com containers Linux e o aplicativo Ollama. Reabra o terminal após a instalação para atualizar o PATH.",
  },
  macOS: {
    python: ".venv/bin/python",
    create: "python3.12 -m venv .venv",
    copy: "test -f .env || cp .env.example .env",
    start: "bash scripts/start.sh",
    docker: "https://docs.docker.com/desktop/setup/install/mac-install/",
    note: "Instale Python 3.12 e as versões de Docker Desktop e Ollama compatíveis com seu Mac (Apple Silicon ou Intel). Abra ambos os aplicativos antes de iniciar.",
  },
  Linux: {
    python: ".venv/bin/python",
    create: "python3.12 -m venv .venv",
    copy: "test -f .env || cp .env.example .env",
    start: "bash scripts/start.sh",
    docker: "https://docs.docker.com/engine/install/",
    note: "Instale Python 3.12 com suporte a venv, Docker Engine com o plugin Compose e Ollama seguindo as instruções da sua distribuição. Inicie o daemon Docker e o serviço Ollama; sem serviço, use ollama serve em outro terminal.",
  },
};
export function GuidePage() {
  const [os, setOS] = useState<keyof typeof systems>("Windows");
  const s = systems[os];
  return (
    <>
      <div className="os-tabs" aria-label="Sistema do coletor">
        {(Object.keys(systems) as (keyof typeof systems)[]).map((key) => (
          <button
            className="button secondary"
            aria-pressed={os === key}
            onClick={() => setOS(key)}
            key={key}
          >
            {key}
          </button>
        ))}
      </div>
      <div className="guide-grid">
        <section className="panel guide">
          <h2>Executar no {os}</h2>
          <p>{s.note}</p>
          <p>
            Execute os comandos na pasta Occhio. O ambiente virtual é chamado
            diretamente; não é preciso ativá-lo.
          </p>
          <p>
            <a href={s.docker} target="_blank" rel="noreferrer">
              Instalar Docker
            </a>{" "}
            ·{" "}
            <a
              href={`https://ollama.com/download/${os === "Windows" ? "windows" : os === "macOS" ? "mac" : "linux"}`}
              target="_blank"
              rel="noreferrer"
            >
              Instalar Ollama
            </a>
          </p>
          <h3>1. Preparar o Python</h3>
          <pre>{`${s.create}\n${s.python} -m pip install -r requirements.lock.txt\n${s.copy}`}</pre>
          <h3>2. Preparar o modelo e conferir o Docker</h3>
          <pre>
            {
              "ollama pull qwen3:1.7b\nollama list\ndocker version\ndocker compose version"
            }
          </pre>
          <p>
            Se você mudou OLLAMA_MODEL no .env, baixe esse modelo. O primeiro
            download precisa de internet.
          </p>
          <h3>3. Iniciar a pipeline completa</h3>
          <pre>{s.start}</pre>
          <p>
            O script inicia RabbitMQ, gera o contrato e abre API, gRPC e
            consumidor. Acesse{" "}
            <a href="http://127.0.0.1:8000">127.0.0.1:8000</a>. Na Pipeline,
            confira os quatro serviços; depois clique em Analisar agora.
          </p>
          <h3>Frontend a partir do Git</h3>
          <p>
            O ZIP inclui a interface compilada. Ao clonar ou modificar o
            frontend, instale Node.js 22 e execute:
          </p>
          <pre>{"cd frontend\nnpm ci\nnpm run build\ncd .."}</pre>
        </section>
        <section className="panel guide">
          <h2>Monitoramento e análise</h2>
          <p>
            CPU, memória, processos e discos atualizam sem IA. O botão solicita
            uma nova coleta e sua interpretação pelo modelo. No streaming, cada
            coleta é analisada em sequência.
          </p>
          <h3>Somente monitoramento</h3>
          <pre>{`${s.python} -m uvicorn backend.api.gateway:app --host 127.0.0.1 --port 8000`}</pre>
          <p>
            Esse modo dispensa Docker e Ollama, mas não habilita análise.
            Encerre-o com Ctrl+C antes de iniciar a pipeline completa, para
            liberar a porta 8000.
          </p>
          <h3>Diagnóstico</h3>
          <ul>
            <li>Docker não reconhecido: instale-o e reabra o terminal.</li>
            <li>
              Docker instalado, sem conexão: abra o Desktop ou inicie o daemon.
            </li>
            <li>Ollama sem modelo: confira ollama list e OLLAMA_MODEL.</li>
            <li>
              gRPC ausente: execute o script completo; Uvicorn sozinho não
              inicia gRPC.
            </li>
            <li>
              Resultado na fila: o consumidor precisa estar ativo para salvar no
              histórico.
            </li>
          </ul>
          <pre>
            {"docker compose ps\ndocker compose logs --tail 80 rabbitmq"}
          </pre>
          <h3>Encerrar</h3>
          <p>
            Ctrl+C encerra os processos Python. Para parar o RabbitMQ
            preservando os dados:
          </p>
          <pre>docker compose stop rabbitmq</pre>
          <p>
            O coletor observa onde o Python executa. Em WSL, container ou VM,
            discos e processos pertencem a esse ambiente, não necessariamente ao
            computador hospedeiro.
          </p>
        </section>
      </div>
    </>
  );
}
