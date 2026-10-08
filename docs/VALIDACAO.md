# Validação da entrega

Verificação realizada em ambiente Linux com Python 3.12. A data de referência da revisão é 08/10/2026.

## Executado

| Verificação | Resultado | Escopo |
| --- | --- | --- |
| Pytest | 19 testes aprovados | Coletor, validação, SQLite, consumidor, publicador, API e gRPC |
| Ruff | Aprovado | Código Python, testes e scripts |
| TypeScript | Aprovado | Tipagem estrita do frontend |
| Prettier | Aprovado | Formatação do código frontend |
| Build Vite | Aprovado | Assets de produção incluídos no ZIP |
| Navegador Chromium | Sem erro JavaScript nos cenários executados | Navegação e interface |
| Layout | Sem overflow horizontal nas telas verificadas | Visão geral, histórico, pipeline e guia em 390, 768 e 1440 px |
| Interações com respostas controladas | Aprovado | Análise única, estado consumido, modal/Escape, exportação JSON, streaming, histórico e erro HTTP |
| Métricas ao vivo | Aprovado | Coleta psutil no ambiente de execução; screenshots em docs/images |

Os testes de transporte abrem um servidor gRPC real em uma porta loopback e exercitam chamadas unárias e streaming. Ollama e publicação AMQP são substituídos por implementações de teste nesses casos. Os testes de interface usam respostas controladas, claramente separadas do produto; o aplicativo entregue não tem modo de dados fictícios.

O pytest emitiu um aviso de depreciação do adaptador TestClient da dependência Starlette em relação ao httpx; não houve falha. Uma atualização futura dessas dependências deve repetir a suíte.

## Não executado neste ambiente

- Inferência no Ollama com o modelo qwen3:1.7b.
- Comunicação com um RabbitMQ real e persistência após consumo real.
- Teste completo de queda/retorno do broker.
- Instalação e execução no Windows ou no computador da equipe.
- Benchmark de desempenho, carga, segurança ou alta disponibilidade.

Ollama e Docker não estavam instalados no ambiente desta revisão. Portanto, os testes aprovados não constituem prova do fluxo real ponta a ponta nem permitem afirmar que a aplicação está homologada para produção.

## Verificação obrigatória antes de apresentar

Execute os serviços no seu computador e rode:

```bash
python scripts/verify_e2e.py
```

O verificador exige prontidão dos serviços, executa uma análise unária e duas de streaming, espera a gravação de cada ID pelo consumidor e só então salva `evidence/e2e.json` com status `passed`. Em falha, retorna código diferente de zero. Use também o experimento de consumidor parado descrito em DEMONSTRACAO.md.

Os screenshots entregues mostram o console com métricas reais do ambiente de teste e serviços de inferência/mensageria indisponíveis. Não representam uma execução bem-sucedida do Ollama.
