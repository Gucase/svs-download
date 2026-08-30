#requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputSvg,

    [string]$WorkDir,
    [ValidateRange(0, 10000)]
    [int]$SlideIndex = 0,
    [ValidateRange(0.05, 1.0)]
    [double]$MaxWidthFraction = 0.82,
    [ValidateRange(0.05, 1.0)]
    [double]$MaxHeightFraction = 0.82,
    [ValidateRange(0, 1000)]
    [int]$DelayMs = 0,
    [string]$OutputPptx,
    [string]$PythonExecutable,
    [string]$UsageId,
    [string]$LicenseStatePath,
    [string]$LicenseConfigPath,
    [switch]$RequireEditableGeometry,
    [switch]$GroupNewObjects,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$inputPath = (Resolve-Path -LiteralPath $InputSvg).Path
$stem = [IO.Path]::GetFileNameWithoutExtension($inputPath)
$parent = [IO.Path]::GetDirectoryName($inputPath)
if ([string]::IsNullOrWhiteSpace($WorkDir)) {
    $WorkDir = Join-Path $parent ".scientific-vector-ppt-cache\$stem"
}
$workPath = [IO.Path]::GetFullPath($WorkDir)
New-Item -ItemType Directory -Force -Path $workPath | Out-Null

$validator = Join-Path $PSScriptRoot 'validate_master_svg.py'
$preparer = Join-Path $PSScriptRoot 'prepare_powerpoint_assets.py'
$geometrySvg = Join-Path $workPath 'geometry.svg'
$textJson = Join-Path $workPath 'live-text.json'

$licenseGate = Join-Path $PSScriptRoot 'license_gate.ps1'
. $licenseGate
$python = Resolve-SvsPython -PythonExecutable $PythonExecutable

$validation = & $python.Executable @($python.Prefix) -X utf8 $validator --svg $inputPath --require-text 2>&1
if ($LASTEXITCODE -ne 0) { throw "MASTER_SVG_INVALID|$validation" }
$prepared = & $python.Executable @($python.Prefix) -X utf8 $preparer --input-svg $inputPath --geometry-svg $geometrySvg --text-json $textJson 2>&1
if ($LASTEXITCODE -ne 0) { throw "POWERPOINT_ASSET_PREPARATION_FAILED|$prepared" }

$manifest = Get-Content -LiteralPath $textJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($DryRun) {
    [ordered]@{
        ok = $true
        mode = 'dry-run'
        geometry_svg = $geometrySvg
        live_text_json = $textJson
        live_text_count = @($manifest.text_elements).Count
        powerpoint_untouched = $true
    } | ConvertTo-Json -Compress
    exit 0
}

$visiblePowerPoint = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -match '^POWERPNT$'
} | Select-Object -First 1
if ($null -eq $visiblePowerPoint) {
    throw 'POWERPOINT_NOT_RUNNING|Open PowerPoint and the target presentation yourself.'
}

$usage = Start-SvsUsage -Python $python -InputSvg $inputPath -UsageId $UsageId -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath

