#Requires -Version 5.1
<#
.SYNOPSIS
  Link this checkout's canonical skill trees into Claude Code.

.DESCRIPTION
  Creates one directory junction per bundled skill under ~/.claude/skills
  pointing at <repo>/skills/<name>, plus ~/.claude/scripts -> <repo>/scripts so
  the skills' `../../scripts/run_in_worktree.py` references resolve through the
  junctions. Nothing is copied; a `git pull` is visible to Claude Code at the
  next session. Existing junctions that already point at the canonical tree are
  left alone; real directories with the same name are reported, never deleted.

.PARAMETER ClaudeHome
  Claude Code user directory. Default: $HOME/.claude

.EXAMPLE
  pwsh -File .\scripts\install-for-claude.ps1
#>
[CmdletBinding()]
param(
    [string]$ClaudeHome = (Join-Path $HOME ".claude")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SkillsSrc = Join-Path $RepoRoot "skills"
$SkillsDest = Join-Path $ClaudeHome "skills"

$SkillNames = @(
    "audit-z80", "debug-z80", "develop-z80", "document-z80", "optimize-z80",
    "organize-z80", "port-spectranext", "route-z80", "send-bridgezx",
    "shrink-z80", "workflow"
)

function Test-SamePath([string]$Left, [string]$Right) {
    $l = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/')
    $r = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/')
    return [string]::Equals($l, $r, [System.StringComparison]::OrdinalIgnoreCase)
}

function Ensure-Junction([string]$Link, [string]$Target) {
    if (-not (Test-Path -LiteralPath $Target)) { throw "Missing target: $Target" }
    if (Test-Path -LiteralPath $Link) {
        $item = Get-Item -LiteralPath $Link -Force
        $isReparse = [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
        if ($isReparse) {
            $current = $item.Target
            if ($current -is [array]) { $current = $current[0] }
            if ($current -and (Test-SamePath $current $Target)) {
                Write-Host "    ok:       $Link"
                return
            }
            cmd.exe /c "rmdir `"$Link`"" | Out-Null
            if (Test-Path -LiteralPath $Link) { throw "Failed to unlink stale junction: $Link" }
            Write-Host "    relinked: $Link (was $current)"
        }
        else {
            Write-Warning "Real directory in the way, not touched: $Link"
            return
        }
    }
    New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null
    Write-Host "    linked:   $Link -> $Target"
}

Write-Host "==> z80-skills -> Claude Code (junctions)" -ForegroundColor Cyan
Write-Host "    repo:   $RepoRoot"
Write-Host "    skills: $SkillsDest"

if (-not (Test-Path -LiteralPath $SkillsDest)) {
    New-Item -ItemType Directory -Path $SkillsDest -Force | Out-Null
}
foreach ($name in $SkillNames) {
    $src = Join-Path $SkillsSrc $name
    if (-not (Test-Path -LiteralPath (Join-Path $src "SKILL.md"))) { throw "Missing $name/SKILL.md" }
    Ensure-Junction -Link (Join-Path $SkillsDest $name) -Target $src
}
Ensure-Junction -Link (Join-Path $ClaudeHome "scripts") -Target (Join-Path $RepoRoot "scripts")

Write-Host "==> done. Open a new Claude Code session to reload the skill catalog." -ForegroundColor Cyan
