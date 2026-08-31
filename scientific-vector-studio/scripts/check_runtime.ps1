#requires -Version 5.1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$pythonOk = $false
$pythonVersion = $null
$fontToolsVersion = $null
$cryptographyOk = $false
$numpyVersion = $null
$pillowVersion = $null
try {
    . (Join-Path $PSScriptRoot 'license_gate.ps1')
    $python = Resolve-SvsPython
    $probe = & $python.Executable @($python.Prefix) -X utf8 -c "import json,sys,fontTools,cryptography,numpy,PIL; print(json.dumps({'python':sys.version.split()[0],'fonttools':fontTools.__version__,'cryptography':True,'numpy':numpy.__version__,'pillow':PIL.__version__}))" | ConvertFrom-Json
    $pythonVersion = [string]$probe.python
    $fontToolsVersion = [string]$probe.fonttools
    $cryptographyOk = [bool]$probe.cryptography
    $numpyVersion = [string]$probe.numpy
    $pillowVersion = [string]$probe.pillow
    $pythonOk = [version]$pythonVersion -ge [version]'3.8'
} catch { }

$nativeRunner = Join-Path $PSScriptRoot 'illustrator_document_bridge.jsx'
$illustratorProcess = Get-Process -Name Illustrator -ErrorAction SilentlyContinue | Select-Object -First 1
$powerPointProcess = Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | Select-Object -First 1
$illustratorProgId = Test-Path -LiteralPath 'Registry::HKEY_CLASSES_ROOT\Illustrator.Application.30\CLSID'
$powerPointProgId = Test-Path -LiteralPath 'Registry::HKEY_CLASSES_ROOT\PowerPoint.Application\CLSID'
$applicationReady = ($illustratorProgId -or $powerPointProgId)
$licenseManager = Join-Path $PSScriptRoot 'license_manager.py'
$comparisonTool = Join-Path $PSScriptRoot 'compare_figure_renders.py'
$licenseImporter = Join-Path $PSScriptRoot 'import_license.ps1'

[ordered]@{
    ok = ($pythonOk -and $cryptographyOk -and $numpyVersion -and $pillowVersion -and (Test-Path -LiteralPath $nativeRunner) -and (Test-Path -LiteralPath $licenseManager) -and (Test-Path -LiteralPath $licenseImporter) -and (Test-Path -LiteralPath $comparisonTool) -and $applicationReady)
    python = $pythonVersion
    fonttools = $fontToolsVersion
    cryptography = $cryptographyOk
    numpy = $numpyVersion
    pillow = $pillowVersion
    license_manager = (Test-Path -LiteralPath $licenseManager)
    buyout_license_importer = (Test-Path -LiteralPath $licenseImporter)
    comparison_tool = (Test-Path -LiteralPath $comparisonTool)
    native_illustrator_runtime = (Test-Path -LiteralPath $nativeRunner)
    illustrator_30_registered = $illustratorProgId
    illustrator_running = ($null -ne $illustratorProcess)
    powerpoint_registered = $powerPointProgId
    powerpoint_running = ($null -ne $powerPointProcess)
    application_ready = $applicationReady
} | ConvertTo-Json -Compress
