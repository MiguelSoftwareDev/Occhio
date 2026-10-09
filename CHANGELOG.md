# Alterações

## 2.0.0

- Console redesenhado em React + TypeScript, com layout responsivo, gráfico de sessão, histórico paginado, detalhes, exportação e diagnóstico de serviços.
- Backend separado em API, domínio, serviços, infraestrutura e configuração.
- Correção da interpretação do retorno de `basic_publish`: publisher confirms reportam falhas por exceção; retorno vazio não indica rejeição.
- Publicação com roteamento obrigatório, mensagens persistentes e identificação do evento.
- Consumidor com reconexão, validação, dead-letter e ACK depois do commit.
- Gravação idempotente por ID, timestamp de consumo, índice e WAL no SQLite.
- Preservação de zeros no JSON de resultados Protobuf.
- Streaming gRPC repassado incrementalmente ao navegador via NDJSON.
- Validação das métricas, limite de chamadas concorrentes, controles locais de Host/Origin e renderização textual da análise.
- Testes automatizados, CI, locks, verificador ponta a ponta e documentação de requisitos/demonstração.

## Compatibilidade

O endpoint `/api/history` retorna `{items, total, offset, limit}`. O endpoint de streaming retorna NDJSON incremental. A fila nova é `analysis.results.v2`; mensagens antigas não são migradas. O servidor e o cliente devem regenerar o contrato `.proto` ao atualizar. A entrega não inclui banco de dados nem evidências de inferência real.

## Pixel interface update

- Added the light pixel-art console, compact analysis action, process search/sorting and responsive internal scrolling.
- Added native application icon extraction with opaque IDs, bounded concurrency and no remote logo lookup.
- Added dynamic runtime/host information and interval-based per-process CPU/RSS measurements.
- Added generated walking/typing sprites and five station assets, with a separate movement path and reduced-motion support.
- Added `AnalyzeProgress` and the live HTTP endpoint; progress advances only on confirmed operations and storage consumption.
- Preserved unary and bidirectional streaming, analysis history and exports.
- Added failure-path, progress, runtime and process tests; updated documentation and built assets.
