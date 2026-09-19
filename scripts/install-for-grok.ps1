#Requires -Version 5.1
<#
.SYNOPSIS
  Point Grok Build at this checkout's canonical skill trees.

.DESCRIPTION
  Canonical skill sources remain under ./skills. Grok Build reads them in
  place through ~/.grok/config.toml [skills].paths.

  This script:
    1. Adds <repo>/skills to Grok's extra skill paths
    2. Removes obsolete copies of the eleven bundled skills from
       ~/.grok/skills (and ~/.claude/skills unless -SkipClaudeCleanup)
    3. Leaves unrelated personal skills untouched

  It does not copy, patch, or overlay skill trees into ~/.grok/skills.

.PARAMETER GrokConfig
  Grok config.toml to update. Default: $HOME/.grok/config.toml

.PARAMETER Dest
  Grok user skills directory to clean of bundled copies.
  Default: $HOME/.grok/skills

.PARAMETER ClaudeSkills
  Claude user skills directory to clean of bundled copies.
  Default: $HOME/.claude/skills

.PARAMETER SkipClaudeCleanup
  Do not remove copies under the Claude skills directory.

.PARAMETER SkipBackup
  Accepted for compatibility. Copies are removed, not archived.

.EXAMPLE
  .\scripts\install-for-grok.ps1
