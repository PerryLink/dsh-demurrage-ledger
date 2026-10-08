# dsh-demurrage-ledger — 滞箱费台账核对

`dsh-demurrage-ledger` 读取一份滞箱费台账（表头加每个集装箱一行），核对这份台账自身的齐备与算术：每行是否至少填写了箱号或提单号、免箱期起算日与还箱日期是否可解析且先后成立、超期天数是否等于两个日期之差减去免箱期、金额是否等于超期天数乘以费率、币制是否写成三位字母代码、箱号是否重复、备注栏是否残留未替换的模板占位符。免箱期与费率一律取自台账本身，台账的列名可以是中文，也可以是英文。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 某行的箱号与提单号都是空的，会被报出来吗？ | 会。`DL-001` 对台账给了 `containerNo`、`blNo` 这两栏之一的每一行，要求至少填写其中一项，两项都空即报出该行。它只核对是否填写，不判断这笔费用是否应当发生。台账两栏都没有时，本条会在 `skipped` 中列出自己，而不是静默通过。 |
| 起算日期写成了 `15/03/2026`，而还箱日期比它还早，会怎么处理？ | `DL-002` 解析 `startAt` 并与 `returnAt` 比较：读不出日期的值会逐行报出，而不是略过；起算日期晚于还箱日期也会报出，同一天视为不晚于。它只比较这两个日期，起算日按提单日、放箱日还是到港日，取决于承运人运价本与合同，不由它选定。 |
| 超期天数栏写着 10，但两个日期与免箱期算出来是 7，能查出来吗？ | 能。`DL-003` 按 `returnAt` − `startAt` − `freeDays` 重算，与填报的 `overdueDays` 之差超过配置的 `tolerance`（出厂为 0）即报出该行。只有四个值都填写且可解析的行才执行；没有这样的行时，本条在 `skipped` 中说明自己未执行。起算口径与免箱期是否含节假日仍由合同决定——按工作日或按小时计费时，请调大容差或停用本条。 |
| 金额不等于超期天数乘以费率，而且我的费率是分段递增的。 | `DL-004` 按 `overdueDays` × `rate` 重算，与 `amount` 之差超过 `tolerance`（出厂为 0.01）即报出该行。它不判断费率是否合理、是否与运价本一致。分段费率无法用一个 `rate` 栏表达，这类台账会被报出差异：请停用本条，或改为填写平均费率并在备注中说明。 |
| 币制栏写的是 `美元`，或者 `usd`。 | 会报出。`DL-005` 对不符合规则库 pattern 的 `currency` 值逐行报出，出厂 pattern 为 `^[A-Z]{3}$`，即 `USD` 这样的三位大写字母。它只是形式核对，不判断该币制选择是否正确。本条依据的是规则库唯一引用的公开标准，其 excerpt 如实写明条文本次未取得，故封顶 warn。台账没有币制栏时，本条会在 `skipped` 中列出自己。 |
| 同一个箱号在两行里各出现一次，算重复登记吗？ | `DL-006` 会对重复的 `containerNo` 报出该行，并指出它与哪一行重复，比较时忽略空白字符。它只核对唯一性，命中需人工确认：同一箱分批还箱、或先滞箱后退箱再滞箱，确实可能产生两行——请在备注栏说明，而不是简单删除。台账没有 `containerNo` 栏时，本条报告无法执行，而不是静默通过。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-demurrage-ledger
dsh --profile <name> --dump-config | grep 'dsh-demurrage-ledger'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/demurrage-ledger.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-demurrage-ledger
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-demurrage-ledger contributors.
