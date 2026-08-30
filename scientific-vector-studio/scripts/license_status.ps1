#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$PythonExecutable,
    [string]$LicenseStatePath,
    [string]$LicenseConfigPath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'license_gate.ps1')
$python = Resolve-SvsPython -PythonExecutable $PythonExecutable
Invoke-SvsLicenseManager -Python $python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('status') | ConvertTo-Json -Depth 6 -Compress
