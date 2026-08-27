param(
    [switch]$verbose,
    [switch]$gpu,
    [switch]$create_env,
    [switch]$nodeps,
    [string]$env_name = ".venv",
    [string]$extra = ""
)

$validSwitches = @('verbose', 'gpu', 'create_env', 'nodeps')
$validParams = @('env_name', 'extra')

$allArgs = $MyInvocation.Line -split ' ' | Where-Object { $_ -match '^-' }
$unknownFlags = @()
foreach ($arg in $allArgs) {
    $flagName = $arg -replace '^-+', ''
    $isValidSwitch = $flagName -in $validSwitches
    $isValidParam = ($flagName -split '=')[0] -in $validParams
    if (-not ($isValidSwitch -or $isValidParam)) {
        $unknownFlags += $flagName
    }
}

if ($unknownFlags.Count -gt 0) {
    Write-Host "ERROR: Unknown flags: $($unknownFlags -join ', ')" -ForegroundColor Red
    Write-Host "`nAvailable parameters:" -ForegroundColor Cyan
    Write-Host "  -verbose      : Show detailed output" -ForegroundColor Green
    Write-Host "  -gpu          : Ignored (GPU not required)" -ForegroundColor Green
    Write-Host "  -create_env   : Create virtual environment" -ForegroundColor Green
    Write-Host "  -nodeps       : Skip installing dependencies" -ForegroundColor Green
    Write-Host "  -env_name     : Env name (default: .venv)" -ForegroundColor Green
    Write-Host "  -extra        : Extra pip arguments" -ForegroundColor Green
    exit 1
}

Write-Host "=== Neo Prompt Installation ===" -ForegroundColor Magenta

function Test-Python312 {
    try {
        $result = & python --version 2>&1
        if ($result -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            return ($major -eq 3 -and $minor -ge 12)
        }
    } catch {
        return $false
    }
    return $false
}

function Test-VenvExists {
    param([string]$Path)
    return (Test-Path "$Path\Scripts\python.exe") -or (Test-Path "$Path/bin/python")
}

function Show-Usage {
    Write-Host "`nUsage:" -ForegroundColor Cyan
    Write-Host "  .\install.ps1 -create_env" -ForegroundColor Green
    Write-Host "  .\install.ps1 -create_env -verbose" -ForegroundColor Green
    Write-Host "  .\install.ps1 -create_env -nodeps" -ForegroundColor Green
    Write-Host "`nParameters:" -ForegroundColor Yellow
    Write-Host "    -create_env  : Create virtual environment (required on first run)" -ForegroundColor Gray
    Write-Host "    -gpu         : Ignored" -ForegroundColor Gray
    Write-Host "    -verbose     : Show detailed output" -ForegroundColor Gray
    Write-Host "    -nodeps      : Do NOT install dependencies" -ForegroundColor Gray
    Write-Host "    -env_name    : Virtual environment name (default: .venv)" -ForegroundColor Gray
    Write-Host "    -extra       : Extra arguments for pip" -ForegroundColor Gray
}

function Install-PythonWindows {
    Write-Host "  Downloading Python 3.12..." -ForegroundColor Gray
    $pythonUrl = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
    $installer = "$env:TEMP\python-3.12.4-amd64.exe"

    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($pythonUrl, $installer)
        Write-Host "  Downloaded" -ForegroundColor Green

        Write-Host "  Installing Python 3.12..." -ForegroundColor Gray
        $process = Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -PassThru
        if ($process.ExitCode -eq 0) {
            Write-Host "  Python 3.12 installed successfully" -ForegroundColor Green
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            return $true
        } else {
            Write-Host "  Installation failed with code: $($process.ExitCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  Download failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    } finally {
        Remove-Item $installer -ErrorAction SilentlyContinue
    }
}

# Step 1: Python check
Write-Host "[1/4] Checking Python 3.12+..." -ForegroundColor Cyan

$hasPython312 = Test-Python312

