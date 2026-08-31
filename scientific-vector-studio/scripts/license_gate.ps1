#requires -Version 5.1

$script:SvsPurchaseMessage = @'
欢迎关注“队长的生物实验室”微信公众号/小红书。
3 张免费体验已用完。39 元一次买断，绑定一台电脑不限绘图次数；同机 Illustrator/PowerPoint 共用。
添加队长的笔记本微信（XBBen01），提供机器码购买 SVS 买断授权文件。
不限次仅指 SVS 授权，不包含 Codex/API、Illustrator 等第三方费用或使用额度。
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
            Show-SvsPurchasePrompt
            throw "LICENSE_PURCHASE_REQUIRED|$script:SvsPurchaseMessage"
        }
        throw "LICENSE_MANAGER_FAILED|$text"
    }
    return $text | ConvertFrom-Json
}

function Show-SvsPurchasePrompt {
    try {
        Add-Type -AssemblyName PresentationFramework -ErrorAction Stop
        [void][System.Windows.MessageBox]::Show(
            $script:SvsPurchaseMessage,
            'Scientific Vector Studio',
            [System.Windows.MessageBoxButton]::OK,
            [System.Windows.MessageBoxImage]::Information
        )
    }
    catch {
        Write-Host $script:SvsPurchaseMessage
    }
}

function Start-SvsUsage {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Python,
        [Parameter(Mandatory = $true)][string]$InputSvg,
        [string]$UsageId,
        [string]$LicenseStatePath,
        [string]$LicenseConfigPath
    )
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $InputSvg).Hash.ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($UsageId)) { $UsageId = "svg-$($hash.Substring(0, 32))" }
    $reservation = Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @(
        'reserve', '--usage-id', $UsageId, '--artifact-sha256', $hash
    )
    return [ordered]@{ UsageId = $UsageId; Reused = [bool]$reservation.reused }
}

function Complete-SvsUsage {
    param([hashtable]$Python, [string]$UsageId, [string]$LicenseStatePath, [string]$LicenseConfigPath)
    [void](Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('commit', '--usage-id', $UsageId))
}

function Cancel-SvsUsage {
    param([hashtable]$Python, [string]$UsageId, [string]$LicenseStatePath, [string]$LicenseConfigPath)
    try {
        [void](Invoke-SvsLicenseManager -Python $Python -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath -Arguments @('cancel', '--usage-id', $UsageId))
    }
    catch { }
}