#>
[CmdletBinding()]
param(
    [string]$GrokConfig = (Join-Path $HOME ".grok\config.toml"),
    [string]$Dest = (Join-Path $HOME ".grok\skills"),
    [string]$ClaudeSkills = (Join-Path $HOME ".claude\skills"),
    [switch]$SkipClaudeCleanup,
    [switch]$SkipBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SkillsSrc = Join-Path $RepoRoot "skills"

$SkillNames = @(
    "audit-z80",
    "debug-z80",
    "develop-z80",
    "document-z80",
    "optimize-z80",
    "organize-z80",
    "port-spectranext",
    "route-z80",
    "send-bridgezx",
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

function ConvertTo-TomlPath([string]$Path) {
    return ($Path -replace '\\', '/')
}

function Test-ReparsePoint([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Test-SamePath([string]$Left, [string]$Right) {
    $leftFull = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/')
    $rightFull = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/')
    return [string]::Equals($leftFull, $rightFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Remove-SkillDirSafely([string]$Path, [string]$CanonicalPath) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    if (Test-SamePath $Path $CanonicalPath) {
        Write-Host "    skip canonical: $Path"
        return $false
    }
    if (Test-ReparsePoint $Path) {
        $code = 0
        cmd.exe /c "rmdir `"$Path`"" | Out-Null
        $code = $LASTEXITCODE
        if ($code -ne 0 -or (Test-Path -LiteralPath $Path)) {
            throw "Failed to remove reparse point without touching target: $Path"
        }
        Write-Host "    unlinked: $Path"
        return $true
    }
    Remove-Item -LiteralPath $Path -Recurse -Force
    Write-Host "    removed: $Path"
    return $true
}

function Remove-BundledCopies([string]$Root) {
    if (-not (Test-Path -LiteralPath $Root)) { return 0 }
    if (Test-SamePath $Root $SkillsSrc) {
        throw "Refusing to delete the canonical skills directory: $SkillsSrc"
    }
    $removed = 0
    foreach ($name in $SkillNames) {
        $copy = Join-Path $Root $name
        $canonical = Join-Path $SkillsSrc $name
        if (Remove-SkillDirSafely -Path $copy -CanonicalPath $canonical) {
            $removed += 1
        }
    }
    $shared = Join-Path $Root "_z80-shared"
    $sharedCanonical = Join-Path $RepoRoot "scripts"
    if (Remove-SkillDirSafely -Path $shared -CanonicalPath $sharedCanonical) {
        $removed += 1
    }
    return $removed
}

function Set-GrokSkillsPath([string]$ConfigPath, [string]$SkillsPath) {
    $tomlPath = ConvertTo-TomlPath $SkillsPath
    $quoted = '"' + $tomlPath.Replace('"', '\"') + '"'
    $dir = Split-Path -Parent $ConfigPath
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $text = ""
    if (Test-Path -LiteralPath $ConfigPath) {
        $text = [System.IO.File]::ReadAllText($ConfigPath)
    }

    if ($text -match [regex]::Escape($tomlPath)) {
        Write-Host "    config already lists $tomlPath"
        return
    }

    $nl = "`r`n"
    $pathsMatch = [regex]::Match($text, '(?m)^paths\s*=\s*\[([^\]]*)\]')
    if ($pathsMatch.Success) {
        $inner = $pathsMatch.Groups[1].Value.Trim()
        if ($inner.Length -eq 0) {
            $replacement = "paths = [$quoted]"
        }
        else {
            $trimmed = $inner.TrimEnd().TrimEnd(',')
            $replacement = "paths = [$trimmed, $quoted]"
        }
        $text = $text.Remove($pathsMatch.Index, $pathsMatch.Length).Insert($pathsMatch.Index, $replacement)
    }
    elseif ($text -match '(?m)^\[skills\]\s*$') {
        $text = [regex]::Replace(
            $text,
            '(?m)^\[skills\]\s*$',
            "[skills]$nl" + "paths = [$quoted]",
            1
        )
    }
    else {
        if ($text.Length -gt 0 -and -not $text.EndsWith("`n")) {
            $text += $nl
        }
        if ($text.Length -gt 0) {
            $text += $nl
        }
        $text += "[skills]$nl"
        $text += "# Canonical Z80 skill trees. Do not copy these into ~/.grok/skills.$nl"
        $text += "paths = [$quoted]$nl"
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($ConfigPath, $text, $utf8NoBom)
    Write-Host "    wrote $quoted into $ConfigPath"
}

# --- main ---
Write-Step "z80-skills → Grok Build (in-place)"
Write-Host "    repo: $RepoRoot"
Write-Host "    skills: $SkillsSrc"
Write-Host "    config: $GrokConfig"
Write-Host "    grok skills dir: $Dest"

Assert-Path $SkillsSrc "skills/"
foreach ($name in $SkillNames) {
    Assert-Path (Join-Path $SkillsSrc "$name\SKILL.md") "$name/SKILL.md"
}

if ($SkipBackup) {
    Write-Host "    SkipBackup is accepted; copies are removed, not archived."
}

Write-Step "Pointing Grok at canonical skills/"
Set-GrokSkillsPath -ConfigPath $GrokConfig -SkillsPath $SkillsSrc

Write-Step "Removing obsolete Grok copies"
$removedGrok = Remove-BundledCopies -Root $Dest
Write-Host "    grok copies removed: $removedGrok"

if (-not $SkipClaudeCleanup) {
    Write-Step "Removing obsolete Claude copies"
    $removedClaude = Remove-BundledCopies -Root $ClaudeSkills
    Write-Host "    claude copies removed: $removedClaude"
}

Write-Step "Verify"
$configText = [System.IO.File]::ReadAllText($GrokConfig)
$tomlPath = ConvertTo-TomlPath $SkillsSrc
if ($configText -notmatch [regex]::Escape($tomlPath)) {
    throw "Grok config does not list canonical skills path: $tomlPath"
}
foreach ($name in $SkillNames) {
    Assert-Path (Join-Path $SkillsSrc "$name\SKILL.md") "canonical $name/SKILL.md"
    $copy = Join-Path $Dest $name
    if (Test-Path -LiteralPath $copy) {
        throw "Obsolete Grok copy still present: $copy"
    }
}

Write-Host ""
Write-Host "Done. Grok reads the eleven skills from:" -ForegroundColor Green
Write-Host "  $tomlPath"
Write-Host "Open a new Grok task so the catalog reloads."
Write-Host ""
Write-Host "Update loop:"
Write-Host "  cd $RepoRoot"
Write-Host "  git pull --ff-only"
Write-Host "  # no Grok reinstall needed; the checkout is the catalog"