if (-not $hasPython312) {
    Write-Host "  Python 3.12+ not found" -ForegroundColor Yellow

    if ($create_env) {
        Write-Host "  Attempting to install Python 3.12 automatically..." -ForegroundColor Cyan
        $installed = Install-PythonWindows
        if (-not $installed) {
            Write-Host "  Could not install Python automatically" -ForegroundColor Red
            Write-Host "  Please install Python 3.12+ manually from https://python.org" -ForegroundColor Yellow
            exit 1
        }
        $hasPython312 = Test-Python312
        if (-not $hasPython312) {
            Write-Host "  Python installation verification failed. Restart terminal and run again." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  Python 3.12+ is required but not found!" -ForegroundColor Red
        Show-Usage
        exit 1
    }
}

Write-Host "  Python 3.12+ available" -ForegroundColor Green
$pythonVersion = & python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Gray

# Step 2: venv
Write-Host "[2/4] Checking virtual environment..." -ForegroundColor Cyan

$venvPath = ".\$env_name"
$venvExists = Test-VenvExists -Path $venvPath

if (-not $venvExists) {
    Write-Host "  Virtual environment '$env_name' not found!" -ForegroundColor Yellow

    if ($create_env) {
        Write-Host "  Creating venv '$env_name'..." -ForegroundColor Gray
        & python -m venv $env_name
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Failed to create venv" -ForegroundColor Red
            exit 1
        }
        Write-Host "  venv created: $venvPath" -ForegroundColor Green
        $venvExists = $true
    } else {
        Write-Host "  Virtual environment required but not found! Use -create_env" -ForegroundColor Red
        Show-Usage
        exit 1
    }
} else {
    Write-Host "  Virtual environment found: $venvPath" -ForegroundColor Green
}

# Activate
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    $activateScript = "$venvPath/bin/activate"
}
if (Test-Path $activateScript) {
    if ($activateScript -like "*.ps1") {
        & $activateScript
    } else {
        $env:PATH = "$venvPath\Scripts;$venvPath\bin;$env:PATH"
    }
    Write-Host "  Environment activated" -ForegroundColor Green
} else {
    Write-Host "  Could not find activation script, using direct path" -ForegroundColor Yellow
    $env:PATH = "$venvPath\Scripts;$venvPath\bin;$env:PATH"
}

# Step 3: Install
Write-Host "[3/4] Installing Neo Prompt..." -ForegroundColor Cyan

python -m pip install --upgrade pip

$pipArgs = @("install", "--no-cache-dir", "--force-reinstall")

if ($nodeps) {
    $pipArgs += "-e", ".", "--no-deps"
    Write-Host "  Mode: WITHOUT dependencies" -ForegroundColor Yellow
} else {
    $pipArgs += "-e", "."
    Write-Host "  Mode: WITH dependencies (gradio, requests)" -ForegroundColor Green
}

if ($extra) {
    $pipArgs += $extra.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
}

if ($verbose) {
    Write-Host "  Running: pip $($pipArgs -join ' ')" -ForegroundColor Gray
    & pip @pipArgs
} else {
    Write-Host "  Installing... (please wait)" -ForegroundColor Gray
    & pip @pipArgs 2>&1 | Out-Null
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to install project" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "  Project installed successfully" -ForegroundColor Green

# Step 4: Verify
Write-Host "[4/4] Verifying imports..." -ForegroundColor Cyan

$importCheck = python -c "import gradio, requests; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  All dependencies loaded" -ForegroundColor Green
} else {
    Write-Host "  Import error: $importCheck" -ForegroundColor Red
    Write-Host "  Try manually: pip install 'gradio>=6.13.0' 'requests>=2.33.1'" -ForegroundColor Yellow
    exit 1
}

if (Test-Path ".\pro\config.py") {
    Write-Host "  Configuration found. Edit pro/config.py if needed." -ForegroundColor Green
} else {
    Write-Host "  Warning: pro/config.py not found." -ForegroundColor Yellow
}

# Final
Write-Host "`n=== Installation Successful ===" -ForegroundColor Green
Write-Host "  Virtual environment: $venvPath" -ForegroundColor Cyan
Write-Host "    To activate manually: $env_name\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  Run the app:" -ForegroundColor Yellow
Write-Host "    python Neo-Prompt.py" -ForegroundColor White
Write-Host "  or" -ForegroundColor Yellow
Write-Host "    run.bat" -ForegroundColor White
Write-Host "  and" -ForegroundColor Yellow
Write-Host "    Then open http://127.0.0.1:7860" -ForegroundColor Gray
Read-Host  "`n=== Done ===" -ForegroundColor Magenta