function Convert-HexToOfficeRgb([string]$value) {
    $known = @{
        black = '#000000'; white = '#FFFFFF'; red = '#FF0000'; green = '#008000';
        blue = '#0000FF'; gray = '#808080'; grey = '#808080'; orange = '#FFA500';
        purple = '#800080'; yellow = '#FFFF00'
    }
    $text = ([string]$value).Trim()
    if ($known.ContainsKey($text.ToLowerInvariant())) { $text = $known[$text.ToLowerInvariant()] }
    if ($text -match '^#([0-9A-Fa-f]{3})$') {
        $text = '#' + $matches[1][0] + $matches[1][0] + $matches[1][1] + $matches[1][1] + $matches[1][2] + $matches[1][2]
    }
    if ($text -notmatch '^#([0-9A-Fa-f]{6})$') { $text = '#000000' }
    $null = $text -match '^#([0-9A-Fa-f]{6})$'
    $hex = $matches[1]
    $r = [Convert]::ToInt32($hex.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($hex.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($hex.Substring(4, 2), 16)
    return $r + 256 * $g + 65536 * $b
}

$powerPoint = $null
$presentation = $null
$slide = $null
$createdNames = New-Object System.Collections.Generic.List[string]
$jobId = "SVS_$([Guid]::NewGuid().ToString('N').Substring(0, 12))"
try {
    # The process guard prevents this COM call from launching PowerPoint.
    $powerPoint = New-Object -ComObject PowerPoint.Application
    if ($powerPoint.Presentations.Count -lt 1) {
        throw 'POWERPOINT_DOCUMENT_REQUIRED|Open the target presentation yourself.'
    }
    $presentation = $powerPoint.ActivePresentation
    if ($SlideIndex -gt 0) {
        if ($SlideIndex -gt $presentation.Slides.Count) { throw 'SLIDE_INDEX_OUT_OF_RANGE' }
        $slide = $presentation.Slides.Item($SlideIndex)
    } else {
        $slide = $powerPoint.ActiveWindow.View.Slide
    }
    if ($null -eq $slide) { throw 'ACTIVE_SLIDE_REQUIRED' }

    $slideWidth = [double]$presentation.PageSetup.SlideWidth
    $slideHeight = [double]$presentation.PageSetup.SlideHeight
    $picture = $slide.Shapes.AddPicture($geometrySvg, 0, -1, 0, 0, -1, -1)
    $picture.Name = "${jobId}_geometry"
    $createdNames.Add($picture.Name)
    $picture.LockAspectRatio = -1
    $scale = [Math]::Min(($slideWidth * $MaxWidthFraction) / [double]$picture.Width, ($slideHeight * $MaxHeightFraction) / [double]$picture.Height)
    $picture.Width = [double]$picture.Width * $scale
    $picture.Height = [double]$picture.Height * $scale
    $picture.Left = ($slideWidth - [double]$picture.Width) / 2
    $picture.Top = ($slideHeight - [double]$picture.Height) / 2

    $geometryShape = $picture
    $geometryEditable = $false
    try {
        $converted = $picture.ConvertToShape()
        if ($null -ne $converted) {
            $geometryShape = $converted
            $geometryShape.Name = "${jobId}_geometry_editable"
            $createdNames.Clear()
            $createdNames.Add($geometryShape.Name)
            $geometryEditable = $true
        }
    }
    catch {
        if ($RequireEditableGeometry) {
            try { $picture.Delete() } catch { }
            throw "POWERPOINT_SVG_CONVERSION_UNAVAILABLE|$($_.Exception.Message)"
        }
    }

    $viewBox = @($manifest.view_box)
    $vbX = [double]$viewBox[0]
    $vbY = [double]$viewBox[1]
    $vbWidth = [double]$viewBox[2]
    $vbHeight = [double]$viewBox[3]
    $scaleX = [double]$geometryShape.Width / $vbWidth
    $scaleY = [double]$geometryShape.Height / $vbHeight

    $textIndex = 0
    foreach ($item in @($manifest.text_elements)) {
        $textIndex += 1
        $fontSize = [Math]::Max(1.0, [double]$item.font_size * $scaleY)
        $content = [string]$item.content
        $lineCount = [Math]::Max(1, @($content -split "`n").Count)
        $boxWidth = [Math]::Max(24.0, $fontSize * [Math]::Max(2, ($content -split "`n" | ForEach-Object { $_.Length } | Measure-Object -Maximum).Maximum) * 0.62)
        $boxHeight = [Math]::Max($fontSize * 1.35 * $lineCount, 12.0)
        $left = [double]$geometryShape.Left + ([double]$item.x - $vbX) * $scaleX
        if ([string]$item.text_anchor -eq 'middle') { $left -= $boxWidth / 2 }
        elseif ([string]$item.text_anchor -eq 'end') { $left -= $boxWidth }
        $top = [double]$geometryShape.Top + ([double]$item.y - $vbY) * $scaleY - $fontSize
        $box = $slide.Shapes.AddTextbox(1, $left, $top, $boxWidth, $boxHeight)
        $box.Name = "${jobId}_text_$textIndex"
        $createdNames.Add($box.Name)
        $box.Rotation = [double]$item.rotation
        $box.Line.Visible = 0
        $box.Fill.Visible = 0
        $box.TextFrame2.MarginLeft = 0
        $box.TextFrame2.MarginRight = 0
        $box.TextFrame2.MarginTop = 0
        $box.TextFrame2.MarginBottom = 0
        $box.TextFrame2.AutoSize = 1
        $range = $box.TextFrame2.TextRange
        $range.Text = $content
        $range.Font.Name = [string]$item.font_family
        $range.Font.Size = $fontSize
        $range.Font.Bold = $(if ([string]$item.font_weight -match 'bold|[6-9]00') { -1 } else { 0 })
        $range.Font.Italic = $(if ([string]$item.font_style -eq 'italic') { -1 } else { 0 })
        $range.Font.Fill.ForeColor.RGB = Convert-HexToOfficeRgb ([string]$item.fill)
        $range.Font.Fill.Transparency = 1.0 - [Math]::Min(1.0, [Math]::Max(0.0, [double]$item.opacity))
        $range.ParagraphFormat.Alignment = $(if ([string]$item.text_anchor -eq 'middle') { 2 } elseif ([string]$item.text_anchor -eq 'end') { 3 } else { 1 })
        if ($DelayMs -gt 0) { Start-Sleep -Milliseconds $DelayMs }
    }

    if ($GroupNewObjects -and $createdNames.Count -gt 1) {
        $nameArray = [object[]]$createdNames.ToArray()
        $group = $slide.Shapes.Range($nameArray).Group()
        $group.Name = "${jobId}_group"
        $createdNames.Clear()
        $createdNames.Add($group.Name)
    }

    if (-not [string]::IsNullOrWhiteSpace($OutputPptx)) {
        $target = [IO.Path]::GetFullPath($OutputPptx)
        $targetDirectory = Split-Path -Parent $target
        if ($targetDirectory) { New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null }
        $presentation.SaveAs($target)
    }

    if (-not $usage.Reused) {
        Complete-SvsUsage -Python $python -UsageId $usage.UsageId -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath
    }

    [ordered]@{
        ok = $true
        slide_index = $slide.SlideIndex
        geometry_editable = $geometryEditable
        live_text_count = @($manifest.text_elements).Count
        new_object_count = $createdNames.Count
        existing_objects_preserved = $true
        output_pptx = $(if ([string]::IsNullOrWhiteSpace($OutputPptx)) { $null } else { [IO.Path]::GetFullPath($OutputPptx) })
    } | ConvertTo-Json -Compress
}
catch {
    if ($null -ne $slide) {
        foreach ($name in @($createdNames)) {
            try { $slide.Shapes.Item($name).Delete() } catch { }
        }
    }
    if ($null -ne $usage -and -not $usage.Reused) {
        Cancel-SvsUsage -Python $python -UsageId $usage.UsageId -LicenseStatePath $LicenseStatePath -LicenseConfigPath $LicenseConfigPath
    }
    throw
}
finally {
    foreach ($comObject in @($slide, $presentation, $powerPoint)) {
        if ($null -ne $comObject -and [Runtime.InteropServices.Marshal]::IsComObject($comObject)) {
            [Runtime.InteropServices.Marshal]::ReleaseComObject($comObject) | Out-Null
        }
    }
}
