# Demonstração do Tema 2 — 20 minutos

## Antes da aula

1. Instale dependências e modelo; execute uma análise para aquecer o Ollama.
2. Confirme os quatro serviços na aba Pipeline.
3. Rode `python scripts/verify_e2e.py` e guarde o JSON gerado com resultados reais.
4. Teste sem internet após baixar tudo; o caminho de inferência continua local.
5. Registre hardware, SO, versão do modelo (`ollama list`) e horários. Não use números deste roteiro como medições.

## Roteiro

| Minutos | Mostrar | Evidência |
| --- | --- | --- |
| 0–3 | Problema, escopo e relação com SO | CPU, memória, processos e comunicação entre processos |
| 3–6 | Arquitetura lógica/física e contrato | `.proto`, unary e streaming bidirecional |
| 6–9 | Métricas reais e análise única | Texto retornado pelo Ollama e ID publicado |
| 9–12 | Streaming com 2–3 coletas | Resultados progressivos e IDs diferentes |
| 12–15 | Consumidor parado e reiniciado | Fila acumulando e histórico recebendo depois |
| 15–18 | Testes, falhas e persistência | Exportação JSON; reiniciar API mantém histórico |
| 18–20 | Resultados, limites e próximos passos | Medições reais e conclusões da equipe |

## Prova do transporte assíncrono

Use os três terminais separados descritos em INSTALACAO.md, em vez de `run_all.py`, que encerra o conjunto se um filho termina.

1. Pare apenas o terminal do consumidor com Ctrl+C.
2. Na visão geral, execute uma análise única. O botão permite publicação quando o consumidor está parado.
3. Observe “Publicada · aguardando consumo”, consumidor indisponível e mensagem na fila.
4. Reinicie `python -m backend.services.consumer`.
5. Observe “Consumo confirmado”, fila drenada e análise no histórico.
6. Mostre o mesmo `analysis_id` no log e no JSON exportado.

## Falhas controladas

- Pare Ollama: nenhuma análise falsa deve aparecer; a interface sinaliza indisponibilidade.
- Pare RabbitMQ: não deve ser reportada publicação bem-sucedida.
- Reinicie o broker: o consumidor tenta reconectar automaticamente.
- Cancele um streaming: os resultados já publicados permanecem disponíveis.

Não gere carga que comprometa a máquina. Abrir uma aplicação comum já permite observar variação. Uma diferença de uso não comprova qual processo causou o pico.

## Resultados para o artigo

Meça pelo menos três execuções unárias e um streaming. Registre CPU/memória, duração de inferência (`inference_ms`), modelo, conteúdo da análise e horários de coleta/análise/consumo. Separe a primeira execução (aquecimento) das seguintes. Discuta limitações de uma amostra única, erro do modelo e dependência do hardware.
