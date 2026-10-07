import { describeTablePlugin } from './table-plugin-suite.ts'
import { Config } from '../src/config.ts'
import { parseMaterial, runCheck, SPEC } from '../src/model.ts'
import { buildView } from '../src/view.ts'
import { inject, name, resolvePackageFile, TOOL_NAME } from '../src/index.ts'

describeTablePlugin({
  name,
  inject,
  TOOL_NAME,
  resolvePackageFile,
  Config,
  rulesFile: 'rules/demurrage-ledger.yaml',
  parseMaterial,
  runCheck,
  buildView,
  columnNames: SPEC.columns,
  samples: {
    good: {
      carrier: '某某船务',
      blNo: 'MSCUAA123456',
      rows: [
        {
          箱号: 'MSCU1234567',
          提单号: 'MSCUAA123456',
          免箱期: '7',
          起算日期: '2026-03-01',
          还箱日期: '2026-03-15',
          超期天数: '7',
          费率: '120',
          滞箱费金额: '840',
          币制: 'USD',
        },
      ],
    },
    unknownColumn: { rows: [{ 备注: '甲' }] },
  },
})
