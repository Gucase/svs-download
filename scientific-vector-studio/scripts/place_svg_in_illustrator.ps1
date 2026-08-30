#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$InputSvg,
    [string]$WorkDir,
    [ValidateSet('append', 'review')][string]$Mode = 'review',
    [string]$OutputAi,
    [string]$OutputPng,
    [ValidateSet('center', 'top-center', 'left-center', 'bottom-center', 'bottom-right', 'top-right', 'bottom-left', 'top-left')]
    [string]$Placement = 'center',
    [ValidateRange(0.01, 1)][double]$MaxWidthFraction = 0.72,
    [ValidateRange(0.01, 1)][double]$MaxHeightFraction = 0.78,
    [int]$DelayMs = 0,
    [string]$PythonExecutable,
    [string]$UsageId,
    [string]$LicenseStatePath,
    [string]$LicenseConfigPath,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($DelayMs -ne 0) { throw 'Native document import does not support delayed per-object playback; omit DelayMs.' }
if (-not $DryRun -and -not $UsageId) { throw 'Provide a stable UsageId for this figure, including corrections and other app outputs.' }
$sourceFile = (Get-Item -LiteralPath $InputSvg).FullName
. (Join-Path $PSScriptRoot 'license_gate.ps1')
$interpreter = Resolve-SvsPython -PythonExecutable $PythonExecutable
$auditTool = Join-Path $PSScriptRoot 'validate_master_svg.py'
$auditText = & $interpreter.Executable @($interpreter.Prefix) -X utf8 $auditTool --svg $sourceFile --profile illustrator-native
if ($LASTEXITCODE -ne 0) { throw "Vector validation failed: $auditText" }
$audit = ($auditText -join "`n") | ConvertFrom-Json
$destinationFiles = @{}
foreach ($entry in @{ai = $OutputAi; png = $OutputPng}.GetEnumerator()) {
    if (-not $entry.Value) { continue }
    $absolute = [IO.Path]::GetFullPath($entry.Value)
    if ([IO.Path]::GetExtension($absolute) -ine ('.' + $entry.Key)) { throw "Expected .$($entry.Key) output: $absolute" }
    if (Test-Path -LiteralPath $absolute) { throw "Existing output is protected: $absolute" }
    if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($absolute)) -PathType Container)) { throw "Output parent must already exist: $absolute" }
    $destinationFiles[$entry.Key] = $absolute
}
if ($DryRun) {
    [ordered]@{ status = 'VALIDATED'; mode = $Mode; audit = $audit; app_untouched = $true; charged = $false } | ConvertTo-Json -Depth 8
    return
}
if ($PSVersionTable.PSEdition -eq 'Core') { throw 'Run this bridge in powershell.exe (Windows PowerShell 5.1), not pwsh.' }
$illustrator = $null
foreach ($registeredName in @('Illustrator.Application', 'Illustrator.Application.30')) {
    try { $illustrator = [Runtime.InteropServices.Marshal]::GetActiveObject($registeredName); break } catch { }
}
if ($null -eq $illustrator) { throw 'Open Illustrator and a document, then retry. SVS will not launch it automatically.' }
if ([int]$illustrator.Documents.Count -eq 0) { throw 'Open a document in Illustrator before importing.' }
if (-not $WorkDir) { $WorkDir = Join-Path ([IO.Path]::GetTempPath()) ('svs-import-' + [guid]::NewGuid().ToString('N')) }
$jobFolder = [IO.Path]::GetFullPath($WorkDir)
[void][IO.Directory]::CreateDirectory($jobFolder)
$preparedFile = Join-Path $jobFolder (([guid]::NewGuid().ToString('N')) + '.svg')
$preparation = & $interpreter.Executable @($interpreter.Prefix) -X utf8 (Join-Path $PSScriptRoot 'prepare_native_svg.py') --input $sourceFile --output $preparedFile
if ($LASTEXITCODE -ne 0) { throw "Native preparation failed: $preparation" }
$job = @{
    source = $preparedFile; mode = $Mode; placement = $Placement
    widthFraction = $MaxWidthFraction; heightFraction = $MaxHeightFraction
    expectedText = [int]$audit.live_text_count
    groupName = 'SVS_' + (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.Substring(0, 16)
    outputAi = $destinationFiles['ai']; outputPng = $destinationFiles['png']
}
$bridgeText = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'illustrator_document_bridge.jsx'))
$reservationArgs = @{ Python = $interpreter; UsageId = $UsageId; LicenseStatePath = $LicenseStatePath; LicenseConfigPath = $LicenseConfigPath }
Write-Verbose 'Reserving this figure before document transfer.'
$reservation = Start-SvsUsage @reservationArgs -InputSvg $sourceFile
$delivered = $false
$submitted = $false
$replyReceived = $false
try {
    Write-Verbose 'Submitting the native SVG document transfer to Illustrator.'
    $submitted = $true
    $answer = [string]$illustrator.DoJavaScript(('var SVS_DOCUMENT_JOB = ' + ($job | ConvertTo-Json -Compress) + ";`n" + $bridgeText))
    $replyReceived = $true
    if (-not $answer.StartsWith('SVS_IMPORT_OK|')) { throw "Illustrator import did not complete: $answer" }
    $delivered = $true
    Write-Verbose 'Native vectors are present; completing the usage transaction.'
    if (-not $reservation.Reused) { Complete-SvsUsage @reservationArgs }
    $parts = $answer.Split('|')
    $report = [ordered]@{status = 'IMPORTED'; mode = $Mode; document = [Uri]::UnescapeDataString($parts[1]);
        paths = [int]$parts[2]; live_text = [int]$parts[3]; gradients = [int]$parts[4];
        export_issue = [Uri]::UnescapeDataString($parts[5]); usage_id = $UsageId; source = $sourceFile}
    $report | ConvertTo-Json -Depth 4
    if ($report.export_issue) { Write-Warning ('Editable artwork is present, but an optional export failed: ' + $report.export_issue) }
}
catch {
    if (-not $delivered -and -not $reservation.Reused -and (-not $submitted -or $replyReceived)) { Cancel-SvsUsage @reservationArgs }
    if ($submitted -and -not $replyReceived) { Write-Warning 'COM completion is uncertain. The reservation is retained; inspect Illustrator before committing, cancelling or retrying this UsageId.' }
    # After an ambiguous COM transport error, inspect the app before retrying.
    throw
}
