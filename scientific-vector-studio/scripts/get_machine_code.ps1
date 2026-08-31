#requires -Version 5.1
[CmdletBinding()]
param([string]$PythonExecutable)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'license_gate.ps1')
$python = Resolve-SvsPython -PythonExecutable $PythonExecutable
Invoke-SvsLicenseManager -Python $python -Arguments @('machine-code') | ConvertTo-Json -Depth 4 -Compress
