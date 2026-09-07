#requires -Version 5.1

$script:SvsPurchaseMessage = @'
欢迎关注“队长的生物实验室”微信公众号/小红书。
免费体验已用完。39 元一次买断，绑定一台电脑；参考图重建与科研图元绘制均不限次数，同机 Illustrator/PowerPoint 共用。
如需购买，可联系微信 XBBen01 获取与本机绑定的 .svslicense 授权文件。
不限次仅指 SVS 授权，不包含 Codex 第三方使用额度。
'@

function Resolve-SvsPython {
    param([string]$PythonExecutable)
    if (-not [string]::IsNullOrWhiteSpace($PythonExecutable)) {
        return [ordered]@{ Executable = (Resolve-Path -LiteralPath $PythonExecutable).Path; Prefix = @() }
    }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $launcher) {
        return [ordered]@{ Executable = $launcher.Source; Prefix = @('-3') }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) { throw 'PYTHON_NOT_FOUND|Install Python or pass -PythonExecutable.' }
    return [ordered]@{ Executable = $python.Source; Prefix = @() }
}

function Invoke-SvsLicenseManager {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Python,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$LicenseStatePath,
        [string]$LicenseConfigPath
    )
    if (-not [string]::IsNullOrWhiteSpace($LicenseConfigPath)) {
        throw 'ONLINE_LICENSING_RETIRED|Use import_license.ps1 for the buyout file; omit LicenseConfigPath.'
    }
    $manager = Join-Path $PSScriptRoot 'license_manager.py'
    $managerArguments = @('-X', 'utf8', $manager)
    if (-not [string]::IsNullOrWhiteSpace($LicenseStatePath)) {
        $managerArguments += @('--state', [IO.Path]::GetFullPath($LicenseStatePath))
    }
    $managerArguments += $Arguments
    $output = & $Python.Executable @($Python.Prefix) @managerArguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()
    if ($exitCode -ne 0) {
        if ($exitCode -eq 4 -or $text -match 'purchase_required') {
            $purchaseMessage = $script:SvsPurchaseMessage
            try {
                $failure = $text | ConvertFrom-Json
                if (-not [string]::IsNullOrWhiteSpace([string]$failure.message)) { $purchaseMessage = [string]$failure.message }
            }
            catch { }
            Show-SvsPurchasePrompt -Message $purchaseMessage
            throw "LICENSE_PURCHASE_REQUIRED|$purchaseMessage"
        }
        throw "LICENSE_MANAGER_FAILED|$text"
    }
    return $text | ConvertFrom-Json
}

function Show-SvsPurchasePrompt {
    param([string]$Message = $script:SvsPurchaseMessage)
    try {
        Add-Type -AssemblyName PresentationFramework -ErrorAction Stop
        [void][System.Windows.MessageBox]::Show(
            $Message,
            'Scientific Vector Studio',
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Information
        )
    }
    catch {
        Write-Host $Message
    }
}

function Start-SvsUsage {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Python,
        [Parameter(Mandatory = $true)][string]$InputSvg,
        [string]$UsageId,
        [ValidateSet('reference_reconstruction', 'scientific_asset_drawing')]
        [string]$FeatureMode = 'reference_reconstruction',
        [string]$LicenseStatePath,
        [string]$LicenseConfigPath
    )
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $InputSvg).Hash.ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($UsageId)) { $UsageId = "svg-$($hash.Substring(0, 32))" }
    $reservation = Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @(
        'reserve', '--usage-id', $UsageId, '--artifact-sha256', $hash, '--mode', $FeatureMode
    )
    return [ordered]@{ UsageId = $UsageId; Reused = [bool]$reservation.reused }
}

function Complete-SvsUsage {
    param([hashtable]$Python, [string]$UsageId, [string]$LicenseStatePath, [string]$LicenseConfigPath,
          [string]$FeatureMode = 'reference_reconstruction')
    [void](Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('commit', '--usage-id', $UsageId))
}

function Cancel-SvsUsage {
    param([hashtable]$Python, [string]$UsageId, [string]$LicenseStatePath, [string]$LicenseConfigPath,
          [string]$FeatureMode = 'reference_reconstruction')
    try {
        [void](Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('cancel', '--usage-id', $UsageId))
    }
    catch { }
}
