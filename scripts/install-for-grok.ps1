#Requires -Version 5.1
<#
.SYNOPSIS
  Install z80-skills into Grok Build (~/.grok/skills) with Grok runtime adaptations.

.DESCRIPTION
  Canonical skill sources remain under ./skills (Codex/plugin layout).
  This script:
    1. Copies the seven Grok-compatible skills into ~/.grok/skills (repo = canonical on name conflict)
    2. Copies run_in_worktree.py into each skill that needs disposable worktrees
    3. Rewrites ../../scripts/run_in_worktree.py paths for the flat Grok layout
    4. Derives Grok workflow adaptations from the canonical workflow sources
    5. Patches domain SKILL.md Runtime Portability notes for Grok Build

  Does NOT modify ./skills sources.

.PARAMETER Dest
  Destination skills root. Default: $HOME/.grok/skills

.PARAMETER SyncClaude
  Also install pure (unadapted) skill trees into ~/.claude/skills for parity.

.PARAMETER SkipBackup
  Do not backup existing destination skills before overwrite.

.EXAMPLE
  .\scripts\install-for-grok.ps1

.EXAMPLE
  git pull --ff-only; .\scripts\install-for-grok.ps1 -SyncClaude
#>
[CmdletBinding()]
param(
    [string]$Dest = (Join-Path $HOME ".grok\skills"),
    [switch]$SyncClaude,
    [switch]$SkipBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SkillsSrc = Join-Path $RepoRoot "skills"
$SharedScript = Join-Path $RepoRoot "scripts\run_in_worktree.py"

$SkillNames = @(
    "audit-z80",
    "debug-z80",
    "develop-z80",
    "optimize-z80",
    "organize-z80",
    "shrink-z80",
    "workflow"
)

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Path([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing $Label`: $Path"
    }
}

function Backup-Skill([string]$SkillDir, [string]$ArchiveRoot) {
    if (-not (Test-Path -LiteralPath $SkillDir)) { return }
    $name = Split-Path $SkillDir -Leaf
    $target = Join-Path $ArchiveRoot $name
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    Copy-Item -LiteralPath $SkillDir -Destination $target -Recurse -Force
    Write-Host "    backup: $name"
}

function Copy-SkillTree([string]$Name, [string]$DestRoot) {
    $src = Join-Path $SkillsSrc $Name
    $dst = Join-Path $DestRoot $Name
    Assert-Path $src "skill source $Name"
    if (Test-Path -LiteralPath $dst) {
        Remove-Item -LiteralPath $dst -Recurse -Force
    }
    Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
    Write-Host "    installed: $Name"
}

function Copy-RunInWorktree([string]$DestRoot) {
    Assert-Path $SharedScript "run_in_worktree.py"
    foreach ($name in @("audit-z80", "debug-z80", "develop-z80", "optimize-z80", "shrink-z80")) {
        $scripts = Join-Path $DestRoot "$name\scripts"
        if (-not (Test-Path -LiteralPath $scripts)) {
            New-Item -ItemType Directory -Path $scripts -Force | Out-Null
        }
        Copy-Item -LiteralPath $SharedScript -Destination (Join-Path $scripts "run_in_worktree.py") -Force
    }
    $shared = Join-Path $DestRoot "_z80-shared\scripts"
    New-Item -ItemType Directory -Path $shared -Force | Out-Null
    Copy-Item -LiteralPath $SharedScript -Destination (Join-Path $shared "run_in_worktree.py") -Force
}

function Patch-WorktreePaths([string]$DestRoot) {
    $mdFiles = Get-ChildItem -LiteralPath $DestRoot -Recurse -Filter "*.md" -File |
        Where-Object {
            $_.FullName -notmatch '[\\/]_backup' -and
            $_.FullName -notmatch '[\\/]skill-archives' -and
            $_.FullName -notmatch '[\\/]_z80-shared'
        }
    foreach ($file in $mdFiles) {
        # Only touch files under the seven skill trees we just installed
        $rel = $file.FullName.Substring($DestRoot.Length).TrimStart('\', '/')
        $top = ($rel -split '[\\/]')[0]
        if ($SkillNames -notcontains $top) { continue }

        $text = [System.IO.File]::ReadAllText($file.FullName)
        $orig = $text
        $text = $text.Replace('<skill-dir>/../../scripts/run_in_worktree.py', '`$SKILL_DIR/scripts/run_in_worktree.py')
        $text = $text.Replace('$SKILL_DIR/../../scripts/run_in_worktree.py', '$SKILL_DIR/scripts/run_in_worktree.py')
        $text = $text.Replace('../../scripts/run_in_worktree.py', '$SKILL_DIR/scripts/run_in_worktree.py')
        # Fix accidental double-backtick forms from prior partial patches
        $text = $text.Replace('``$SKILL_DIR/scripts/run_in_worktree.py`', '`$SKILL_DIR/scripts/run_in_worktree.py`')
        $text = $text.Replace('``$SKILL_DIR/scripts/run_in_worktree.py', '`$SKILL_DIR/scripts/run_in_worktree.py')
        if ($text -ne $orig) {
            [System.IO.File]::WriteAllText($file.FullName, $text)
            Write-Host "    path-fix: $rel"
        }
    }
}

function Set-TextFile([string]$Path, [string]$Text) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Patch-WorkflowForGrok([string]$DestRoot) {
    $workflow = Join-Path $DestRoot "workflow"
    $skillPath = Join-Path $workflow "SKILL.md"
    $rolesPath = Join-Path $workflow "references\roles.md"
    $heavyPath = Join-Path $workflow "references\heavy.md"
    foreach ($path in @($skillPath, $rolesPath, $heavyPath)) {
        Assert-Path $path "canonical workflow input"
    }

    $skill = [System.IO.File]::ReadAllText($skillPath)
    $nl = if ($skill.Contains("`r`n")) { "`r`n" } else { "`n" }
    if ($skill -notmatch '(?m)^## Host runtime \(Grok Build\)$') {
        $hostSection = @(
            '## Host runtime (Grok Build)',
            '',
            '- Spawn workers with `spawn_subagent`; use the mappings in `references/roles.md`.',
            '- Prefer lean-ctx tools for read, search, and shell work when available.',
            '- On Windows, invoke `python` or the interpreter named by the user; do not',
            '  hardcode `python3` paths.',
            '- Domain Z80 skills and `workflow` live as siblings under `~/.grok/skills/`.'
        ) -join $nl
        $skill = $skill.Replace('## Select effort', "$hostSection$nl$nl## Select effort")
    }
    $portableTypes = @(
        'Use only documented built-in `worker`, `explorer`, or `default` types.',
        'Task names identify workflow roles; they are not external custom-agent profiles.'
    ) -join $nl
    $grokTypes = @(
        'Use only the Grok host mappings documented in `references/roles.md`.',
        'Task labels identify workflow roles; they are not external custom-agent profiles.'
    ) -join $nl
    $skill = $skill.Replace($portableTypes, $grokTypes)
    Set-TextFile -Path $skillPath -Text $skill

    $roles = [System.IO.File]::ReadAllText($rolesPath)
    $nl = if ($roles.Contains("`r`n")) { "`r`n" } else { "`n" }
    $rolesPrefix = @(
        '# Portable Agent Roles (Grok Build)',
        '',
        'Use Grok''s `spawn_subagent` tool. Role behavior comes from the',
        'self-contained task capsule, not from custom profiles.',
        '',
        '| Workflow role | Task label | `subagent_type` | `capability_mode` | Isolation |',
        '| --- | --- | --- | --- | --- |',
        '| Investigator | `explorer` | `explore` | `read-only` | `none` |',
        '| Implementer | `executor` | `general-purpose` | `read-write` or `all` | boundary-dependent |',
        '| Verifier | `verifier` | `general-purpose` | `read-only` or `execute` | `none` |',
        '| Exceptional implementer | `sol_executor` | `general-purpose` | `all` | boundary-dependent |',
        '',
        '## Spawn rules (Grok)',
        '',
        '- Call `spawn_subagent` with a fresh, self-contained task capsule.',
        '- Put the workflow role in `description`; prefer `background: true` and collect',
        '  results with `get_command_or_subagent_output`.',
        '- Do not pass `model` unless the user explicitly requested one.',
        '- Map Codex `explorer` to `explore`, and `worker` or `default` to',
        '  `general-purpose`. A fresh spawn replaces `fork_turns="none"`.',
        '- For disposable-worktree-only mutation, require `isolation="worktree"` or',
        '  another verified disposable worktree.'
    ) -join $nl
    $roles = [regex]::Replace(
        $roles,
        '(?s)\A# Portable Agent Roles.*?\r?\n## Capsule contracts',
        "$rolesPrefix$nl$nl## Capsule contracts",
        1
    )
    Set-TextFile -Path $rolesPath -Text $roles

    $heavy = [System.IO.File]::ReadAllText($heavyPath)
    $nl = if ($heavy.Contains("`r`n")) { "`r`n" } else { "`n" }
    $oldReadOnly = @(
        '- **primary-tree read-only:** use only `explorer` or read-only `default` roles;',
        '  do not spawn `executor` or `sol_executor` for that surface.'
    ) -join $nl
    $newReadOnly = @(
        '- **primary-tree read-only:** use only `explore` or read-only `general-purpose` roles;',
        '  do not spawn `executor` or `sol_executor` for that surface.'
    ) -join $nl
    $heavy = $heavy.Replace($oldReadOnly, $newReadOnly)
    $oldRoles = @(
        '- `explorer`: built-in `explorer`, read-only investigation.',
        '- `executor`: built-in `worker`, default implementation.',
        '- `verifier`: built-in `default`, independent verification and failure analysis.',
        '- `sol_executor`: built-in `worker`, exceptional implementation only when the',
        '  normal implementer cannot reasonably own the package; at most one.'
    ) -join $nl
    $newRoles = @(
        '- `explorer`: `explore`, read-only investigation.',
        '- `executor`: write-capable `general-purpose`, default implementation.',
        '- `verifier`: read-only or execute-only `general-purpose`, independent verification.',
        '- `sol_executor`: full-capability `general-purpose`, exceptional implementation only',
        '  when the normal implementer cannot reasonably own the package; at most one.'
    ) -join $nl
    $heavy = $heavy.Replace($oldRoles, $newRoles)
    $oldSpawn = @(
        '3. Spawn each worker with `fork_turns="none"` and a self-contained capsule of',
        '   at most 400 words.'
    ) -join $nl
    $newSpawn = @(
        '3. Spawn each worker through `spawn_subagent` with a fresh, self-contained',
        '   capsule of at most 400 words.'
    ) -join $nl
    $heavy = $heavy.Replace($oldSpawn, $newSpawn)
    Set-TextFile -Path $heavyPath -Text $heavy

    Write-Host "    workflow adapted from canonical sources"
}

function Patch-SkillMarkdown([string]$SkillMd) {
    if (-not (Test-Path -LiteralPath $SkillMd)) { return }
    $name = Split-Path (Split-Path $SkillMd -Parent) -Leaf
    $text = [System.IO.File]::ReadAllText($SkillMd)
    $orig = $text

    # 1) Sibling workflow path (idempotent)
    $needle = 'Apply the sibling `$workflow` skill at `../workflow/SKILL.md` as the execution'
    $replacement = @(
        'Apply the sibling `$workflow` skill at `../workflow/SKILL.md` (or'
        '`~/.grok/skills/workflow/SKILL.md` on Grok Build) as the execution'
    ) -join "`r`n"
    if ($text.Contains($needle) -and -not $text.Contains('~/.grok/skills/workflow/SKILL.md')) {
        $text = $text.Replace($needle, $replacement)
    }

    # 2) Windows python note inside Runtime Portability (idempotent)
    if ($text -notmatch 'prefer `python` when `python3`') {
        $text = $text.Replace(
            'never assume a platform-specific path.',
            "never assume a platform-specific path. On Windows hosts, prefer`r`n  ``python`` when ``python3`` is not on ``PATH``."
        )
        $text = $text.Replace(
            'never assume a Windows, macOS, or Linux path.',
            "never assume a Windows, macOS, or Linux path. On Windows hosts,`r`n  prefer ``python`` when ``python3`` is not on ``PATH``."
        )
    }

    # 3) Grok bullets (skip if already adapted — require the bullet form, not the path hint)
    if ($text -notmatch '(?m)^- On Grok Build') {
        $bullets = switch ($name) {
            'optimize-z80' {
                @(
                    '- On Grok Build, `spawn_subagent` with `isolation="worktree"` is an equivalent'
                    '  disposable sandbox when preferred.'
                    '- On Grok Build: load sibling `$workflow` from `~/.grok/skills/workflow/SKILL.md`'
                    '  when needed; prefer lean-ctx tools for read/search/shell.'
                ) -join "`r`n"
            }
            'develop-z80' {
                @(
                    '- On Grok Build: prefer lean-ctx for read/search/shell; Medium/Heavy agents use'
                    '  `spawn_subagent` per `$workflow`. On Windows, prefer `python` when `python3`'
                    '  is missing. Disposable spikes may use `isolation="worktree"` or'
                    '  `"$SKILL_DIR/scripts/run_in_worktree.py"`.'
                ) -join "`r`n"
            }
            'organize-z80' {
                @(
                    '- On Grok Build: prefer lean-ctx for read/search/shell; Medium/Heavy agents use'
                    '  `spawn_subagent` per `$workflow`. On Windows, prefer `python` when `python3`'
                    '  is missing.'
                ) -join "`r`n"
            }
            default {
                @(
                    '- On Grok Build: load sibling `$workflow` from `~/.grok/skills/workflow/SKILL.md`'
                    '  when needed; prefer lean-ctx tools for read/search/shell; Medium/Heavy agents use'
                    '  `spawn_subagent` per the workflow skill.'
                ) -join "`r`n"
            }
        }

        if ($text -match '(?m)^## Runtime Portability\s*$') {
            $text = [regex]::Replace(
                $text,
                '(?ms)(## Runtime Portability\r?\n)(.*?)(\r?\n## )',
                {
                    param($m)
                    $body = $m.Groups[2].Value.TrimEnd()
                    return $m.Groups[1].Value + $body + "`r`n" + $bullets + $m.Groups[3].Value
                },
                1
            )
        }
        else {
            $insert = "`r`n## Runtime Portability`r`n`r`n$bullets`r`n"
            $text = [regex]::Replace(
                $text,
                '(?ms)(## Workflow Core\r?\n.*?)(\r?\n## )',
                { param($m) $m.Groups[1].Value.TrimEnd() + $insert + $m.Groups[2].Value },
                1
            )
        }
    }

    # 4) optimize-z80 worktree helper line (flat layout)
    if ($name -eq 'optimize-z80') {
        $text = $text.Replace(
            'disposable worktree through `$SKILL_DIR/../../scripts/run_in_worktree.py`.',
            'disposable worktree through `"$SKILL_DIR/scripts/run_in_worktree.py"`.'
        )
        $text = $text.Replace(
            'disposable worktree through $SKILL_DIR/../../scripts/run_in_worktree.py.',
            'disposable worktree through `"$SKILL_DIR/scripts/run_in_worktree.py"`.'
        )
    }

    if ($text -ne $orig) {
        Set-TextFile -Path $SkillMd -Text $text
        Write-Host "    portability: $name"
    }
}

function Patch-DomainPortability([string]$DestRoot) {
    foreach ($name in @("audit-z80", "debug-z80", "develop-z80", "optimize-z80", "organize-z80", "shrink-z80")) {
        Patch-SkillMarkdown -SkillMd (Join-Path $DestRoot "$name\SKILL.md")
    }
}

function Sync-ClaudeSkills {
    $claude = Join-Path $HOME ".claude\skills"
    New-Item -ItemType Directory -Path $claude -Force | Out-Null
    Write-Step "Syncing pure (unadapted) skills to $claude"
    foreach ($name in $SkillNames) {
        Copy-SkillTree -Name $name -DestRoot $claude
    }
    Write-Host "    Claude copies are upstream layout (no Grok overlay)."
}

# --- main ---
Write-Step "z80-skills → Grok Build installer"
Write-Host "    repo: $RepoRoot"
Write-Host "    dest: $Dest"

Assert-Path $SkillsSrc "skills/"
Assert-Path $SharedScript "scripts/run_in_worktree.py"

New-Item -ItemType Directory -Path $Dest -Force | Out-Null

if (-not $SkipBackup) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $HOME ".grok\skill-archives\z80-pre-install-$stamp"
    New-Item -ItemType Directory -Path $archive -Force | Out-Null
    Write-Step "Backing up existing skills to $archive"
    foreach ($name in $SkillNames) {
        Backup-Skill -SkillDir (Join-Path $Dest $name) -ArchiveRoot $archive
    }
}

