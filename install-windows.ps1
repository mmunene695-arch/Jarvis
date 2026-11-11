<#
.SYNOPSIS
    Installs JARVIS v0.2 on Windows.

.DESCRIPTION
    Creates a virtual environment, installs JARVIS and its optional extras, then
    runs a self-check. Nothing is installed as a service and nothing starts at
    login unless you later run `jarvis --command "enable startup"`.

.PARAMETER Extras
    Optional extra sets to install: all (default), voice, vision, bluetooth,
    system, none.

.PARAMETER VenvDir
    Folder for the virtual environment. Default: .venv

.PARAMETER NoVenv
    Install into the current Python environment instead of a virtual one.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install-windows.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -Extras voice
#>
[CmdletBinding()]
param(
    [string]$Extras = "all",
    [string]$VenvDir = ".venv",
    [switch]$NoVenv,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok([string]$Message) {
    Write-Host "    [ok] $Message" -ForegroundColor Green
}

function Write-Warn([string]$Message) {
    Write-Host "    [!]  $Message" -ForegroundColor Yellow
}

function Resolve-Python {
    $candidates = @(
        @{ Exe = "py";    Args = @("-3") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        $exe = Get-Command $candidate.Exe -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        try {
            $raw = & $candidate.Exe @($candidate.Args + @("-c", "import sys; print('%d.%d' % sys.version_info[:2])")) 2>$null
            if ($LASTEXITCODE -ne 0 -or -not $raw) { continue }
            $version = ($raw | Select-Object -Last 1).Trim()
            $parts = $version.Split(".")
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -eq 3 -and $minor -ge 9) {
                $candidate.Version = $version
                return $candidate
            }
        } catch {
            continue
        }
    }
    return $null
}

Write-Host "JARVIS v0.2 installer (Windows)" -ForegroundColor White
Write-Host "Python 3.9 or newer is required. https://www.python.org/downloads/windows/" -ForegroundColor DarkGray

Write-Step "Looking for Python"
$python = Resolve-Python
if (-not $python) {
    Write-Host ""
    Write-Host "No suitable Python found." -ForegroundColor Red
    Write-Host "Install Python 3.9+ from https://www.python.org/downloads/windows/ and tick"
    Write-Host "'Add python.exe to PATH', then run this script again."
    Write-Host "Quick option:  winget install --id Python.Python.3.12 -e"
    exit 1
}
Write-Ok "Python $($python.Version) found ($($python.Exe))"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if ($NoVenv) {
    Write-Step "Using the current Python environment (-NoVenv)"
    $pythonExe = $python.Exe
    $pythonArgs = $python.Args
} else {
    $venvPath = Join-Path $repoRoot $VenvDir
    if (-not (Test-Path $venvPath)) {
        Write-Step "Creating virtual environment in $venvPath"
        & $python.Exe @($python.Args + @("-m", "venv", $venvPath))
        if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
    } else {
        Write-Step "Reusing virtual environment $venvPath"
    }
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) { throw "The virtual environment looks incomplete: $pythonExe is missing." }
    $pythonArgs = @()
    Write-Ok "Virtual environment ready"
}

Write-Step "Upgrading pip"
& $pythonExe @($pythonArgs + @("-m", "pip", "install", "--upgrade", "pip", "--quiet"))
if ($LASTEXITCODE -ne 0) { Write-Warn "pip upgrade failed; continuing with the existing pip." }

$extrasArg = ""
if ($Extras -and $Extras -ne "none") {
    $extrasArg = "[$Extras]"
}

Write-Step "Installing JARVIS$extrasArg (this can take a few minutes)"
& $pythonExe @($pythonArgs + @("-m", "pip", "install", "-e", ".$extrasArg"))
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Warn "Installing every extra failed on this machine."
    Write-Host "    JARVIS itself has no required dependencies; retrying with the core package."
    & $pythonExe @($pythonArgs + @("-m", "pip", "install", "-e", "."))
    if ($LASTEXITCODE -ne 0) { throw "Installation failed. Check the pip output above." }
    Write-Ok "Core package installed (optional extras skipped)"
} else {
    Write-Ok "Package installed"
}

if (-not $SkipTests) {
    Write-Step "Running the local test suite (offline)"
    & $pythonExe @($pythonArgs + @("-m", "pip", "install", "--quiet", "pytest"))
    & $pythonExe @($pythonArgs + @("-m", "pytest", "-q"))
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Some tests failed. JARVIS may still work; see the output above."
    } else {
        Write-Ok "All local tests passed"
    }
}

Write-Step "Self-check"
& $pythonExe @($pythonArgs + @("-m", "jarvis", "--doctor"))

Write-Host ""
Write-Host "JARVIS is installed." -ForegroundColor Green
Write-Host ""
if (-not $NoVenv) {
    Write-Host "Activate the environment for this terminal:" -ForegroundColor White
    Write-Host "    .\$VenvDir\Scripts\Activate.ps1"
} else {
    Write-Host "The 'jarvis' command should already be on your PATH." -ForegroundColor White
}
Write-Host ""
Write-Host "Start the offline console (no microphone needed):"
Write-Host "    jarvis --console"
Write-Host "Ask one question and exit:"
Write-Host "    jarvis --command `"system status`""
Write-Host "Start voice standby (needs the voice extra and OPENAI_API_KEY):"
Write-Host "    jarvis --voice"
Write-Host ""
Write-Host "Optional: add a visibly-starting launcher to your Windows startup items"
Write-Host "    jarvis --command `"enable startup`" --yes"
Write-Host ""
Write-Host "If PowerShell blocks the virtual environment activation, run once:"
Write-Host "    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
Write-Host ""
