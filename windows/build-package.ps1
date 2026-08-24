param(
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SourceSkill = $Root

# Keep this source file ASCII-only for Windows PowerShell 5.1 compatibility.
# Unicode code points below spell the Chinese folder name for package archives.
if ([string]::IsNullOrWhiteSpace($Output)) {
    $Output = -join @([char]0x538B, [char]0x7F29, [char]0x5305)
}

$PackageRoot = Join-Path $Root $Output
$PackageName = "WangEr Audit Sampling v1.2.0-beta"
$ZipPath = Join-Path $PackageRoot "WangEr-Audit-Sampling-Windows.zip"
$StagingRoot = Join-Path $env:SystemDrive "WANGERAUDITPKG"
$PackageDir = Join-Path $StagingRoot $PackageName

if (-not (Test-Path (Join-Path $Root "runtime\python\python.exe"))) {
    throw "Portable Python is missing. Run windows\build-portable.ps1 first."
}
if (-not (Test-Path (Join-Path $Root "models\PP-OCRv5_mobile_det")) -or -not (Test-Path (Join-Path $Root "models\PP-OCRv5_mobile_rec"))) {
    throw "Local PaddleOCR models are missing."
}

New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
if (Test-Path $StagingRoot) { Remove-Item $StagingRoot -Recurse -Force }
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

Copy-Item (Join-Path $SourceSkill "SKILL.md") $PackageDir
Copy-Item (Join-Path $SourceSkill "agents") $PackageDir -Recurse
Copy-Item (Join-Path $Root "README.md") $PackageDir
Copy-Item (Join-Path $Root "VERSION") $PackageDir
Copy-Item (Join-Path $Root "LICENSE") $PackageDir
Copy-Item (Join-Path $Root "THIRD_PARTY_NOTICES.md") $PackageDir
Copy-Item (Join-Path $Root "docs\privacy.md") (Join-Path $PackageDir "PRIVACY.md")
New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "engine") | Out-Null
Copy-Item (Join-Path $Root "audit_sampling") (Join-Path $PackageDir "engine") -Recurse
Copy-Item (Join-Path $Root "audit-sampling.bat") (Join-Path $PackageDir "engine")
Copy-Item (Join-Path $Root "agent-output.schema.json") (Join-Path $PackageDir "engine")
Copy-Item (Join-Path $Root "requirements-windows.txt") (Join-Path $PackageDir "engine")
Copy-Item (Join-Path $Root "models") (Join-Path $PackageDir "engine") -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "engine\runtime") | Out-Null
$PythonSource = Join-Path $Root "runtime\python"
$PythonTarget = Join-Path $PackageDir "engine\runtime\python"
New-Item -ItemType Directory -Force -Path $PythonTarget | Out-Null
$RoboLog = Join-Path $env:TEMP "audit-sampling-robocopy.log"
& robocopy $PythonSource $PythonTarget /E /XD __pycache__ /XF *.pyc *.pyo /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /LOG:$RoboLog | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "Portable Python copy failed. See $RoboLog"
}

Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -CompressionLevel Optimal
Remove-Item $StagingRoot -Recurse -Force
Write-Host "Package created: $ZipPath"
