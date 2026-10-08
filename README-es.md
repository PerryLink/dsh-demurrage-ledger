# dsh-demurrage-ledger — Verificación de integridad y aritmética del libro de demoras y detenciones de contenedores

`dsh-demurrage-ledger` lee un libro de demoras y detenciones de contenedores (滞箱费台账) —la cabecera más una fila por contenedor— y comprueba la integridad y la aritmética de ese mismo libro: que cada fila registre al menos un número de contenedor o un conocimiento de embarque, que la fecha de inicio del periodo libre y la fecha de devolución se puedan analizar y sean coherentes entre sí, que los días de exceso sean iguales a la diferencia entre esas dos fechas menos los días libres, que el importe sea igual a los días de exceso × la tarifa, que la moneda se escriba como código de tres letras, que no se repita ningún número de contenedor y que no quede ningún marcador de plantilla sin sustituir en la observación. Los días libres y la tarifa se toman del propio libro, cuyas columnas pueden estar en chino o en inglés.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| Una fila tiene vacíos tanto el número de contenedor como el conocimiento de embarque. ¿Se informa de algo? | Sí. `DL-001` exige que en cada fila a la que el libro da al menos una de esas dos columnas esté relleno `containerNo` o `blNo`, e informa de la fila cuando ambas están vacías. Solo comprueba que uno de los dos esté puesto, no si el cargo debió producirse. Si el libro no trae ninguna de las dos columnas, la regla se nombra a sí misma en `skipped` en lugar de pasar en silencio. |
| La fecha de inicio se escribió como `15/03/2026` y la fecha de devolución es anterior. ¿Qué hace la regla? | `DL-002` analiza `startAt` y lo compara con `returnAt`: un valor que no puede leer como fecha se informa en esa fila en lugar de omitirse, y una fecha de inicio posterior a la de devolución también se informa; el mismo día cuenta como no posterior. Solo compara esas dos fechas: qué convención de inicio se aplica (conocimiento de embarque, entrega o llegada) queda para la tarifa del transportista y el contrato. |
| La columna de días de exceso dice 10, pero las dos fechas y el periodo libre dan 7. ¿Se detecta? | Sí. `DL-003` recalcula los días como `returnAt` − `startAt` − `freeDays` e informa de la fila cuando el `overdueDays` declarado difiere en más de la `tolerance` configurada, 0 por defecto. Solo se ejecuta en filas con los cuatro valores presentes y analizables; cuando ninguna fila los reúne, la regla se informa en `skipped`. La convención de inicio y si el periodo libre cuenta festivos siguen siendo del contrato: para una base de días laborables o de horas, suba la tolerancia o desactive la regla. |
| El importe no es igual a los días de exceso por la tarifa, y mi tarifa se escalona. ¿Se informa? | `DL-004` multiplica `overdueDays` × `rate` e informa de la fila cuando `amount` difiere en más de la `tolerance`, 0.01 por defecto. No juzga si la tarifa es razonable ni si coincide con la del transportista. Una tarifa escalonada no cabe en una sola celda `rate`, así que ese libro informará de una diferencia: desactive la regla, o registre una tarifa media y dígalo en la observación. |
| La celda de moneda dice `美元`, o `usd`. ¿Se informa? | Sí. `DL-005` informa de todo valor de `currency` que no coincida con el patrón del paquete, `^[A-Z]{3}$` por defecto: tres letras mayúsculas como `USD`. Es solo una comprobación de forma y no juzga si esa moneda es la correcta para la liquidación. Su base es la única norma pública que cita el paquete, y su excerpt deja constancia de que el texto del artículo no se obtuvo, por lo que la regla se queda en warn. Sin columna de moneda, la regla se nombra en `skipped`. |
| El mismo número de contenedor aparece en dos filas. ¿Es un registro duplicado? | `DL-006` informa de la fila cuando un valor de `containerNo` se repite, comparando sin espacios, y señala la fila anterior con la que coincide. Solo comprueba la unicidad, y un hallazgo requiere confirmación humana: un contenedor devuelto por etapas, o liberado y vuelto a retener, puede ocupar legítimamente dos filas — dígalo en la observación en vez de borrar una fila. Sin columna `containerNo`, la regla informa de que no pudo ejecutarse en lugar de pasar en silencio. |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
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

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-demurrage-ledger
dsh --profile <name> --dump-config | grep 'dsh-demurrage-ledger'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/demurrage-ledger.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-demurrage-ledger
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-demurrage-ledger contributors.
