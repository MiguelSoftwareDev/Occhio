# Matriz de atendimento — Tema 2

Fonte: PDF de Avaliação A3 2026-2 enviado com o projeto, seção “Tema 2”.

| Exigência | Implementação | Como comprovar |
| --- | --- | --- |
| Ollama 100% local, modelo aberto | Ollama em loopback; padrão qwen3:1.7b; sem fallback externo | `ollama list`, configuração e execução após desconectar a rede |
| Dados reais de sistema | psutil: CPU, memória, disco, quantidade de processos e uptime | Painel ao vivo e `GET /api/metrics` |
| Análise em texto | Prompt versionado, resposta do modelo exibida sem HTML | Análise única e exportação JSON |
| Comunicação coletor–analisador via gRPC | API/coletor chama servidor gRPC separado | `services/analysis_server.py` e contrato |
| Pelo menos um método unário | AnalyzeSnapshot | Botão Análise única |
| Pelo menos um método de streaming | StreamSnapshots bidirecional | Streaming com resultados progressivos |
| Publicar resultados em fila/tópico | RabbitMQ topic exchange, fila durável e publisher confirms | Console do broker e IDs publicados |
| Consumir em outro processo | `backend.services.consumer` separado | Terminais/PIDs e histórico persistido |
| Demonstrar fluxo ponta a ponta | `scripts/verify_e2e.py` + roteiro | Executar com serviços reais e salvar evidence/e2e.json |

O código cobre os itens técnicos. A comprovação real exige executar o modelo e o broker no ambiente da equipe; testes com substitutos não substituem essa demonstração.

## Entregas gerais do enunciado

Além do software, o professor pede artigo/relatório, roteiro de implementação/instalação, slides, configurações e registro do prompt/modelo. Também pede nomes e matrículas dos componentes e apresentação presencial de 20 minutos. O prazo indicado para documentação é **25/11/2026**; conferir a divisão de apresentações da turma com o professor.

A pasta docs fornece roteiro e base estrutural, mas não inventa integrantes, matrículas, medições ou conclusões experimentais. O artigo e os slides finais devem incorporar a execução real da equipe. Veja ENTREGA_ACADEMICA.md.
