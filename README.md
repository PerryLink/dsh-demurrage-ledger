# dsh-demurrage-ledger — Demurrage and detention ledger completeness and arithmetic check

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-demurrage-ledger` reads one demurrage and detention ledger (滞箱费台账) — the header plus one row per container — and checks that ledger's own completeness and arithmetic: that each row records at least a container number or a bill of lading, that the free-period start and the return date parse and follow each other, that the overdue days equal the gap between those two dates less the free days, that the charge equals the overdue days × the rate, that the currency is written as a three-letter code, that no container number is repeated, and that no unreplaced template placeholder survives in the remark. The free days and the rate are read from the ledger itself, whose columns may be named in Chinese or in English.

## What it looks like

![Terminal demo of dsh-demurrage-ledger: real output over its DL-002 fixture](https://raw.githubusercontent.com/PerryLink/dsh-demurrage-ledger/main/docs/assets/dsh-demurrage-ledger-demo.png)

Real output from this plugin over its own `DL-002` test fixture — not a mock-up. The rule pack ships no invented quotations, so a finding names both the clause it applied and the fact that the clause text was not obtained.

## What it answers

| You ask | What it answers |
|---|---|
| A row has both the container number and the bill of lading blank. Will the check say anything? | Yes. `DL-001` requires `containerNo` or `blNo` to be filled on every row the ledger gives at least one of those two columns, and reports the row when both are empty. It checks only that one of them is filled, not whether the charge should have arisen. A ledger carrying neither column makes the rule list itself in `skipped` rather than passing silently. |
| The start date was typed as `15/03/2026` and the return date falls before it. What does the rule do? | `DL-002` parses `startAt` and compares it with `returnAt`: a value it cannot read as a date is reported on that row rather than passed over, and a start date later than the return date is reported too — the same day counts as not later. It compares those two dates only; which start convention applies (bill of lading, release or arrival) is left to the carrier's tariff and the contract. |
| The overdue days column says 10, but the two dates and the free period give 7. Is that caught? | Yes. `DL-003` recomputes the days as `returnAt` − `startAt` − `freeDays` and reports the row when the declared `overdueDays` differ by more than the configured `tolerance`, which is 0 by default. It runs only on rows where all four values are present and parse; when no row carries all four, the rule reports itself in `skipped`. The start convention and whether the free period counts holidays stay with the contract — for a working-day or hourly basis, raise the tolerance or disable the rule. |
| The charge does not equal the overdue days times the rate — and my tariff steps up after the first week. | `DL-004` multiplies `overdueDays` × `rate` and reports the row when `amount` differs by more than the `tolerance`, 0.01 by default. It does not judge whether the rate is reasonable or whether it matches the tariff. A stepped tariff cannot be expressed in one `rate` cell, so such a ledger will report a difference: disable the rule, or record an average rate and say so in the remark. |
| The currency cell says `美元`, or `usd`. Is that reported? | Yes. `DL-005` reports any `currency` value that does not match the pack's pattern, `^[A-Z]{3}$` by default — three upper-case letters such as `USD`. It is a form check only and does not judge whether that currency is the right one for the settlement. Its basis is the one public standard the pack cites, and its excerpt records that the clause text was not obtained, so the rule stays at warn. A ledger with no currency column makes the rule report itself in `skipped`. |
| The same container number appears on two rows. Is that a duplicate entry? | `DL-006` reports the row when a `containerNo` value repeats, comparing with whitespace ignored, and names the earlier row it matches. It checks uniqueness only, and a hit needs human confirmation: a box returned in stages, or released and then detained again, can legitimately take two rows — say so in the remark rather than deleting a row. With no `containerNo` column the rule reports that it could not run instead of passing silently. |

## Standards it follows

| Document | Number | Cited by rules |
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

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for a month's ledger use `ptc` |

## What it does

Registers the `demurrage_ledger` tool. It reads one ledger — rows keyed by the ledger's own column names, in
Chinese or English — applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis |
|---|---|---|---|
| `DL-001` | a container or bill of lading is recorded | warn | ledger traceability |
| `DL-002` | the start and return dates parse and follow each other | warn | date consistency |
| `DL-003` | overdue days match the dates and the free period | warn | arithmetic |
| `DL-004` | the charge equals overdue days × rate | warn | arithmetic |
| `DL-005` | the currency is a three-letter code | warn | GB/T 12406 |
| `DL-006` | container numbers are unique in the ledger | warn | ledger uniqueness |
| `DL-007` | the remark column holds no unreplaced placeholder | warn | ledger integrity |

## Install

```sh
dsh plugin --profile <name> add dsh-demurrage-ledger
dsh --profile <name> --dump-config | grep 'dsh-demurrage-ledger'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/demurrage-ledger.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `DL-003` `daysField` / `fromField` / `toField` / `subtractField` / `tolerance` — the day arithmetic. Raise
  `tolerance` if the ledger rounds, or disable the rule for a working-day or hourly basis.
- `DL-004` `resultField` / `factorFields` / `tolerance` — the charge arithmetic, tolerance `0.01` by default.
- `DL-005` `pattern` — the currency shape; three upper-case letters by default.
- `DL-007` `terms` — the placeholders to look for.

## Material format

The tool accepts JSON or YAML:

```yaml
carrier: 某某船务
blNo: MSCUAA123456
rows:
  - { 箱号: MSCU1234567, 提单号: MSCUAA123456, 免箱期: '7', 起算日期: 2026-03-01,
      还箱日期: 2026-03-15, 超期天数: '7', 费率: '120', 滞箱费金额: '840', 币制: USD,
      备注: 按运价本分段计费，此为平均费率 }
```

Column names are matched case-insensitively and ignoring spaces, underscores and hyphens; the ledger's own
column names are kept, so a finding names the column it read. Dates may be `2026-03-01` or
`2026-03-01 14:00`, and numeric cells may carry units and thousands separators.

## Rule sources

Rule data lives in `rules/demurrage-ledger.yaml`. Because no national standard governs demurrage, the pack's
`basis` entries say so explicitly instead of citing one; the only external reference is the currency-code
standard, whose excerpt admits the clause text was not obtained. The load-time guard still requires every
rule to carry a document, a clause, an excerpt and a source, and still forbids a `derived-from-principle` or
locally configured check from being `error`.

## Troubleshooting

- **`DL-003` fires on a ledger I computed by hand.** Check the start convention and whether the free period
  includes holidays. The finding shows the two dates and the free days it used, so the sum can be redone.
- **`DL-004` fires on a segmented tariff.** A single rate cannot express a stepped tariff. Disable the rule,
  or record an average rate and say so in the remark.
- **`DL-005` fires on `USD `.** The default pattern accepts exactly three upper-case letters; a trailing
  space or a lower-case code fails. Normalise the export.
- **`DL-006` fires twice on one container.** That can be legitimate — a container returned in stages, or
  re-detained after release. Say so in the remark rather than deleting a row.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`; if
  your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-demurrage-ledger@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, the shared table-plugin suite plus paired fixtures
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-demurrage-ledger   # refresh src/shared from ../_shared
```

The plugin is **data-only**: `src/model.ts` declares the table shape, the shared kit supplies the reader and
the check engine, and the rule pack declares every check.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-demurrage-ledger contributors.
