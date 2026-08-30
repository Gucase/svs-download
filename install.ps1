#requires -Version 5.1

[CmdletBinding()]
param(
    [switch]$Force,
    [string]$InstallRoot = (Join-Path $env:USERPROFILE '.codex\skills')
)

$ErrorActionPreference = 'Stop'
$assetUrl = 'https://github.com/Gucase/svs-download/releases/latest/download/scientific-vector-studio.zip'
$checksumsUrl = 'https://github.com/Gucase/svs-download/releases/latest/download/SHA256SUMS.txt'
$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("svs-install-" + [guid]::NewGuid().ToString('N'))
$archivePath = Join-Path $temporaryRoot 'scientific-vector-studio.zip'
$checksumsPath = Join-Path $temporaryRoot 'SHA256SUMS.txt'
$extractPath = Join-Path $temporaryRoot 'extracted'
$targetPath = Join-Path $InstallRoot 'scientific-vector-studio'

function Resolve-SvsPython {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { return @{ Executable = $launcher.Source; Prefix = @('-3') } }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @{ Executable = $python.Source; Prefix = @() } }
    throw 'Python 3.8 or newer was not found. Install Python with pip, then run this installer again.'
}

try {
    New-Item -ItemType Directory -Path $temporaryRoot | Out-Null
    Invoke-WebRequest -Uri $assetUrl -OutFile $archivePath -UseBasicParsing
    Invoke-WebRequest -Uri $checksumsUrl -OutFile $checksumsPath -UseBasicParsing

    $checksumLine = Select-String -LiteralPath $checksumsPath -Pattern 'scientific-vector-studio\.zip$' | Select-Object -First 1
    if (-not $checksumLine) { throw 'Release checksum entry was not found.' }
    $expectedHash = ($checksumLine.Line -split '\s+')[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) { throw 'Release checksum verification failed.' }

    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractPath
    $stagedSkill = Join-Path $extractPath 'scientific-vector-studio'
    if (-not (Test-Path -LiteralPath (Join-Path $stagedSkill 'SKILL.md'))) {
        throw 'The release does not contain a valid scientific-vector-studio skill folder.'
    }

    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    if (Test-Path -LiteralPath $targetPath) {
        if (-not $Force) { throw "The skill is already installed at $targetPath. Re-run with -Force to update it." }
        $backupPath = "$targetPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -LiteralPath $targetPath -Destination $backupPath
        Write-Host "Previous version backed up to $backupPath"
    }

    Move-Item -LiteralPath $stagedSkill -Destination $targetPath
    Write-Host "Scientific Vector Studio installed at $targetPath" -ForegroundColor Green

    $python = Resolve-SvsPython
    $versionText = & $python.Executable @($python.Prefix) -c "import sys; print('.'.join(map(str,sys.version_info[:3])))"
    if ([version]$versionText -lt [version]'3.8') { throw "Python 3.8 or newer is required; found $versionText." }
    & $python.Executable @($python.Prefix) -m pip install -r (Join-Path $targetPath 'requirements.txt') --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }

    $runtimeResult = & (Join-Path $targetPath 'scripts\check_runtime.ps1')
    Write-Host 'Environment report:'
    Write-Host $runtimeResult
    Write-Host 'Installation and Python dependency setup completed.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}
