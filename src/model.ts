/**
 * dsh-demurrage-ledger — table shape and material contract.
 *
 * The plugin is data-only: this file declares which columns the material may use
 * and how they map onto canonical field names; the shared kit supplies the reader
 * and the check engine, and the rule pack declares every check. Adding a check
 * that fits an existing kind is a rule-pack edit, not a code change.
 */

import { canonicaliseRow, parseTable, type TableSpec } from './shared/table.ts'
import { runTableCheck, type TableCheckOptions, type TableInput } from './shared/rows.ts'
import type { Ruleset } from './shared/rules.ts'

/** Tool id exposed to the model, and the row id in `cordis.patch.yml`. */
export const TOOL_NAME = 'demurrage_ledger'

/** The register's column aliases, declared once so both the spec and the guard see them. */
const COLUMNS = {
  containerNo: ['箱号', '集装箱号', 'containerNo', 'container'],
  blNo: ['提单号', '提运单号', '运单号', 'blNo'],
  sealNo: ['封号', '铅封号', 'sealNo'],
  size: ['箱型', '尺寸', 'size'],
  freeDays: ['免箱期', '免用期天数', '免费天数', 'freeDays'],
  startAt: ['起算日期', '免箱期起算日', '免费起算日', 'startAt'],
  returnAt: ['还箱日期', '还箱时间', 'returnAt'],
  overdueDays: ['超期天数', '滞箱天数', 'overdueDays'],
  rate: ['费率', '滞箱费率', '标准', 'rate'],
  amount: ['滞箱费金额', '金额', '费用', 'amount'],
  currency: ['币制', '币种', 'currency'],
  invoicedAt: ['开票日期', '账单日期', 'invoicedAt'],
  status: ['处理状态', '状态', 'status'],
  note: ['备注', '说明', 'note', 'remark'],
} as const

/** How the material declares its table. */
export const SPEC: TableSpec = {
  rowKeys: ['rows', 'items', 'containers', '箱'],
  columns: COLUMNS,
  header: {
  carrier: ['carrier', '船公司', '承运人', '箱东'],
  blNo: ['blNo', '提单号', '提运单号'],
  contractNo: ['contractNo', '协议号', '合同号'],
  currency: ['currency', '币制', '币种'],
  checkedAt: ['checkedAt', '核对日期'],
  },
}

/** Fields the material must carry somewhere for the reader to accept it. */
export const REQUIRE_ANY_OF = [
  '箱号',
  'containerNo',
  '超期天数',
  'overdueDays',
  '滞箱费金额',
  'amount',
  '还箱日期',
  'returnAt',
]

/**
 * Parse the material and attach its canonical field names.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized table, with each row's aliases resolved to field names.
 */
export function parseMaterial(source: string, target: string): TableInput {
  const table = parseTable(source, target, {
    ...SPEC,
    ...(REQUIRE_ANY_OF === undefined ? {} : { requireAnyOf: REQUIRE_ANY_OF }),
  })
  for (const row of table.rows) canonicaliseRow(row, SPEC)
  return table
}

/**
 * Run the rule pack against the material.
 * @param input - normalized table.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value, rule selection and overrides.
 * @returns the report.
 */
export function runCheck(input: TableInput, ruleset: Ruleset, options: TableCheckOptions) {
  return runTableCheck(input, ruleset, options)
}

export type { TableCheckOptions, TableInput }
