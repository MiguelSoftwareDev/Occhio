# Instalação e operação

## Pré-requisitos

- Python 3.12, Docker com Compose v2 e Ollama local.
- Modelo aberto padrão: `qwen3:1.7b`. O uso de RAM e a latência variam com o hardware; teste antes da apresentação. Não há requisito de GPU no código.
- Node 22 apenas para compilar/modificar React. A entrega ZIP inclui o build.
- Internet para a preparação. A inferência usa `127.0.0.1` sem proxy e sem seguir redirecionamentos.

## Windows: comandos manuais

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
ollama pull qwen3:1.7b
docker compose up -d --wait rabbitmq
.\.venv\Scripts\python.exe -m backend.generate_proto
.\.venv\Scripts\python.exe backend/run_all.py
```

Não sobrescreva `.env` se já o configurou. Abra `http://127.0.0.1:8000`. `Ctrl+C` encerra os processos Python; RabbitMQ e Ollama continuam disponíveis. Para parar o broker: `docker compose stop rabbitmq`. Evite `down -v` se deseja preservar as mensagens.

## Execução em terminais separados

Útil para comprovar ao professor que há processos independentes. Ative `.venv` e execute cada comando em um terminal, todos na raiz:

```bash
python -m backend.services.analysis_server
python -m backend.services.consumer
python -m uvicorn backend.api.gateway:app --host 127.0.0.1 --port 8000
```

O coletor é executado no processo da API; a chamada para o serviço de análise passa obrigatoriamente por gRPC. Não use `run_all.py` simultaneamente com esses terminais.

## Configuração

| Variável | Padrão | Função |
| --- | --- | --- |
| OLLAMA_URL | http://127.0.0.1:11434 | Serviço local; hosts externos são rejeitados |
| OLLAMA_MODEL | qwen3:1.7b | Modelo instalado pelo `ollama pull` |
| GRPC_ADDRESS | 127.0.0.1:50051 | Endereço do serviço gRPC |
| RABBITMQ_URL | amqp://occhio:occhio_demo@127.0.0.1:5672/ | Credencial local de demonstração |
| DATABASE_PATH | data/occhio.db | SQLite relativo à raiz |
| ANALYSIS_TIMEOUT_SECONDS | 120 | Timeout por inferência, permitido entre 5 e 600 |

A credencial do Compose é exclusivamente para demonstração local. Mudar `.env` não altera um usuário RabbitMQ já criado no volume. Altere a senha no broker e atualize a URL em conjunto se necessário. A aplicação usa a fila `analysis.results.v2`, separada da fila da versão anterior; não migra mensagens antigas automaticamente.

## Problemas comuns

| Sintoma | Verificação |
| --- | --- |
| Ollama indisponível | Execute `ollama list` e `ollama serve`; confira a porta 11434 |
| Modelo ausente | Execute `ollama pull qwen3:1.7b` e confira o nome em `.env` |
| Timeout de análise | Faça uma primeira inferência antes da aula; aumente o timeout até 600 se necessário |
| gRPC indisponível | Gere o contrato e inicie o servidor; confira conflitos na porta 50051 |
| RabbitMQ indisponível | `docker compose ps` e `docker compose logs rabbitmq` |
| Publicada, sem consumo | Inicie `backend.services.consumer`; confira permissões do diretório data |
| Fila de falhas > 0 | Abra o RabbitMQ em http://127.0.0.1:15672 e inspecione `analysis.failed.v2` |
| Frontend não compilado | Na pasta frontend, execute `npm ci` e `npm run build`; reinicie a API |
| Build ausente ao clonar Git | `frontend/dist` não é versionado; compile uma vez |
| Contrato incompatível | Reinstale o lock e rode `python -m backend.generate_proto` |

## Atualizar dependências

`requirements.txt` descreve intervalos diretos; o lock representa o ambiente testado. Após atualizar, rode build, testes e verificação real antes de renovar o lock. O lock usa o servidor HTTP básico do Uvicorn, sem dependências opcionais específicas do Unix.
