# dsh-demurrage-ledger — Verificação da integridade e da aritmética do registo de demoras e detenções de contentores

`dsh-demurrage-ledger` lê um registo de demoras e detenções de contentores (滞箱费台账) —o cabeçalho mais uma linha por contentor— e verifica a integridade e a aritmética desse mesmo registo: se cada linha regista pelo menos um número de contentor ou um conhecimento de embarque, se a data de início do período livre e a data de devolução são analisáveis e coerentes entre si, se os dias de excesso são iguais à diferença entre essas duas datas menos os dias livres, se o montante é igual aos dias de excesso × a tarifa, se a moeda está escrita como código de três letras, se não há números de contentor repetidos e se não resta nenhum marcador de modelo por substituir na observação. Os dias livres e a tarifa são lidos do próprio registo, cujas colunas podem ter nomes em chinês ou em inglês.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| Uma linha tem vazios tanto o número do contentor como o conhecimento de embarque. Isso é reportado? | Sim. `DL-001` exige que, em cada linha a que o registo dá pelo menos uma dessas duas colunas, esteja preenchido `containerNo` ou `blNo`, e reporta a linha quando ambos estão vazios. Verifica apenas que um dos dois está preenchido, não se o encargo deveria ter ocorrido. Se o registo não trouxer nenhuma das duas colunas, a regra indica-se a si própria em `skipped` em vez de passar em silêncio. |
| A data de início foi escrita como `15/03/2026` e a data de devolução é anterior. O que faz a regra? | `DL-002` analisa `startAt` e compara-o com `returnAt`: um valor que não consegue ler como data é reportado nessa linha em vez de ser omitido, e uma data de início posterior à de devolução também é reportada; o mesmo dia conta como não posterior. Compara apenas essas duas datas: qual a convenção de início aplicável (conhecimento de embarque, entrega ou chegada) fica para a tarifa do transportador e o contrato. |
| A coluna dos dias de excesso diz 10, mas as duas datas e o período livre dão 7. Isso é detetado? | Sim. `DL-003` recalcula os dias como `returnAt` − `startAt` − `freeDays` e reporta a linha quando o `overdueDays` declarado difere mais do que a `tolerance` configurada, 0 por omissão. Só corre em linhas com os quatro valores presentes e analisáveis; quando nenhuma linha os reúne, a regra reporta-se em `skipped`. A convenção de início e a inclusão de feriados no período livre continuam a ser do contrato: para uma base de dias úteis ou de horas, aumente a tolerância ou desative a regra. |
| O montante não é igual aos dias de excesso vezes a tarifa, e a minha tarifa é escalonada. Isso é reportado? | `DL-004` multiplica `overdueDays` × `rate` e reporta a linha quando `amount` difere mais do que a `tolerance`, 0,01 por omissão. Não julga se a tarifa é razoável nem se corresponde à do transportador. Uma tarifa escalonada não cabe numa única célula `rate`, pelo que esse registo reportará uma diferença: desative a regra, ou registe uma tarifa média e diga-o na observação. |
| A célula da moeda diz `美元`, ou `usd`. Isso é reportado? | Sim. `DL-005` reporta qualquer valor de `currency` que não corresponda ao padrão do pacote, `^[A-Z]{3}$` por omissão: três letras maiúsculas como `USD`. É apenas uma verificação de forma e não julga se essa moeda é a correta para a liquidação. A sua base é a única norma pública citada pelo pacote, e o seu excerpt regista que o texto do artigo não foi obtido, pelo que a regra fica em warn. Sem coluna de moeda, a regra indica-se em `skipped`. |
| O mesmo número de contentor aparece em duas linhas. É um registo duplicado? | `DL-006` reporta a linha quando um valor de `containerNo` se repete, comparando sem espaços, e indica a linha anterior com que coincide. Verifica apenas a unicidade, e um resultado exige confirmação humana: um contentor devolvido por etapas, ou liberto e novamente retido, pode legitimamente ocupar duas linhas — diga-o na observação em vez de apagar uma linha. Sem coluna `containerNo`, a regra reporta que não pôde ser executada em vez de passar em silêncio. |

## Normas que segue

| Documento | Número | Regras que o citam |
|---|---|---|
| 承运人运价本与运输合同（无国家标准） | 无统一标准（本条依据为台账可追溯性） | DL-001 |
| 承运人运价本与运输合同（无国家标准） | 无统一标准（本条依据为日期自洽） | DL-002 |
| 承运人运价本与运输合同（无国家标准） | 无统一标准（本条依据为算术自洽） | DL-003, DL-004 |
| 《表示货币的代码》 | GB/T 12406—2022（表示货币的代码；2022-12-30 发布并实施；全部代替 GB/T 12406—2008（该版名称为「表示货币和资金的代码」）——注意旧版名称含"资金"；修改采用 ISO 4217:2015，非等同采用；条号本次未取得） | DL-005 |
| 承运人运价本与运输合同（无国家标准） | 无统一标准（本条依据为台账唯一性） | DL-006 |
| 承运人运价本与运输合同（无国家标准） | 无统一标准（本条依据为台账真实性） | DL-007 |

**Boundary:** this plugin checks a **滞箱费台账** for arithmetic and completeness — that a container or bill of
lading is recorded, that the free-period start and the return date parse and follow each other, that the
overdue days equal the gap between those dates less the free days, that the charge equals days × rate, that
the currency follows its format, and that container numbers do not repeat. It does **not** decide who bears
the charge, whether a rate is reasonable, whether a waiver is available, or whether the amount is
recoverable. **Those depend on the contract, the allocation of responsibility and commercial negotiation.**

> ### ⚠️ There is no national standard for this, and the pack does not pretend otherwise
>
> Demurrage and detention are set by **each carrier's tariff and the contract of carriage** — free periods and
> rates differ between carriers, trades and container types, and **no unified national standard exists**. So
> this pack does **not** fabricate a standard number: every rule's `excerpt` states plainly that its basis is
> arithmetic self-consistency or ledger traceability and that **no citable clause exists**. The one exception
> is the currency format, whose home is GB/T 12406 (identical to ISO 4217), and that excerpt says the clause
> text was not obtained. A test asserts that every excerpt carries one of those admissions.
>
> **The plugin ships no carrier's free period and no rate.** Both come from the ledger. Two consequences are
> worth knowing before trusting a finding:
>
> - **Segmented rates break `DL-004`.** Tariffs commonly step up (one rate for days 1–7, a higher one from
>   day 8). A single `rate` column cannot express that, so a ledger priced in segments will report a
>   difference. Disable the rule, or record an average rate with a note that says so.
> - **`DL-003` does not choose the start convention.** Whether the clock starts at the bill of lading, at
>   release, or at arrival — and whether the free period includes holidays — is the contract's business. The
>   ledger's `起算日期` and `免箱期` are assumed to already follow it.

## Compatibility

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-demurrage-ledger
dsh --profile <name> --dump-config | grep 'dsh-demurrage-ledger'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/demurrage-ledger.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-demurrage-ledger
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-demurrage-ledger contributors.
