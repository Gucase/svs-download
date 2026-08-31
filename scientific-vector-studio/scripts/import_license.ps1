#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$LicenseFile,
    [string]$PythonExecutable,
    [string]$LicenseStatePath
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'license_gate.ps1')
$python = Resolve-SvsPython -PythonExecutable $PythonExecutable
$file = (Resolve-Path -LiteralPath $LicenseFile).Path
Invoke-SvsLicenseManager -Python $python -LicenseStatePath $LicenseStatePath -Arguments @(
    'import-license', '--file', $file
) | ConvertTo-Json -Depth 6 -Compress
