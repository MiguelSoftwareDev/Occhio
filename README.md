# Occhio

**Observabilidade local com análise de sistemas por IA.**

Occhio coleta CPU, memória, disco e processos reais do computador, envia os dados por gRPC para um serviço de análise com Ollama e publica a resposta no RabbitMQ. Um consumidor independente grava os resultados no SQLite. O console apresenta métricas, histórico e a situação de cada serviço.

Projeto acadêmico de Organização de Computadores e Sistemas Operacionais — **Tema 2**.

![Console Occhio](docs/images/console-desktop.png)

## Iniciar no Windows

Requisitos: Python 3.12, Docker Desktop em execução e Ollama instalado. Para editar o frontend, Node.js 22. O ZIP inclui `frontend/dist`, portanto Node não é necessário apenas para executar a entrega.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
Copy-Item .env.example .env
ollama pull qwen3:1.7b
.\scripts\start.ps1
```

Abra **http://127.0.0.1:8000**. Se o Ollama não iniciar automaticamente, execute `ollama serve` em outro terminal. Caso a política do PowerShell bloqueie o script, use os comandos manuais de [instalação](docs/INSTALACAO.md); não é necessário alterar políticas do computador.

## Iniciar no Linux/macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
cp .env.example .env
ollama pull qwen3:1.7b
./scripts/start.sh # Linux ou Mac
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1 # Windows pra poder rordar 
.\scripts\start.ps1 #Comando do Windows
```

## Arquitetura

- `frontend/src`: React + TypeScript, componentes, hooks e cliente HTTP.
- `backend/api`: endpoints HTTP e ponte incremental NDJSON → navegador.
- `backend/domain`: modelos validados e conversões Protobuf.
- `backend/services`: coleta, servidor gRPC e consumidor independente.
- `backend/infrastructure`: Ollama, RabbitMQ e SQLite.
- `backend/core`: configuração por ambiente.
- `proto`: contrato versionado com unary e streaming bidirecional.
- `tests`: regras, persistência, API, mensageria e transporte gRPC.
- `scripts`: inicialização e verificação ponta a ponta.
- `docs`: arquitetura, decisões, instalação, demonstração e matriz do enunciado.

A API/coletor, o servidor gRPC e o consumidor são processos distintos. Ollama roda no host; apenas o RabbitMQ usa Docker. Assim, `psutil` mede o host em que o Python é executado, não um container da aplicação.

## Confiabilidade

Publicação durável com publisher confirms e roteamento obrigatório; ACK somente depois da gravação; deduplicação por `analysis_id`; reconexão do consumidor com espera progressiva; fila de falhas para eventos inválidos; validação de métricas; limites de concorrência; deadlines; confirmação de consumo separada da confirmação de publicação.

Não há promessa de entrega exatamente uma vez: a fila permite reentrega e o banco evita registros duplicados. Se a resposta da publicação se perder, seu estado pode ser ambíguo. Não há retentativa automática da solicitação de IA.

## Verificação

```bash
pip install -r requirements-dev.txt
python -m backend.generate_proto
ruff check backend tests scripts
pytest -q
python scripts/verify_e2e.py
```

O último comando **exige os serviços reais ativos** e salva evidências em `evidence/e2e.json`. Os testes automatizados comuns isolam Ollama e RabbitMQ; exercitam o transporte gRPC real em loopback. Consulte [o relatório de validação](docs/VALIDACAO.md) para distinguir o que foi executado do que depende do seu ambiente.

## Desenvolvimento do frontend

```bash
cd frontend
npm ci
npm run dev
# ou gerar a versão servida pelo backend:
npm run build
```

O Vite encaminha `/api` ao backend em `127.0.0.1:8000`. Reinicie o backend após o primeiro build. O arquivo `package-lock.json` fixa a árvore JavaScript; `requirements.lock.txt` fixa as dependências Python testadas.

## Documentação

- [Instalação e solução de problemas](docs/INSTALACAO.md)
- [Arquitetura e garantias](docs/ARCHITECTURE.md)
- [Roteiro de demonstração](docs/DEMONSTRACAO.md)
- [Requisitos do Tema 2](docs/REQUISITOS.md)
- [Decisões de engenharia](docs/DECISOES.md)
- [Validação da entrega](docs/VALIDACAO.md)
- [Estrutura do artigo e apresentação](docs/ENTREGA_ACADEMICA.md)

## Escopo e limites

Aplicação local para estudo e demonstração: sem autenticação multiusuário, TLS ou exposição pública. Portas vinculadas ao loopback. O modelo analisa uma coleta por vez e não determina causalidade. Tendências do gráfico são mantidas apenas durante a sessão; análises consumidas permanecem no SQLite. O histórico não possui expurgo automático.

Download de dependências/modelo exige rede. Depois da preparação, a análise usa Ollama local. Não publique `.env`, `data/` ou evidências com informações do seu host sem revisá-las.
