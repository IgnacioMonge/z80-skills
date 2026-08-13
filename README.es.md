# Z80 Skills — Adaptive Research

**Idiomas:** [English](README.md) · Español

Plugin para Codex con un workflow adaptativo independiente, un selector de
dominio ligero y cinco skills complementarios para desarrollar, analizar y
organizar proyectos Z80, especialmente software de ZX Spectrum escrito en
ensamblador, C o una mezcla de ambos con z88dk o SDCC.

El objetivo no es producir listas genéricas de trucos. Los skills inspeccionan
el código y los artefactos actuales, adaptan la profundidad y el paralelismo al
riesgo real y distinguen claramente entre evidencia probada, estimaciones e
hipótesis.

> Ejecución adaptativa, desarrollo dirigido por especificaciones, análisis,
> organización, reducción de tamaño y optimización multiobjetivo basados en
> evidencia para Z80 y ZX Spectrum.

## Contenido

- [Qué incluye](#qué-incluye)
- [Qué aporta frente a un análisis genérico](#qué-aporta-frente-a-un-análisis-genérico)
- [Ejecución adaptativa y multiagente](#ejecución-adaptativa-y-multiagente)
- [Investigación externa dirigida](#investigación-externa-dirigida)
- [Detalle de cada skill](#detalle-de-cada-skill)
- [Instalación](#instalación)
- [Uso](#uso)
- [Artefactos recomendados](#artefactos-recomendados)
- [Seguridad y límites](#seguridad-y-límites)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Validación](#validación)
- [Licencia y copyright](#licencia-y-copyright)

## Qué incluye

| Skill | Pregunta principal | Resultado |
|---|---|---|
| `workflow` | ¿Cuál es el menor nivel de ejecución suficiente para esta tarea de ingeniería? | Ejecución directa light, un flujo medium controlado por Sol o coordinación heavy plana con workers Luna acotados. |
| `route-z80` | ¿Qué único especialista Z80, si procede, es responsable del resultado solicitado? | Una ruta de dominio o `workflow` sin especialista para ingeniería ordinaria. |
| `develop-z80` | ¿Cómo convertir esta idea para ZX o Next en un proyecto construible y verificable? | Concepto, especificación, plan técnico, backlog de tareas, implementación y evidencia criterio por criterio. |
| `audit-z80` | ¿Hay defectos, corrupción, errores ABI, riesgos ISR/memoria/hardware o regresiones? | Hallazgos priorizados por severidad y confianza, con evidencia, verificación y riesgo residual. |
| `organize-z80` | ¿Qué fronteras de propiedad, dependencias, fuentes y placement necesitan cambiar? | Mapa proporcional, diseño, slice reversible o decisión explícita de no cambiar. |
| `shrink-z80` | ¿Cómo reducir almacenamiento, tamaño enlazado, memoria residente, BSS/stack, bancos u overlays? | Reducciones netas clasificadas por seguridad y por calidad de la evidencia. |
| `optimize-z80` | ¿Cuál es el cuello de botella real y qué cambios ofrecen el mejor equilibrio entre tamaño, velocidad, RAM, renderizado y latencia? | Hasta tres experimentos priorizados con impacto, riesgo, rollback y plan de validación. |

`workflow` es independiente de Z80 y selecciona el esfuerzo de ejecución.
`route-z80` selecciona dominio únicamente cuando el objetivo es realmente
ambiguo. Los cinco skills especialistas se solapan solo donde es útil:

- Usa `workflow` directamente para planificación, implementación y verificación adaptativas.
- Usa `route-z80` para elegir un especialista sin cargar todos los candidatos.
- Usa `develop-z80` solo para una iniciativa explícita de producto o un dossier
  SDD existente, no para fixes ordinarios ni features aisladas del repositorio.
- Usa `audit-z80` para corrección y seguridad técnica.
- Usa `organize-z80` para mapear o mejorar con seguridad propiedad, dependencias, layout de fuentes y placement en runtime.
- Usa `shrink-z80` para una búsqueda exhaustiva centrada exclusivamente en
  tamaño.
- Usa `optimize-z80` para decidir entre objetivos que compiten entre sí y
  ordenar los siguientes experimentos.

## Qué aporta frente a un análisis genérico

### Evidencia local antes que folklore

- Solo el código actual y los artefactos demostrablemente frescos pueden
  confirmar un hallazgo o una mejora.
- Los mapas, símbolos, listings, ASM generado y binarios enlazados cuentan como
  evidencia únicamente cuando corresponden a la misma revisión, configuración
  y target.
- Escáneres, agentes, conocimiento previo, foros y repositorios generan
  candidatos; no sustituyen la verificación local.
- Un artefacto obsoleto reduce explícitamente la confianza a estados como
  `NEEDS BUILD`, `REQUIERE BUILD` o `SPECULATIVE`.
- En proyectos con varios targets, una propuesta solo supera la puerta de
  promoción cuando cada target satisface sus propios límites.

### Carga progresiva

Cada `SKILL.md` funciona como un dispatcher compacto. Codex carga primero el
contrato común y después únicamente las referencias y scripts pertinentes para
el problema observado. Esto evita introducir en contexto manuales, técnicas o
logs que no pueden cambiar el resultado.

### Herramientas deterministas

El plugin incluye analizadores Python sin dependencias externas para perfilar
el proyecto, resumir mapas, detectar patrones, inventariar fronteras ABI,
evaluar frescura de artefactos, localizar library pulls y estimar candidatos.
Sus resultados son señales reproducibles, no veredictos automáticos.

## Ejecución adaptativa y multiagente

El skill independiente `workflow` es el núcleo común de ejecución:

| Nivel | Estrategia |
|---|---|
| **Light** | El hilo principal resuelve directamente una tarea acotada. |
| **Medium** | Un controlador Sol persistente planifica y revisa un flujo de ejecución Luna. |
| **Heavy** | Un controlador Sol persistente coordina workers Luna independientes y acotados en topología plana. |

En `auto`, cada skill Z80 aporta señales de dominio `Focused`, `Standard` o
`Deep` después del preflight. Workflow controla ruta, despacho, reparación,
verificación e integración; el skill de dominio conserva puertas de evidencia,
definición de lanes, contrato de salida y restricciones de escritura. Un nivel
explícito gana, pero nunca autoriza una operación prohibida por el proyecto o el
skill de dominio.
Antes del despacho, workflow clasifica cada superficie como solo lectura del
árbol principal, exclusiva de un worktree desechable o mutación autorizada del
árbol principal, y selecciona solo roles compatibles con esa frontera.

## Investigación externa dirigida

La búsqueda externa se activa para resolver una incertidumbre concreta, no
para adornar el informe ni repetir una lista de sitios conocidos.

### Cuándo se activa

- El usuario solicita investigación profunda en foros, blogs, repositorios o
  demoscene.
- Una versión de compilador, ABI, firmware, emulador, modelo de hardware o
  detalle de timing puede cambiar un hallazgo principal.
- El código, los artefactos generados y la documentación se contradicen.
- Un análisis profundo mantiene un punto ciego material.
- Una secuencia de instrucciones, helper, codec, renderer, loader o esquema de
  bancos requiere arqueología de código.

### Cómo busca

1. Formula una pregunta desde una firma local mínima: opcode, símbolo, fragmento
   emitido, versión, dirección, síntoma o restricción.
2. Busca fragmentos exactos y conceptos con vocabulario alternativo.
3. Amplía términos en inglés, español, polaco, ruso, checo y otras comunidades
   regionales pertinentes.
4. Diversifica las fuentes: código, tests, commits, issues, forks, emuladores,
   mediciones de hardware, listas de correo, foros archivados, blogs personales,
   repositorios pequeños, disassemblies, generadores y material demoscene.
5. Sigue autores, citas, forks, problemas relacionados y enlaces archivados.
6. Intenta refutar cada finalista buscando bugs, regresiones, issues cerrados o
   rechazados y fallos específicos por modelo.
7. Verifica CPU, modelo Spectrum, ABI, interrupciones, paginación, memoria,
   toolchain y timing antes de transferir una técnica.

La investigación tiene presupuesto y reglas de parada: conserva solo las pocas
fuentes capaces de cambiar una decisión. Una técnica popular sin ancla en el
proyecto permanece como hipótesis.

Para proteger proyectos privados, las búsquedas usan únicamente firmas mínimas
normalizadas; nunca deben subir código privado ni identificadores del proyecto.

## Detalle de cada skill

### `route-z80`

Dispatcher de dominio ligero para peticiones Z80 ambiguas. Selecciona un único
especialista según el resultado solicitado, o `workflow` para un fix, revisión,
refactor, test, build o cambio documental ordinario. No decide entre Light,
Medium y Heavy ni carga todos los skills candidatos.

### `develop-z80`

Desarrollo dirigido por especificaciones desde una idea inicial hasta código
verificado. Da forma al concepto, define comportamiento observable, elige el
perfil ZX/Next, planifica hitos ejecutables, crea tareas con dependencias,
implementa las tareas listas y reconcilia cada criterio de aceptación con
evidencia.

El usuario no dirige esas fases. El skill deduce dónde empezar, avanza
automáticamente y solo pregunta por decisiones de producto materiales o por la
autorización que falte antes de modificar código de producto.

El trabajo pequeño conserva un único dossier SDD en la conversación. Un proyecto
de varias sesiones puede persistir ese mismo dossier en el repositorio en vez de
dispersar idea, requisitos, plan, tareas y estado entre varios archivos.

`auto` sigue siendo la experiencia normal; los techos opcionales `idea`, `spec`,
`plan`, `tasks`, `implement` y `verify` permiten trabajo dirigido. Evidencia,
decisiones de plataforma, formato del dossier y verificación por hitos se cargan
progresivamente desde referencias separadas.

### `audit-z80`

Auditoría de solo lectura para encontrar defectos reales y riesgos
reproducibles.

**Cobertura**

- fronteras C/ASM, calling conventions, registros, flags y stack;
- ISR, `DI`/`EI`, reentrada y estado compartido;
- mapas de memoria, BSS, stack gap, bancos y overlays;
- firmware, ROM, RST 8, esxDOS, divMMC y diferencias entre modelos;
- semántica C, buffers, promoción, signedness y lifetime;
- ASM/listings generados, reglas copt y comportamiento z88dk/SDCC;
- ULA, contention, puertos, timing y regresiones visibles para el usuario.

**Modos**

- `auto`: preflight y profundidad adaptativa.
- `preflight`: perfil y señales de escalado sin auditoría completa.
- `full` / `diverge`: cobertura amplia con las mismas puertas de evidencia.
- Focos: `asm`, `c`, `abi`, `isr`, `memory`, `spectrum-hw`, `esxdos`,
  `toolchain`, `copt` y `map`.

**Helpers principales**

- `preflight_scan.py`: inventario de fuentes, artefactos y señales de riesgo.
- `z80_pattern_scan.py`: patrones estructurales ASM/C.
- `abi_inventory.py`: declaraciones, convenciones y fronteras C/ASM.
- `map_summary.py`: símbolos, direcciones y aproximación del stack gap.
- `smoke_test.py`: comprobación reproducible de los analizadores.

La salida pone primero los hallazgos que superan la puerta de promoción. Si
ninguno sobrevive, lo indica y señala el riesgo residual más importante en vez
de rellenar el informe con observaciones débiles.

### `organize-z80`

Workflow de arquitectura y reorganización Z80 basado en evidencia.

**Cobertura**

- propiedad, dependencias, estado mutable, layout de fuentes y placement en runtime;
- un mapa persistente opcional del estado actual, recomendado y final verificado;
- seams ASM puro y C/ASM, mapas, símbolos, entradas generadas y targets;
- migraciones incrementales que preservan ABI, timing, banking, formatos y contratos de build.

**Modos**

- `map`, `design`, `plan`, `apply` y `review`, además de `help`.
- La demanda escala como `Focused`, `Standard` o `Deep`; `apply` ejecuta únicamente un slice aprobado y reversible.

Informa severidad, confianza, coste organizativo, evidencia de validación y
`NO REORGANIZATION NEEDED` cuando la estructura actual ya es proporcionada.

### `shrink-z80`

Optimizador de tamaño basado en mediciones y contabilidad neta.

**Objetivos separados**

- tamaño de almacenamiento;
- CODE/DATA enlazado;
- memoria residente;
- BSS y margen de stack;
- techo de banco u overlay;
- reserva mínima por target.

**Modos**

- `scan`: análisis adaptativo completo.
- `preflight`: perfil de artefactos y presión.
- Focos: `deadcode`, `dedup`, `micro`, `data`, `compress`, `refactor`,
  `arch`, `libpull`, `blackbelt` y `reserve`.
- `diverge`: exploración amplia sin relajar la prueba.

**Orden de ataque**

1. Arquitectura, residencia, datos y librerías enlazadas.
2. Código generado, helpers y representaciones repetidas.
3. Compresión con coste neto y RAM pico separados.
4. Microoptimizaciones y técnicas de mayor riesgo solo cuando pueden importar.

No suma propuestas dependientes, subsumidas, incompatibles o todavía no
construidas. Distingue seguridad (`SAFE`, `AGGRESSIVE`, `EXPERIMENTAL`) y
calidad de medida (`EXACTO`, `ESTIMADO`, `REQUIERE BUILD`).

**Helpers principales**

- `preflight_scan.py` y `artifact_freshness.py`;
- `map_summary.py`, `deadcode_scan.py` y `libpull_scan.py`;
- `generated_helper_scan.py` y `literal_dup_scan.py`;
- `z80_pattern_scan.py`;
- `net_compression_check.py`, que separa ahorro de almacenamiento y RAM pico.

### `optimize-z80`

Motor de estrategia multiobjetivo para decidir qué optimizar primero y cómo
validarlo.

**Ámbitos**

- tamaño, ciclos y latencia;
- RAM, stack y layout de datos;
- renderizado, contention e I/O;
- bancos, overlays y transiciones;
- C a ASM, ABI, librerías, codegen y toolchain;
- restricciones por modelo y hardware.

**Modos**

- `Triage`: inspección de solo lectura sin build. Los artefactos obsoletos
  limitan la confianza.
- `Measurement`: baseline reproducible en un worktree desechable.
- `Experiment`: requiere aprobación explícita, cambia una sola variable y se
  elimina salvo que el usuario pida conservarla.

Primero identifica el cuello de botella dominante. Después aplica vetos de
política y target, fusiona duplicados, audita los finalistas y recomienda como
máximo tres experimentos siguientes.

Cada candidato incluye:

- ancla y frescura de la evidencia;
- zona, mecanismo e impacto esperado;
- efecto sobre tamaño, ciclos/latencia, RAM/stack y UX cuando corresponda;
- riesgo, targets, restricciones, rollback y validación;
- confianza (`PROVEN`, `LIKELY` o `SPECULATIVE`);
- motivo por el que supera ahora a las alternativas.

Los estimadores estáticos de ciclos, mapas o patrones no constituyen prueba por
sí solos.

## Instalación

### Requisitos

- Codex con soporte para plugins y skills.
- Los niveles Medium y Heavy de `workflow` requieren subagentes de Codex y usan
  únicamente los tipos integrados `default`, `worker` y `explorer`. Sol y Luna
  son modelos preferidos, no dependencias de perfiles personalizados; cualquier
  pérdida del modelo fijado se gestiona y declara según el contrato del workflow.
- Git para clonar y actualizar el repositorio.
- Python 3.9 o posterior para los helpers generales; Python 3.11 o posterior
  es obligatorio cuando `optimize-z80` deba interpretar o aplicar una política
  TOML.
- z88dk o SDCC únicamente cuando el proyecto o una medición reproducible los
  requiera.

### Primera instalación

Clona el repositorio en cualquier ubicación bajo tu directorio personal. El
checkout es la fuente canónica de los siete skills.

```sh
git clone https://github.com/IgnacioMonge/z80-skills.git ~/plugins/z80-skills
cd ~/plugins/z80-skills
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

`install_personal_marketplace.py` crea o actualiza
`~/.agents/plugins/marketplace.json`, apunta `z80-skills` al checkout real,
conserva las demás entradas y sustituye solo la entrada llamada `z80-skills`.
No mantengas copias, enlaces simbólicos ni junctions creados manualmente para
ningún skill incluido bajo `~/.agents/skills/<skill-name>` ni en la ruta
heredada `~/.codex/skills/<skill-name>`. Esas copias pueden ocultar el plugin
con namespace y omitir archivos del paquete como `scripts/run_in_worktree.py`;
copiar directorios individuales desde `skills/` no constituye una instalación
completa. El plugin ya incluye los siete skills, incluidos `route-z80` y
`workflow`. El instalador avisa si encuentra una de estas
ubicaciones duplicadas; muévela o desactívala antes de abrir una tarea nueva de
Codex.

Solo `route-z80` participa en la selección implícita de dominio Z80. Los cinco
especialistas siguen disponibles mediante invocación explícita de
`$develop-z80`, `$audit-z80`, `$organize-z80`, `$shrink-z80` y `$optimize-z80`;
después de decidir, `route-z80` carga únicamente el hermano seleccionado. Así el
trabajo ordinario permanece en `workflow` y no se inyectan las cinco
descripciones especialistas.

Abre una tarea nueva de Codex después de instalar: el catálogo de skills se
carga al iniciar la tarea y no se actualiza dinámicamente dentro de una tarea
ya abierta.

### Actualización

```sh
cd /ruta/a/z80-skills
git pull --ff-only
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

Los cambios del plugin actualizan la versión del manifiesto incluida en Git
para que Codex cree una copia instalada nueva. No edites directamente
`~/.codex/plugins/cache`. Después de actualizar, abre una tarea nueva.

## Uso

Los skills se invocan mediante lenguaje natural. Cuanto más concretos sean el
target, el objetivo y los artefactos disponibles, más precisa será la
priorización.

### Workflow adaptativo

```text
Usa workflow en modo auto para implementar este cambio con el menor nivel de
ejecución suficiente y conservar los contratos existentes del repositorio.
```

### Selección de dominio Z80

```text
Usa route-z80 para elegir el único especialista relevante para esta petición
del repositorio Z80, o workflow si no hace falta un contrato especialista.
```

### Desarrollo dirigido por especificaciones

```text
Usa develop-z80 para dirigir esta idea de juego para ZX Spectrum Next desde el
concepto hasta una implementación verificada. Elige y ejecuta por mí las fases
SDD; pregunta solo cuando falte una decisión de producto material.
```

### Auditoría

```text
Usa audit-z80 en modo auto para revisar este proyecto mixto ASM/C.
Prioriza ABI, ISR y memoria; informa únicamente hallazgos anclados al código actual.
```

```text
Usa audit-z80 en modo full. Revisa las diferencias entre los targets 48K y 128K,
incluidos paging, ROM, stack, interrupciones y artefactos generados.
```

### Organización

```text
Usa organize-z80 en modo design para mapear propiedad, dependencias y placement
en este proyecto mixto ASM/C; propone únicamente el menor cambio de frontera justificado.
```

```text
Usa organize-z80 en modo apply para ejecutar solo esta fase aprobada; conserva
scopes de símbolos, mapas, ABI y el punto de rollback existente.
```

### Reducción de tamaño

```text
Usa shrink-z80 en modo scan. Necesito recuperar al menos 512 bytes de CODE/DATA
sin cambiar el comportamiento y separando ahorro exacto de ahorro estimado.
```

```text
Usa shrink-z80 en modo compress para comparar el tamaño neto y la RAM pico de
los codecs aplicados a estos assets concretos.
```

### Optimización multiobjetivo

```text
Usa optimize-z80 en modo Triage para identificar el cuello de botella real y
devolver los tres experimentos con mejor relación entre impacto, riesgo y coste.
```

```text
Usa optimize-z80 en modo Measurement para obtener una línea base fresca sin
modificar mi árbol principal.
```

## Artefactos recomendados

Los skills pueden empezar solo con fuentes, pero estos artefactos aumentan la
confianza:

| Evidencia | Utilidad |
|---|---|
| `.asm`, `.s`, `.c`, `.h` | Semántica actual, fronteras ABI, patrones y reachability. |
| `.map`, `.sym` | Layout, símbolos, secciones, bancos, library pulls y stack gap. |
| `.lst` o ASM generado | Comportamiento real del compilador y coste del codegen. |
| Binarios, TAP y assets | Tamaño final, compresión y comparaciones reproducibles. |
| Receta de build y flags | Reproducibilidad, toolchain, ABI y configuración. |
| Targets y límites explícitos | Vetos, reservas, compatibilidad y ranking correcto. |

Un timestamp reciente por sí solo no demuestra correspondencia. La revisión,
configuración y receta deben pertenecer a la misma línea base.

## Seguridad y límites

- Los análisis normales son de solo lectura.
- `workflow` nunca amplía los permisos concedidos por el proyecto o el skill de dominio.
- `develop-z80` mantiene idea, especificación, planificación y desglose de tareas
  en solo lectura; la primera edición greenfield también exige aceptación
  explícita de la spec. Todo avance multihito queda acotado a la sesión actual.
- `audit-z80` y `shrink-z80` no editan el proyecto.
- `organize-z80` solo edita código en modo `apply` tras una petición explícita,
  línea base congelada, frontera aprobada, un slice nombrado y rollback; una
  actualización solicitada explícitamente del mapa persistente solo puede
  editar ese documento y su puntero de carga.
- `optimize-z80` solo modifica una copia desechable en modo `Experiment` y
  requiere aprobación explícita.
- Los scripts incluidos usan la biblioteca estándar de Python, trabajan con
  archivos locales y no realizan búsquedas de red.
- Los tests escriben en directorios temporales y los eliminan al terminar.
- El plugin no incluye z88dk, SDCC, emuladores ni herramientas de profiling.
- No es un compilador, un profiler de hardware ni un optimizador automático.
- No confirma ahorros enlazados, timings o compatibilidad sin evidencia
  adecuada.
- SMC, abuso de SP, `DI`/`EI`, opcodes no documentados, floating bus y otras
  técnicas dependientes de hardware requieren etiquetas de riesgo y validación
  específica por target.
- La investigación externa nunca debe publicar fuentes privadas, rutas,
  símbolos sensibles ni identificadores del proyecto.

## Estructura del repositorio

```text
LICENSE
README.md
README.es.md
.codex-plugin/
  plugin.json
evals/
  baseline.json
  routing.jsonl
  evidence.jsonl
  fixtures/
  schemas/
scripts/
  install_personal_marketplace.py
  run_behavior_evals.py
  run_in_worktree.py
  test_behavior_evals.py
skills/
  workflow/
    SKILL.md
    agents/openai.yaml
    references/
  route-z80/
    SKILL.md
    agents/openai.yaml
  develop-z80/
    SKILL.md
    agents/openai.yaml
    references/
  audit-z80/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
  organize-z80/
    SKILL.md
    agents/openai.yaml
    references/
  shrink-z80/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
    tests/
  optimize-z80/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
```

Cada skill mantiene las instrucciones centrales en `SKILL.md` y los detalles
de carga selectiva en `references/`; los skills con analizadores reproducibles
los mantienen en `scripts/`.

## Validación

Pruebas incluidas:

```sh
python3 scripts/test_workflow_integration.py
python3 scripts/test_personal_marketplace.py
python3 scripts/test_run_in_worktree.py
python3 skills/audit-z80/scripts/smoke_test.py
python3 skills/shrink-z80/tests/run_smoke.py
python3 -m unittest discover -s skills/optimize-z80/scripts -p 'test_*.py'
python3 scripts/test_behavior_evals.py
```

También debe validarse el manifiesto del plugin y el frontmatter de cada skill
antes de publicar una nueva versión.

Los evals de comportamiento están separados deliberadamente de los unit tests.
Valida sus datasets sin consumir modelo:

```sh
python3 scripts/run_behavior_evals.py --dry-run
```

Tras instalar la misma versión que muestra `.codex-plugin/plugin.json`, ejecuta
las suites etiquetadas de routing y evidencia en sesiones Codex nuevas y de solo
lectura:

```sh
python3 scripts/run_behavior_evals.py --suite evals/routing.jsonl
python3 scripts/run_behavior_evals.py --suite evals/evidence.jsonl
```

El runner rechaza una versión instalada obsoleta salvo override explícito,
registra precisión y recall por ruta y escribe resultados JSON ignorados bajo
`evals/results/`. `evals/baseline.json` conserva el resumen verificado pequeño y
no sensible, distinguiendo ejecuciones completas de replays dirigidos de una
corrección.

## Licencia y copyright

Copyright © 2026 M. Ignacio Monge García.

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE). Permite usar,
copiar, modificar, publicar y distribuir el software y su documentación,
siempre que se conserven el aviso de copyright y el texto de la licencia.

## Autor

M. Ignacio Monge García
