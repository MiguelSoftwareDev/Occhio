# Decisões de engenharia

## 01 — React + TypeScript e Vite

Console com estados assíncronos, cancelamento, streaming e detalhes. Tipagem entre componentes reduz inconsistências e Vite gera assets estáticos servidos pela API. Sem framework de servidor JavaScript: a aplicação não precisa de SEO nem de um servidor JavaScript adicional. CSS próprio e ícones Lucide; sem fontes externas ou dados demonstrativos embutidos.

## 02 — Backend no host

Ollama e Python executam no host para que `psutil` represente o computador monitorado. Apenas RabbitMQ fica em container. Containerizar o coletor sem explicar seu escopo poderia apresentar métricas de outro ambiente como se fossem do host.

## 03 — Camadas pequenas

Domínio para validação, serviços para o fluxo, infraestrutura para integrações e API para transporte HTTP. Funções diretas com comentários curtos português/inglês. Evita um framework de abstrações e mantém o caminho do dado legível para apresentação.

## 04 — RabbitMQ e SQLite

RabbitMQ torna o desacoplamento observável ao parar e reiniciar o consumidor. SQLite mantém instalação simples e permite transações/deduplicação. Um consumidor e volume local bastam para o escopo. Não é arquitetura de alta disponibilidade, nem benchmark de escala.

## 05 — Confirmações separadas

A resposta gRPC significa que o broker confirmou a publicação. O frontend consulta o ID até o consumidor gravar. Isso evita mostrar sucesso de persistência antes do commit.

## 06 — Streaming com processamento sequencial

O contrato é bidirecional; cada snapshot produz uma análise. O servidor processa a sequência sem paralelizar inferências de um mesmo stream. O navegador recebe NDJSON incremental. O tamanho de cada fluxo é limitado para evitar sobrecarga acidental.

## 07 — Limites explícitos

Sem autenticação pública, outbox, expurgo, múltiplos hosts ou execução de comandos sugeridos pelo LLM. Recomendações do modelo são texto. Evoluções possíveis devem ser guiadas por uma necessidade demonstrada, não pelo número de tecnologias no repositório.
