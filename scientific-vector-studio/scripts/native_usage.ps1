#requires -Version 5.1
param(
    [Parameter(Mandatory = $true)][ValidateSet('Reserve', 'Commit', 'Cancel')][string]$Action,
    [Parameter(Mandatory = $true)][string]$UsageId,
    [string]$InputSvg,
    [string]$PythonExecutable,
    [string]$LicenseStatePath,
    [string]$LicenseConfigPath
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'license_gate.ps1')
if ([string]::IsNullOrWhiteSpace($UsageId)) { throw 'A stable generation UsageId is required.' }
$runtime = Resolve-SvsPython -PythonExecutable $PythonExecutable
$parameters = @{ Python = $runtime; UsageId = $UsageId; LicenseStatePath = $LicenseStatePath; LicenseConfigPath = $LicenseConfigPath }
if ($Action -eq 'Reserve') {
    if ([string]::IsNullOrWhiteSpace($InputSvg)) { throw 'Reserve requires InputSvg.' }
    $resolvedSvg = (Resolve-Path -LiteralPath $InputSvg).Path
    $validator = Join-Path $PSScriptRoot 'validate_master_svg.py'
    & $runtime.Executable @($runtime.Prefix) $validator --svg $resolvedSvg --profile illustrator-native
    if ($LASTEXITCODE -ne 0) { throw 'Native vector validation failed; usage was not reserved.' }
    Start-SvsUsage @parameters -InputSvg $resolvedSvg | ConvertTo-Json -Compress
}
elseif ($Action -eq 'Commit') {
    Complete-SvsUsage @parameters
    Write-Output 'SVS_USAGE_COMMITTED'
}
else {
    # Use the manager directly so a failed cancellation is not reported as success.
    Invoke-SvsLicenseManager -Python $runtime -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('cancel', '--usage-id', $UsageId) | ConvertTo-Json -Compress
}