Write-Step "Installing skill trees from repo"
foreach ($name in $SkillNames) {
    Copy-SkillTree -Name $name -DestRoot $Dest
}

Write-Step "Bundling run_in_worktree.py into skill scripts/"
Copy-RunInWorktree -DestRoot $Dest

Write-Step "Rewriting worktree script paths for flat Grok layout"
Patch-WorktreePaths -DestRoot $Dest

Write-Step "Adapting canonical workflow for Grok"
Patch-WorkflowForGrok -DestRoot $Dest

Write-Step "Patching domain Runtime Portability for Grok"
Patch-DomainPortability -DestRoot $Dest

if ($SyncClaude) {
    Sync-ClaudeSkills
}

Write-Step "Verify"
foreach ($name in $SkillNames) {
    $skill = Join-Path $Dest "$name\SKILL.md"
    Assert-Path $skill "$name/SKILL.md"
    $line = (Select-String -Path $skill -Pattern '^description:' | Select-Object -First 1).Line
    $clip = if ($line.Length -gt 72) { $line.Substring(0, 72) + "..." } else { $line }
    Write-Host ("    {0,-14} {1}" -f $name, $clip)
}
$wf = Join-Path $Dest "workflow\SKILL.md"
if (-not (Select-String -Path $wf -Pattern 'Host runtime \(Grok Build\)' -Quiet)) {
    throw "Workflow adaptation missing Grok host section — install incomplete"
}
$workflowChecks = @(
    @{ Path = $wf; Pattern = 'Do not duplicate delegated discovery' },
    @{ Path = (Join-Path $Dest "workflow\references\heavy.md"); Pattern = '## Direct repair loop' },
    @{ Path = (Join-Path $Dest "workflow\references\roles.md"); Pattern = 'within 250 words' }
)
foreach ($check in $workflowChecks) {
    if (-not (Select-String -LiteralPath $check.Path -Pattern $check.Pattern -SimpleMatch -Quiet)) {
        throw "Canonical workflow contract missing after Grok adaptation: $($check.Pattern)"
    }
}
$wt = Join-Path $Dest "optimize-z80\scripts\run_in_worktree.py"
Assert-Path $wt "optimize-z80/scripts/run_in_worktree.py"
$debugWt = Join-Path $Dest "debug-z80\scripts\run_in_worktree.py"
Assert-Path $debugWt "debug-z80/scripts/run_in_worktree.py"

Write-Host ""
Write-Host "Done. Open a new Grok task (or wait for skill auto-reload) and use:" -ForegroundColor Green
Write-Host "  /debug-z80  /audit-z80  /shrink-z80  /optimize-z80  /develop-z80  /organize-z80  /workflow"
Write-Host ""
Write-Host "Update loop:"
Write-Host "  cd $RepoRoot"
Write-Host "  git pull --ff-only"
Write-Host "  .\scripts\install-for-grok.ps1"
