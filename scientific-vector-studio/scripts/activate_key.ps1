#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$Key,
    [string]$ServerUrl,
    [string]$ActivationCode,
    [string]$PythonExecutable,
    [string]$LicenseStatePath,
    [string]$LicenseConfigPath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'license_gate.ps1')
$python = Resolve-SvsPython -PythonExecutable $PythonExecutable
if (-not [string]::IsNullOrWhiteSpace($ServerUrl)) {
    if ([string]::IsNullOrWhiteSpace($ActivationCode)) {
        $secureCode = Read-Host '粘贴小程序生成的一次性激活码' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureCode)
        try { $ActivationCode = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
    $onlineClient = Join-Path $PSScriptRoot 'online_license_client.py'
    $arguments = @('-X', 'utf8', $onlineClient)
    if (-not [string]::IsNullOrWhiteSpace($LicenseConfigPath)) { $arguments += @('--config', [IO.Path]::GetFullPath($LicenseConfigPath)) }
    $arguments += @('activate', '--server', $ServerUrl, '--code', $ActivationCode)
    $result = & $python.Executable @($python.Prefix) @arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "ONLINE_ACTIVATION_FAILED|$result" }
    $ActivationCode = $null
    $result
    exit 0
}
if ([string]::IsNullOrWhiteSpace($Key)) {
    $secureKey = Read-Host '粘贴 Scientific Vector Studio 激活 Key' -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try { $Key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}
if ([string]::IsNullOrWhiteSpace($Key)) { throw 'ACTIVATION_KEY_REQUIRED' }
$result = Invoke-SvsLicenseManager -Python $python -LicenseStatePath $LicenseStatePath -Arguments @('activate', '--key', $Key)
$Key = $null
[ordered]@{
    ok = [bool]$result.ok
    license_id = [string]$result.license_id
    credits = [int]$result.credits
} | ConvertTo-Json -Compress
