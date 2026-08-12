#Requires -Version 5.1
<#
.SYNOPSIS
  Install z80-skills into Grok Build (~/.grok/skills) with Grok runtime adaptations.

.DESCRIPTION
  Canonical skill sources remain under ./skills (Codex/plugin layout).
  This script:
    1. Copies the six skills into ~/.grok/skills (repo = canonical on name conflict)
    2. Copies run_in_worktree.py into each skill that needs disposable worktrees
    3. Rewrites ../../scripts/run_in_worktree.py paths for the flat Grok layout
    4. Applies the Grok workflow overlay (spawn_subagent, lean-ctx, Windows python)
    5. Patches domain SKILL.md Runtime Portability notes for Grok Build

  Does NOT modify ./skills sources. Overlay lives in scripts/grok-overlay/.

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
$OverlayRoot = Join-Path $PSScriptRoot "grok-overlay"
$SharedScript = Join-Path $RepoRoot "scripts\run_in_worktree.py"

$SkillNames = @(
    "audit-z80",
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
    foreach ($name in @("audit-z80", "develop-z80", "optimize-z80", "shrink-z80")) {
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
        # Only touch files under the six skill trees we just installed
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

function Apply-WorkflowOverlay([string]$DestRoot) {
    $overlay = Join-Path $OverlayRoot "workflow"
    Assert-Path (Join-Path $overlay "SKILL.md") "Grok workflow overlay"
    $dst = Join-Path $DestRoot "workflow"
    Copy-Item -LiteralPath (Join-Path $overlay "SKILL.md") -Destination (Join-Path $dst "SKILL.md") -Force
    $refSrc = Join-Path $overlay "references"
    $refDst = Join-Path $dst "references"
    New-Item -ItemType Directory -Path $refDst -Force | Out-Null
    foreach ($name in @("roles.md", "medium.md", "heavy.md")) {
        $from = Join-Path $refSrc $name
        Assert-Path $from "overlay $name"
        Copy-Item -LiteralPath $from -Destination (Join-Path $refDst $name) -Force
    }
    Write-Host "    workflow overlay applied"
}

function Set-TextFile([string]$Path, [string]$Text) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
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
    foreach ($name in @("audit-z80", "develop-z80", "optimize-z80", "organize-z80", "shrink-z80")) {
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
Assert-Path $OverlayRoot "scripts/grok-overlay/"
Assert-Path $SharedScript "scripts/run_in_worktree.py"
Assert-Path (Join-Path $OverlayRoot "workflow\SKILL.md") "grok-overlay/workflow/SKILL.md"

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

Write-Step "Applying Grok workflow overlay"
Apply-WorkflowOverlay -DestRoot $Dest

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
    throw "Workflow overlay missing Grok host section — install incomplete"
}
$wt = Join-Path $Dest "optimize-z80\scripts\run_in_worktree.py"
Assert-Path $wt "optimize-z80/scripts/run_in_worktree.py"

Write-Host ""
Write-Host "Done. Open a new Grok task (or wait for skill auto-reload) and use:" -ForegroundColor Green
Write-Host "  /audit-z80  /shrink-z80  /optimize-z80  /develop-z80  /organize-z80  /workflow"
Write-Host ""
Write-Host "Update loop:"
Write-Host "  cd $RepoRoot"
Write-Host "  git pull --ff-only"
Write-Host "  .\scripts\install-for-grok.ps1"
