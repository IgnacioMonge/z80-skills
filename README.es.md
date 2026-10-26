# Z80 Skills

**Idiomas:** [English](README.md) · Español

Skills de agente para proyectos Z80, especialmente software de ZX Spectrum y ZX
Spectrum Next escrito en ensamblador, C o ambos con z88dk o SDCC. Funcionan con
Codex, Claude Code y Grok Build desde un único checkout; el soporte de Gemini /
Antigravity es parcial.

El paquete incluye once skills: un `workflow` adaptativo y portable, un
selector Z80 ligero, ocho especialistas de ingeniería y envío protegido
mediante BridgeZX. También incluye una herramienta opcional de reducción de
tamaño desatendida, [`shrink-agent`](tools/shrink-agent/README.md).

Los skills no producen listas genéricas de trucos. Inspeccionan el código y los
artefactos de build actuales, ajustan la profundidad y el paralelismo al riesgo
real y separan la evidencia probada de las estimaciones y las hipótesis.

## Contenido

- [Hosts compatibles](#hosts-compatibles)
- [Inicio rápido](#inicio-rápido)
- [Instalación](#instalación)
- [¿Qué skill necesito?](#qué-skill-necesito)
- [Uso](#uso)
- [Cómo funciona](#cómo-funciona)
- [Opcional: shrink-agent](#opcional-shrink-agent)
- [Artefactos recomendados](#artefactos-recomendados)
- [Seguridad y límites](#seguridad-y-límites)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Desarrollo y validación](#desarrollo-y-validación)
- [Licencia](#licencia)

## Hosts compatibles

Todos los hosts leen los mismos árboles canónicos de `skills/`. No se copia
nada, así que un `git pull` los actualiza todos.

| Host | Instalación | Invocación explícita | Entradas implícitas | Estado |
|---|---|---|---|---|
| Codex | Plugin del marketplace personal | `$route-z80`, `$debug-z80`, … | `route-z80`, `workflow` | Completo; las evals de comportamiento se ejecutan aquí |
| Claude Code | Junctions (Windows) o enlaces simbólicos (macOS, Linux) | `/route-z80`, `/debug-z80`, … | `route-z80`, `workflow` | Completo |
| Grok Build | `[skills].paths` en `~/.grok/config.toml` | Mediante el catálogo de skills de Grok | Sigue el catálogo de Grok; los campos de restricción de Codex y Claude Code pueden no aplicarse | Carga completa de skills |
| Gemini / Antigravity | Sin instalador en este repositorio | — | — | Parcial: solo manifiesto y mapeo de delegación |

En cualquier host también puedes describir la tarea en lenguaje natural;
`route-z80` elige el especialista. La delegación multiagente del nivel Heavy se
adapta a la primitiva de subagentes y a los nombres de modelo de cada host
(véase [Ejecución adaptativa y
multiagente](#ejecución-adaptativa-y-multiagente)).

## Inicio rápido

1. Clona el repositorio una sola vez, en cualquier lugar de tu directorio
   personal:

   ```sh
   git clone https://github.com/IgnacioMonge/z80-skills.git ~/plugins/z80-skills
   cd ~/plugins/z80-skills
   ```

2. Regístralo en tu host (detalles en [Instalación](#instalación)):

   | Host | Orden |
   |---|---|
   | Codex | `python3 scripts/install_personal_marketplace.py` y después `codex plugin add z80-skills@personal` |
   | Claude Code, Windows | `pwsh -File .\scripts\install-for-claude.ps1` |
   | Claude Code, macOS o Linux | `sh scripts/install-for-claude.sh` |
   | Grok Build | `pwsh -File .\scripts\install-for-grok.ps1` |

3. Abre una tarea o sesión **nueva**. El catálogo de skills se carga al inicio
   y no se refresca dentro de una tarea ya abierta.

4. Prueba una petición dentro de un proyecto Z80:

   ```text
   Usa route-z80 para elegir el especialista adecuado para esta petición: el
   build de 128K se cuelga al volver de la ISR.
   ```

## Instalación

### Requisitos

- Un host compatible: Codex con soporte de plugins, Claude Code o Grok Build.
- Git, para clonar y actualizar el repositorio.
- Python 3.9 o posterior para los helpers incluidos. `optimize-z80` necesita
  Python 3.11 o posterior para interpretar una política TOML del proyecto; el
  envío por BridgeZX necesita 3.10 o posterior; `shrink-agent` necesita 3.11 o
  posterior. En Windows, usa `python` o `py` donde los ejemplos dicen `python3`.
- PowerShell (`pwsh`) para el instalador de Claude Code en Windows y para el de
  Grok Build.
- z88dk o SDCC solo cuando el proyecto o una medición reproducible los
  necesiten. Este repositorio no incluye compiladores, emuladores ni
  profilers.

### Codex

```sh
cd ~/plugins/z80-skills
python3 scripts/install_personal_marketplace.py
codex plugin add z80-skills@personal
```

`install_personal_marketplace.py` crea o actualiza
`~/.agents/plugins/marketplace.json`, apunta la entrada `z80-skills` a este
checkout y conserva las demás entradas. Después, Codex instala el plugin con
los once skills.

Solo `route-z80` y `workflow` se invocan de forma implícita. Los nueve
especialistas siguen disponibles como `$send-bridgezx`, `$develop-z80`,
`$document-z80`, `$port-spectranext`, `$debug-z80`, `$audit-z80`,
`$organize-z80`, `$shrink-z80` y `$optimize-z80`. Tras seleccionar la ruta,
`route-z80` carga solo el especialista elegido, de modo que el trabajo
rutinario sigue en `workflow` y el contexto no se llena con la descripción de
todos los especialistas.

No mantengas copias, enlaces simbólicos ni junctions de los skills incluidos en
`~/.agents/skills/<nombre>` ni en la ubicación heredada
`~/.codex/skills/<nombre>`. Ocultan el plugin y no contienen archivos del
paquete como `scripts/run_in_worktree.py`. El instalador avisa cuando encuentra
alguna; muévela o desactívala antes de abrir una tarea nueva. No edites nunca
`~/.codex/plugins/cache` directamente.

### Claude Code

```powershell
pwsh -File .\scripts\install-for-claude.ps1
```

```sh
sh scripts/install-for-claude.sh
```

El instalador enlaza `~/.claude/skills/<nombre>` con `skills/<nombre>` para los
once skills. También enlaza `~/.claude/scripts` y `~/.claude/tools` con
`scripts/` y `tools/` de este repositorio, para que se resuelvan las
referencias `../../scripts/...` y `../../tools/...` de los skills. Ambos
instaladores son idempotentes: sustituyen los enlaces obsoletos e informan de
los directorios reales que estorban, pero nunca los borran.

Solo `route-z80` y `workflow` se invocan de forma implícita. Los nueve
especialistas declaran `disable-model-invocation: true` y siguen disponibles
como `/develop-z80`, `/optimize-z80`, etc.

### Grok Build

```powershell
pwsh -File .\scripts\install-for-grok.ps1
```

El instalador añade `<repo>/skills` a `[skills].paths` en
`~/.grok/config.toml`, de modo que Grok Build lee los árboles en su sitio.
También borra copias obsoletas de los once skills incluidos en
`~/.grok/skills` y `~/.claude/skills`, y no toca los skills personales ajenos
al paquete.

Si también usas Claude Code, ejecuta el instalador de Grok con
`-SkipClaudeCleanup`. Si no, eliminará los enlaces de Claude Code como si
fueran copias obsoletas.

### Gemini / Antigravity

El repositorio incluye `gemini-extension.json`, y `workflow` asigna sus roles
de delegación a `invoke_subagent` en los runtimes que lo ofrecen (véase
[roles](skills/workflow/references/roles.md#other-hosts-gemini--antigravity)).
Todavía no hay instalador ni configuración probada para estos hosts.

### Actualización

```sh
cd ~/plugins/z80-skills
git pull --ff-only
```

Claude Code y Grok Build leen directamente los árboles actualizados. Codex
instala una copia versionada, así que vuelve a ejecutar el instalador del
marketplace y `codex plugin add z80-skills@personal`. Los cambios del plugin
suben la versión del manifiesto para que Codex cree una copia nueva. Después,
abre una tarea o sesión nueva en cada host.

## ¿Qué skill necesito?

| Skill | Úsalo cuando | Obtienes |
|---|---|---|
| [workflow](skills/workflow/SKILL.md) | Cualquier tarea de ingeniería, Z80 o no, cuyo esfuerzo y delegación deban ajustarse al riesgo. | Ejecución directa Light o Medium, o coordinación Heavy plana con workers acotados. |
| [route-z80](skills/route-z80/SKILL.md) | Cualquier petición Z80 en lenguaje natural, aunque el especialista parezca obvio; omítelo solo si nombras directamente al especialista. | Un especialista, o `workflow` para el trabajo ordinario. |
| [send-bridgezx](skills/send-bridgezx/SKILL.md) | Hay que enviar archivos o directorios concretos a un ZX o Next mediante BridgeZX. | Una transferencia protegida con la IP explícita o la última conocida, destino opcional y el orden pedido. |
| [develop-z80](skills/develop-z80/SKILL.md) | Una iniciativa de producto explícita o un dosier SDD existente, no arreglos rutinarios. | Concepto, especificación, plan, backlog, implementación y evidencia por criterio de aceptación. |
| [document-z80](skills/document-z80/SKILL.md) | Hay que crear, reestructurar, revisar o sincronizar EN/ES la documentación pública de un proyecto. | Un README y una jerarquía de documentación basados en evidencia, con órdenes y requisitos de hardware verificados. |
| [port-spectranext](skills/port-spectranext/SKILL.md) | Un programa ZX existente se está portando al cartucho Spectranext (no al Spectrum Next). | Entrada canónica, implementación acotada, puertas ligadas a artefactos, evidencia física y entrega. |
| [debug-z80](skills/debug-z80/SKILL.md) | Observas un fallo y su causa es desconocida. | Una explicación causal falsable y, si se pide, una corrección verificada de la causa raíz. |
| [audit-z80](skills/audit-z80/SKILL.md) | Quieres una revisión preventiva o amplia de corrección, o el riesgo de un conjunto de cambios (modo `diff`). | Hallazgos de solo lectura ordenados por gravedad y confianza, con evidencia y riesgo residual. |
| [organize-z80](skills/organize-z80/SKILL.md) | Hay que mapear o cambiar con seguridad la propiedad, las dependencias, la estructura de fuentes o la ubicación en runtime. | Un mapa proporcional, un diseño, un tramo de migración reversible o una decisión explícita de no cambiar. |
| [shrink-z80](skills/shrink-z80/SKILL.md) | Hay que reducir almacenamiento, tamaño enlazado, memoria residente, BSS/pila, bancos u overlays. | Reducciones netas clasificadas por seguridad y calidad de la evidencia. |
| [optimize-z80](skills/optimize-z80/SKILL.md) | Compiten varios objetivos: tamaño, velocidad, RAM, renderizado, latencia. | Hasta tres experimentos priorizados con impacto, riesgo, reversión y validación. |

## Uso

Describe el objetivo, la meta y los artefactos disponibles; cuanto más concreta
sea la petición, mejor será la priorización. Los ejemplos nombran el skill en
la frase. En Codex puedes anteponer `$` y en Claude Code invocarlo como
`/nombre`.

### Workflow adaptativo

```text
Usa workflow en modo auto para implementar este cambio con el nivel de
ejecución mínimo suficiente y conservar los contratos existentes del repositorio.
```

### Selección de dominio Z80

```text
Usa route-z80 para elegir el único especialista relevante para esta petición
sobre el repositorio Z80, o workflow si no hace falta ningún contrato de
evidencia especializado.
```

### Envío mediante BridgeZX

```text
Usa send-bridgezx para enviar build/game.nex a mi Spectrum Next con la última
IP conocida de BridgeZX, en GAMES/DEMO.
```

### Documentación del repositorio

```text
Usa document-z80 para reestructurar el README de este proyecto como página de
entrada, verificar cada afirmación sobre build y hardware y mantener alineados
los archivos en inglés y español sin perder la voz del proyecto.
```

### Desarrollo dirigido por especificaciones

```text
Usa develop-z80 para llevar esta idea de juego para ZX Spectrum Next desde el
concepto hasta una implementación verificada. Elige y ejecuta tú las etapas
SDD; pregunta solo si falta una decisión de producto material.
```

### Port al cartucho Spectranext

```text
Usa port-spectranext para retomar el port de este programa ZX existente al
cartucho Spectranext. Empieza por la puerta canónica de petición de port,
conserva la frontera del consumidor y detente cuando haga falta evidencia de
hardware real.
```

### Depuración de causa raíz

```text
Usa debug-z80 para aislar por qué este build de 128K se cuelga al volver de la
ISR. No edites hasta que una comprobación discriminante identifique al
responsable causal; después aplica y verifica la corrección mínima.
```

### Auditoría

```text
Usa audit-z80 en modo auto para revisar este proyecto mixto ASM/C.
Prioriza ABI, ISR y memoria; informa solo de hallazgos anclados en el código actual.
```

```text
Usa audit-z80 en modo diff contra main. Comprueba si los cambios de ISR y C/ASM
de esta rama rompen la ABI, los registros preservados, el estado compartido o
el mapa de memoria.
```

### Organización

```text
Usa organize-z80 en modo design para mapear la propiedad, las dependencias y la
ubicación en este proyecto mixto ASM/C, y propón solo el cambio de frontera
mínimo justificado.
```

```text
Usa organize-z80 en modo apply para ejecutar solo esta fase aprobada; conserva
el alcance de los símbolos, los mapas, la ABI y el punto de reversión existente.
```

### Reducción de tamaño

```text
Usa shrink-z80 en modo scan. Necesito recuperar al menos 512 bytes de CODE/DATA
sin cambiar el comportamiento, y separar los ahorros exactos de los estimados.
```

```text
Usa shrink-z80 en modo compress para comparar el tamaño neto y la RAM máxima
de los códecs aplicados a estos assets concretos.
```

### Optimización multiobjetivo

```text
Usa optimize-z80 en modo Triage para identificar el cuello de botella real y
devolver los tres experimentos con mejor equilibrio entre impacto, riesgo y coste.
```

```text
Usa optimize-z80 en modo Measurement para obtener una línea base actualizada
sin modificar mi árbol de trabajo principal.
```

## Cómo funciona

### Evidencia local antes que folklore

- Solo el código actual y los artefactos cuya actualidad esté demostrada pueden
  confirmar un hallazgo o una mejora.
- Mapas, símbolos, listados, ASM generado y binarios enlazados cuentan como
  evidencia solo cuando corresponden a la misma revisión, configuración y
  target.
- Escáneres, agentes, conocimiento previo, foros y otros repositorios generan
  candidatos; no sustituyen la verificación local.
- Un artefacto obsoleto rebaja la confianza de forma explícita, a estados como
  `NEEDS BUILD`, `REQUIERE BUILD` o `SPECULATIVE`.
- En proyectos con varios targets, una propuesta solo se promueve cuando cada
  target cumple sus propios límites.

### Carga progresiva

Cada `SKILL.md` es un despachador compacto. El host carga primero el contrato
compartido y después solo las referencias y scripts relevantes para el
problema observado. Manuales, catálogos de técnicas y logs quedan fuera del
contexto salvo que puedan cambiar el resultado.

### Herramientas deterministas

Los skills incluyen analizadores en Python, casi todos solo con la biblioteca
estándar. Perfilan el proyecto, resumen mapas, detectan patrones, inventarían
fronteras ABI, comprueban la actualidad de los artefactos, localizan las
dependencias de biblioteca, estiman T-states y puntúan candidatos. Su
resultado es una señal reproducible, no un veredicto automático.

### Ejecución adaptativa y multiagente

El skill independiente `workflow` es el núcleo de ejecución compartido:

| Nivel | Estrategia |
|---|---|
| **Light** | El hilo principal resuelve directamente una tarea acotada. |
| **Medium** | El hilo principal resuelve directamente un único flujo ordenado de varios pasos. |
| **Heavy** | El hilo principal coordina workers independientes y acotados en una topología plana. |

En `auto`, cada skill Z80 clasifica la demanda como `Focused`, `Standard` o
`Deep` tras el preflight. Workflow decide la ruta, el despacho, la reparación,
la verificación y la integración. El skill de dominio conserva sus puertas de
evidencia, sus líneas de trabajo, su contrato de salida y sus restricciones de
escritura. Un nivel explícito de workflow prevalece, pero nunca autoriza una
operación que el proyecto o el skill de dominio prohíban. Antes de despachar,
workflow clasifica cada superficie como de solo lectura en el árbol principal,
solo en worktree desechable o con mutación autorizada del árbol principal, y
elige solo los roles que encajan.

Las instrucciones explícitas del usuario prevalecen sobre los valores por
defecto de los skills dentro de su alcance; las restricciones del proyecto, los
requisitos de evidencia y los límites del runtime siguen vigentes. Cuando un
skill se detiene, nombra la regla exacta según la
[política de autorización](skills/workflow/references/authorization.md)
compartida.

La delegación Heavy asigna los mismos roles (investigador, implementador,
verificador) en cada host. La [política de roles](skills/workflow/references/roles.md)
canónica contiene el mapeo por host:

- **Codex:** los subagentes usan por defecto Sol 6.1 con el esfuerzo de
  razonamiento de cada encargo. Astra Medium se usa solo si el usuario lo pide
  explícitamente para un análisis causal difícil o de alto riesgo concreto
  ([reglas de activación](skills/workflow/references/roles.md#explicit-astra-medium-opt-in)).
- **Claude Code:** la herramienta `Agent` con subagentes `Explore` o
  `general-purpose` y un modelo `opus` o `sonnet` explícito; el host no expone
  un parámetro de esfuerzo de razonamiento.
- **Gemini / Antigravity:** `invoke_subagent` con tipos `research` o `self` y
  el nivel de modelo heredado.

El host debe admitir y aplicar los ajustes solicitados; un skill no es un
control de gasto del runtime.

### Investigación externa dirigida

La investigación externa resuelve una incertidumbre concreta; no sirve para
adornar el informe ni para repetir una lista de sitios conocidos.

Se activa cuando:

- El usuario pide una investigación profunda en foros, blogs, repositorios o la
  demoscene.
- Una versión del compilador, ABI, firmware, emulador, modelo de hardware o
  detalle de timing puede cambiar un hallazgo principal.
- El código, los artefactos generados y la documentación se contradicen.
- Un análisis profundo mantiene un punto ciego material.
- Una secuencia de instrucciones, helper, códec, renderizador, cargador o
  esquema de bancos requiere arqueología de código.

Cómo busca:

1. Formula una pregunta a partir de una firma local mínima: opcode, símbolo,
   fragmento emitido, versión, dirección, síntoma o restricción.
2. Busca fragmentos exactos y conceptos con terminología alternativa.
3. Amplía los términos al inglés, español, polaco, ruso, checo y otras
   comunidades regionales relevantes.
4. Diversifica las fuentes: código, tests, commits, issues, forks, emuladores,
   mediciones de hardware, listas de correo, foros archivados, blogs
   personales, repositorios pequeños, desensamblados, generadores y material de
   la demoscene.
5. Sigue a autores, citas, forks, issues relacionadas y enlaces archivados.
6. Intenta refutar cada finalista: busca bugs, regresiones, issues cerradas o
   rechazadas y fallos específicos de un modelo.
7. Comprueba CPU, modelo de Spectrum, ABI, interrupciones, paginación, memoria,
   toolchain y timing antes de trasladar una técnica.

La investigación tiene presupuesto y reglas de parada, y conserva solo las
pocas fuentes que pueden cambiar una decisión. Una técnica popular sin un
ancla local sigue siendo una hipótesis. Las búsquedas usan solo firmas mínimas
normalizadas y nunca suben código privado ni identificadores del proyecto.

## Opcional: shrink-agent

[`tools/shrink-agent`](tools/shrink-agent/README.md) es la contrapartida
aplicadora de `shrink-z80`, que es de solo lectura. Es un bucle desatendido
para proyectos z88dk. Propone una reducción de tamaño por rutina mediante la
API de Claude, recompila todos los targets y conserva un cambio solo si todos
compilan, el tamaño total baja, pasan los tests configurados y una revisión
independiente por modelo lo acepta. Trabaja en una rama de worktree
desechable, hace un commit por rutina y nunca fusiona ni hace push.

Necesita Python 3.11 o posterior, su propio entorno virtual
(`tools/shrink-agent/install.py`) y una clave de API de Anthropic. Cada
ejecución cuesta dinero y está limitada por `--max-usd`, 2 USD por defecto. En
Claude Code, `/shrink-z80 agent` ejecuta primero el censo y pregunta antes de
lanzarlo. Su README describe la configuración, los resultados y los límites.

## Artefactos recomendados

Los skills pueden empezar solo con los fuentes; estos artefactos aumentan la
confianza:

| Evidencia | Utilidad |
|---|---|
| `.asm`, `.s`, `.c`, `.h` | Semántica actual, fronteras ABI, patrones y alcanzabilidad. |
| `.map`, `.sym` | Disposición, símbolos, secciones, bancos, dependencias de biblioteca y hueco de pila. |
| `.lst` o ASM generado | Comportamiento real del compilador y coste de la generación de código. |
| Binarios, archivos TAP y assets | Tamaño final, compresión y comparaciones reproducibles. |
| Receta de build y flags | Reproducibilidad, toolchain, ABI y configuración. |
| Targets y límites explícitos | Vetos, reservas, compatibilidad y ordenación correcta. |

Una marca de tiempo reciente no demuestra por sí sola la correspondencia. La
revisión, la configuración y la receta deben pertenecer a la misma línea base.

## Seguridad y límites

- Los análisis normales son de solo lectura.
- `workflow` nunca amplía los permisos concedidos por un proyecto o un skill de
  dominio.
- `develop-z80` mantiene en solo lectura la idea, la especificación, la
  planificación y el desglose de tareas; su primera edición de código de un
  producto nuevo exige además la aceptación explícita de la especificación.
  Cualquier avance automático entre hitos se limita a la sesión actual.
- `port-spectranext` mantiene como autoridad el checkout externo de
  Spectranext y aísla el estado del consumidor. Las ediciones de fuentes quedan
  dentro de la frontera autorizada del consumidor, y los resultados físicos
  requieren la observación explícita del usuario.
- `debug-z80` mantiene el diagnóstico y las reparaciones candidatas en un
  worktree desechable. Solo edita el árbol principal para una reparación
  solicitada y respaldada causalmente.
- `document-z80` edita solo la documentación pública para personas dentro del
  alcance. No cambia código, configuración de build, releases ni instrucciones
  para agentes.
- `audit-z80` y `shrink-z80` no editan el proyecto. `shrink-agent` solo hace
  commits en su propia rama desechable.
- `organize-z80` edita fuentes solo en modo `apply`, tras una petición
  explícita, una línea base congelada, una frontera aprobada, un tramo con
  nombre y un punto de reversión. Una actualización del mapa persistente pedida
  explícitamente solo puede editar ese documento y su puntero de enrutado.
- `optimize-z80` modifica solo una copia desechable en modo `Experiment` y
  requiere aprobación explícita.
- `send-bridgezx` envía solo las fuentes indicadas a la máquina seleccionada y
  nunca reintenta una transferencia dudosa.
- Los analizadores incluidos trabajan con archivos locales y no acceden a la
  red. Los tests escriben en directorios temporales y los eliminan al terminar.
- No es un compilador, un profiler de hardware ni un optimizador automático. No
  confirma ahorros enlazados, timings ni compatibilidad sin la evidencia
  adecuada.
- SMC, abuso de SP, `DI`/`EI`, opcodes no documentados, comportamiento del
  floating bus y otras técnicas dependientes del hardware requieren etiquetas
  de riesgo y validación específica por target.
- La investigación externa nunca debe publicar código privado, rutas, símbolos
  sensibles ni identificadores del proyecto.

## Estructura del repositorio

- `skills/<nombre>/`: `SKILL.md`, metadatos del agente, referencias y
  analizadores.
- `scripts/`: instaladores por host, el runner de worktrees desechables, el
  validador de skills y los tests del repositorio.
- `tools/shrink-agent/`: la herramienta opcional de reducción de tamaño
  desatendida.
- `evals/`: casos de enrutado, evidencia y política con sus fixtures; los
  resultados generados se ignoran.
- `agent_docs/`: contexto del proyecto mantenido para agentes.
- `.codex-plugin/plugin.json`, `plugin.json`, `gemini-extension.json`:
  manifiestos de host con una única versión compartida.

Consulta el [mapa del repositorio](agent_docs/project_structure.md) para la
propiedad de los archivos y [CHANGELOG.md](CHANGELOG.md) para los cambios.

## Desarrollo y validación

Prepara las dependencias del validador y de los tests en un entorno virtual:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r scripts/requirements-validation.txt pytest
```

En Windows PowerShell, actívalo con `.venv\Scripts\Activate.ps1` y usa `python`
en lugar de `python3`.

Valida los skills y ejecuta los tests desde la raíz del repositorio:

```sh
python3 scripts/validate_skills.py
python3 -m pytest -q
python3 skills/audit-z80/scripts/smoke_test.py
python3 skills/shrink-z80/tests/run_smoke.py
```

`validate_skills.py` comprueba los once skills, o uno si le pasas su carpeta,
sin reescribir `SKILL.md` ni `agents/openai.yaml`. No establece el
comportamiento en runtime ni la activación. `pytest` recoge los tests de
`scripts/`, `optimize-z80`, `send-bridgezx` y `shrink-agent`. Los dos scripts
smoke se ejecutan aparte. Valida los manifiestos y el front matter de cada
skill antes de publicar una versión nueva.

### Evals de comportamiento (solo Codex)

Las evals de comportamiento están separadas de los tests unitarios y usan la
CLI de Codex. Comprueba los datasets sin modelo:

```sh
python3 scripts/run_behavior_evals.py --dry-run
```

Tras instalar la versión del plugin indicada en `.codex-plugin/plugin.json`,
ejecuta las suites de enrutado y de evidencia en sesiones nuevas de Codex de
solo lectura:

```sh
python3 scripts/run_behavior_evals.py --suite evals/routing.jsonl
python3 scripts/run_behavior_evals.py --suite evals/evidence.jsonl
```

El runner rechaza un plugin instalado obsoleto salvo que se fuerce. Registra
precisión y exhaustividad por ruta y escribe resultados JSON y trazas por caso,
ignorados por Git, en `evals/results/`. Usa `--model` y `--reasoning-effort`
para que la comparación sea explícita, y mantén fijos casos, fixtures, modelo y
esfuerzo al comparar revisiones de los skills. Los resultados separan los
ajustes solicitados de los datos confirmados por el runtime, registran el uso
de tokens y las acciones observadas, y comparan los archivos del fixture antes
y después de cada caso. Los efectos secundarios no observados siguen siendo
desconocidos, y las trazas pueden contener contenido de fixtures y rutas
locales, así que revísalas antes de compartirlas. `evals/baseline.json`
conserva solo resultados históricos; no demuestra que una versión posterior
pase.

La suite opcional `evals/policy.jsonl` comprueba decisiones sobre activación de
modelos, autorización, lecturas selectivas y reutilización. Sus escenarios solo
piden decisiones, sin llamadas delegadas, builds, ediciones ni transferencias.
Una ejecución real usa inferencia de pago y prueba la interpretación de la
política, no su aplicación en runtime. Consulta la
[evaluación de políticas](evals/POLICY.md). Comprueba su dataset localmente
con:

```sh
python3 scripts/run_behavior_evals.py --suite evals/policy.jsonl --dry-run
```

## Licencia

Este proyecto se distribuye bajo la [licencia MIT](LICENSE).

Copyright © 2026 M. Ignacio Monge García.

## Autor

M. Ignacio Monge García
