# Z80 Skills — Adaptive Research

**Idiomas:** [English](README.md) · Español

Plugin para Codex con un workflow adaptativo independiente, un selector de
dominio ligero, ocho skills complementarios de ingeniería y envío protegido
mediante BridgeZX para proyectos Z80, especialmente software de ZX Spectrum
escrito en ensamblador, C o una mezcla de ambos con z88dk o SDCC.

El objetivo no es producir listas genéricas de trucos. Los skills inspeccionan
el código y los artefactos actuales, adaptan la profundidad y el paralelismo al
riesgo real y distinguen claramente entre evidencia probada, estimaciones e
hipótesis.

> Ejecución adaptativa, desarrollo dirigido por especificaciones, depuración
> causal, análisis, documentación de repositorios, organización, reducción de
> tamaño y optimización multiobjetivo basados en
> evidencia para Z80 y ZX Spectrum.

## Contenido

- [Qué incluye](#qué-incluye)
- [Qué aporta frente a un análisis genérico](#qué-aporta-frente-a-un-análisis-genérico)
- [Ejecución adaptativa y multiagente](#ejecución-adaptativa-y-multiagente)
- [Investigación externa dirigida](#investigación-externa-dirigida)
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
| [workflow](skills/workflow/SKILL.md) | ¿Cuál es el menor nivel de ejecución suficiente para esta tarea de ingeniería? | Ejecución directa Light o Medium en el hilo principal, o coordinación Heavy plana con workers integrados y acotados. |
| [route-z80](skills/route-z80/SKILL.md) | ¿Qué único especialista Z80, si procede, es responsable del resultado solicitado? | Una ruta de dominio o `workflow` sin especialista para ingeniería ordinaria. |
| [send-bridgezx](skills/send-bridgezx/SKILL.md) | ¿Qué ficheros o directorios concretos deben llegar al ZX o Next? | Envío BridgeZX protegido con IP explícita o última conocida, destino opcional y secuencia solicitada. |
| [develop-z80](skills/develop-z80/SKILL.md) | ¿Cómo convertir esta idea para ZX o Next en un proyecto construible y verificable? | Concepto, especificación, plan técnico, backlog de tareas, implementación y evidencia criterio por criterio. |
| [document-z80](skills/document-z80/SKILL.md) | ¿Cómo estructurar la documentación pública del repositorio y mantenerla correcta entre idiomas? | README y jerarquía documental basados en evidencia, con comandos, requisitos de hardware y paridad EN/ES verificados. |
| [port-spectranext](skills/port-spectranext/SKILL.md) | ¿Cómo atraviesa un programa ZX existente el pipeline consumidor del cartucho Spectranext? | Intake canónico, implementación acotada, gates ligados a artefactos, evidencia física y handoff final. |
| [debug-z80](skills/debug-z80/SKILL.md) | ¿Qué causa este fallo observado y qué componente posee la corrección? | Una explicación causal falsable y, cuando se solicita, un fix de causa raíz verificado. |
| [audit-z80](skills/audit-z80/SKILL.md) | ¿Hay defectos latentes o riesgos amplios de corrección? | Hallazgos de solo lectura priorizados por severidad y confianza, con evidencia, verificación y riesgo residual. |
| [organize-z80](skills/organize-z80/SKILL.md) | ¿Qué fronteras de propiedad, dependencias, fuentes y placement necesitan cambiar? | Mapa proporcional, diseño, slice reversible o decisión explícita de no cambiar. |
| [shrink-z80](skills/shrink-z80/SKILL.md) | ¿Cómo reducir almacenamiento, tamaño enlazado, memoria residente, BSS/stack, bancos u overlays? | Reducciones netas clasificadas por seguridad y por calidad de la evidencia. |
| [optimize-z80](skills/optimize-z80/SKILL.md) | ¿Cuál es el cuello de botella real y qué cambios ofrecen el mejor equilibrio entre tamaño, velocidad, RAM, renderizado y latencia? | Hasta tres experimentos priorizados con impacto, riesgo, rollback y plan de validación. |

`workflow` es independiente de Z80 y selecciona el esfuerzo de ejecución.
`route-z80` es el único punto de entrada implícito para seleccionar dominio Z80
desde lenguaje natural, incluidas coincidencias inequívocas con un especialista.
Los skills enrutados se solapan solo donde es útil:

- Usa `workflow` directamente para planificación, implementación y verificación adaptativas.
- Usa `route-z80` para elegir un especialista sin cargar todos los candidatos.
- Usa `send-bridgezx` para entregar ficheros o directorios mediante el cliente
  oficial BridgeZX sin mantener otra IP ni otra implementación del protocolo.
- Usa `develop-z80` solo para una iniciativa explícita de producto o un dossier
  SDD existente, no para fixes ordinarios ni features aisladas del repositorio.
- Usa `document-z80` para crear, reestructurar, revisar o sincronizar la
  documentación pública sin borrar la identidad del proyecto.
- Usa `port-spectranext` para portar un programa ZX existente al cartucho
  Spectranext, no para targets ZX Spectrum Next ni trabajo sobre el backend.
- Usa `debug-z80` para un fallo observado cuyo owner causal sigue sin conocerse.
- Usa `audit-z80` para revisión preventiva o amplia de corrección en solo lectura.
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
| **Medium** | El hilo principal resuelve directamente un flujo ordenado de varios pasos. |
| **Heavy** | El hilo principal coordina workers integrados independientes y acotados en topología plana. |

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

## Instalación

### Requisitos

- Codex con soporte para plugins y skills.
- Los niveles Light y Medium de `workflow` trabajan directamente; Heavy usa
  subagentes cuando están disponibles. Los roles y la selección de modelos
  siguen la [política canónica](skills/workflow/references/roles.md), que comprueba
  las capacidades del runtime y declara las sustituciones de modelo o esfuerzo.
- Git para clonar y actualizar el repositorio.
- Python 3.9 o posterior para los helpers generales; Python 3.11 o posterior
  es obligatorio cuando `optimize-z80` deba interpretar o aplicar una política
  TOML.
- z88dk o SDCC únicamente cuando el proyecto o una medición reproducible los
  requiera.

### Primera instalación

Clona el repositorio en cualquier ubicación bajo tu directorio personal. El
checkout es la fuente canónica de los once skills.

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
completa. El plugin ya incluye los once skills, incluidos `route-z80` y
`workflow`. El instalador avisa si encuentra una de estas
ubicaciones duplicadas; muévela o desactívala antes de abrir una tarea nueva de
Codex.

Solo `route-z80` participa en la selección implícita de dominio Z80. Los nueve
skills enrutados siguen disponibles mediante invocación explícita de
`$send-bridgezx`, `$develop-z80`, `$document-z80`, `$port-spectranext`,
`$debug-z80`, `$audit-z80`, `$organize-z80`, `$shrink-z80` y `$optimize-z80`;
después de decidir, `route-z80` carga únicamente el hermano seleccionado. Así el
router también cubre peticiones inequívocas en lenguaje natural, mientras el
trabajo ordinario permanece en `workflow` y no se inyectan las nueve descripciones
especialistas.

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

### Grok Build y sincronización con Claude

En Windows, instala los once skills en Grok Build con las adaptaciones del host
derivadas de las fuentes canónicas de `workflow`:

```powershell
pwsh -File .\scripts\install-for-grok.ps1
```

El instalador incluye `route-z80`, guarda por defecto una copia con timestamp de
los skills existentes en el destino, incluye el runner de worktrees desechables
y parchea únicamente las copias instaladas. Añade `-SyncClaude` para copiar
también los mismos once árboles canónicos, sin adaptaciones Grok, a
`~/.claude/skills`:

```powershell
pwsh -File .\scripts\install-for-grok.ps1 -SyncClaude
```

Usa `-SkipBackup` solo con destinos de prueba desechables. Abre una tarea nueva
de Grok o Claude después de instalar para recargar su catálogo de skills.

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

### Envío mediante BridgeZX

```text
Usa send-bridgezx para enviar build/juego.nex a mi Spectrum Next con la última
IP conocida por BridgeZX, dentro de JUEGOS/DEMO.
```

### Documentación del repositorio

```text
Usa document-z80 para reestructurar el README como landing page, verificar cada
afirmación sobre build y hardware y mantener alineados los documentos en inglés
y español sin perder la voz del proyecto.
```

### Desarrollo dirigido por especificaciones

```text
Usa develop-z80 para dirigir esta idea de juego para ZX Spectrum Next desde el
concepto hasta una implementación verificada. Elige y ejecuta por mí las fases
SDD; pregunta solo cuando falte una decisión de producto material.
```

### Port al cartucho Spectranext

```text
Usa port-spectranext para reanudar el port de este programa ZX existente al
cartucho Spectranext. Empieza por el port request canónico, conserva el seam del
consumidor y detente para obtener evidencia del hardware real cuando proceda.
```

### Depuración de causa raíz

```text
Usa debug-z80 para aislar por qué este build 128K falla al volver de la ISR. No
edites hasta que un check discriminante identifique el owner causal; entonces
aplica y verifica el fix mínimo.
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
- `port-spectranext` mantiene autoritativo el checkout externo de Spectranext y
  aislado el estado del consumidor; las ediciones quedan dentro del seam
  autorizado y los resultados físicos exigen observación explícita del usuario.
- `debug-z80` mantiene diagnóstico y fixes candidatos en un worktree desechable;
  solo edita el árbol principal para una reparación solicitada y causalmente probada.
- `document-z80` edita solo la documentación pública para personas incluida en
  el alcance; no cambia código, configuración de build, releases ni instrucciones
  de agentes.
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

- `skills/<nombre>/`: `SKILL.md`, metadatos de agente, referencias y analizadores.
- `scripts/`: instalación, runner de worktrees y pruebas.
- `evals/`: casos y fixtures de routing/evidencia; los resultados generados se ignoran.
- `agent_docs/`: contexto mantenido del proyecto.

Consulta el [mapa del repositorio](agent_docs/project_structure.md) para la propiedad de archivos.

## Validación

Pruebas incluidas:

```sh
python3 scripts/test_workflow_integration.py
python3 scripts/test_workflow_context_efficiency.py
python3 scripts/test_personal_marketplace.py
python3 scripts/test_run_in_worktree.py
python3 skills/audit-z80/scripts/smoke_test.py
python3 skills/shrink-z80/tests/run_smoke.py
python3 -m unittest discover -s skills/optimize-z80/scripts -p 'test_*.py'
python3 scripts/test_behavior_evals.py
python3 skills/send-bridgezx/scripts/test_bridgezx_transfer.py
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
`evals/results/`, junto con trazas del runtime por caso. Usa `--model` y
`--reasoning-effort` para hacer explícita la comparación. Los resultados separan
los ajustes solicitados de los confirmados por el runtime, registran el consumo
de tokens informado y las acciones observadas, y comparan los archivos de cada
fixture antes y después. Los efectos no observables de comandos o herramientas
quedan como desconocidos; el JSON final del modelo no demuestra que no intentó
escribir. Las trazas pueden contener datos del fixture y rutas locales;
revísalas antes de compartirlas.

Los informes incluyen una huella del plugin fuente y de las entradas de
evaluación; esa huella no demuestra por sí sola que la copia instalada coincida.
Mantén iguales los casos, fixtures, modelo y esfuerzo al comparar revisiones
de skills por calidad o coste. `evals/baseline.json` conserva
resultados históricos verificados; no demuestra que una versión posterior o
una suite ampliada hayan pasado.

## Licencia y copyright

Copyright © 2026 M. Ignacio Monge García.

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE). Permite usar,
copiar, modificar, publicar y distribuir el software y su documentación,
siempre que se conserven el aviso de copyright y el texto de la licencia.

## Autor

M. Ignacio Monge García
