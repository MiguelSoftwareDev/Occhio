# Requisitos técnicos

Contrato funcional do projeto de desenvolvimento e teste.

| Exigência | Implementação | Como comprovar |
| --- | --- | --- |
| Ollama 100% local, modelo aberto | Ollama em loopback; padrão qwen3:1.7b; sem fallback externo | `ollama list`, configuração e execução após desconectar a rede |
| Dados reais de sistema | psutil: CPU, memória, disco, quantidade de processos e uptime | Painel ao vivo e `GET /api/metrics` |
| Análise em texto | Prompt versionado, resposta do modelo exibida sem HTML | Análise única e exportação JSON |
| Comunicação coletor–analisador via gRPC | API/coletor chama servidor gRPC separado | `services/analysis_server.py` e contrato |
| Pelo menos um método unário | AnalyzeSnapshot | POST /api/analyze/once (unário); a interface usa AnalyzeProgress para acompanhar etapas |
| Pelo menos um método de streaming | StreamSnapshots bidirecional | Streaming com resultados progressivos |
| Publicar resultados em fila/tópico | RabbitMQ topic exchange, fila durável e publisher confirms | Console do broker e IDs publicados |
| Consumir em outro processo | `backend.services.consumer` separado | Terminais/PIDs e histórico persistido |
| Demonstrar fluxo ponta a ponta | `scripts/verify_e2e.py` | Executar com serviços reais e salvar evidence/e2e.json |

O código cobre os itens técnicos. A comprovação real exige executar o modelo e o broker no ambiente da equipe; testes com substitutos não substituem essa demonstração.

