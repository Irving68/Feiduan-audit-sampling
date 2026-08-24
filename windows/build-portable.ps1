param(
    [string]$PythonVersion = "3.10.11"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root "runtime"
$PythonHome = Join-Path $Runtime "python"
$Zip = Join-Path $env:TEMP "python-$PythonVersion-embed-amd64.zip"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"

New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
if (-not (Test-Path (Join-Path $PythonHome "python.exe"))) {
    Invoke-WebRequest -Uri $PythonUrl -OutFile $Zip
    Expand-Archive -Path $Zip -DestinationPath $PythonHome -Force
}

$Pth = Get-ChildItem $PythonHome -Filter "python*._pth" | Select-Object -First 1
$PthLines = @(Get-Content $Pth.FullName) -replace '^#import site$', 'import site'
if ($PthLines -notcontains "..\..") { $PthLines += "..\.." }
$PthLines | Set-Content $Pth.FullName -Encoding ASCII

$GetPip = Join-Path $env:TEMP "get-pip.py"
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $GetPip
& (Join-Path $PythonHome "python.exe") $GetPip
if ($LASTEXITCODE -ne 0) { throw "pip 初始化失败。" }
& (Join-Path $PythonHome "python.exe") -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip 升级失败。" }
& (Join-Path $PythonHome "python.exe") -m pip install -r (Join-Path $Root "requirements-windows.txt")
if ($LASTEXITCODE -ne 0) { throw "Windows 依赖安装失败。" }

$Models = Join-Path $Root "models"
New-Item -ItemType Directory -Force -Path $Models | Out-Null
$DetModel = Join-Path $Models "PP-OCRv5_mobile_det"
$RecModel = Join-Path $Models "PP-OCRv5_mobile_rec"

if ((Test-Path $DetModel) -and (Test-Path $RecModel)) {
    Write-Host "Using bundled PaddleOCR models."
} else {
    # 仅当压缩包未附带模型时联网预热，然后从 PaddleX 缓存复制。
    & (Join-Path $PythonHome "python.exe") -c "from paddleocr import PaddleOCR; PaddleOCR(text_detection_model_name='PP-OCRv5_mobile_det',text_recognition_model_name='PP-OCRv5_mobile_rec',use_doc_orientation_classify=False,use_doc_unwarping=False,use_textline_orientation=False)"
    if ($LASTEXITCODE -ne 0) { throw "PaddleOCR 模型下载失败。请检查网络或重新复制 models 文件夹。" }

    $ModelCache = Join-Path $env:USERPROFILE ".paddlex\official_models"
    $CachedDet = Join-Path $ModelCache "PP-OCRv5_mobile_det"
    $CachedRec = Join-Path $ModelCache "PP-OCRv5_mobile_rec"
    if (-not (Test-Path $CachedDet) -or -not (Test-Path $CachedRec)) {
        throw "模型下载后未找到缓存。请重新复制项目中的 models 文件夹。"
    }
    Copy-Item $CachedDet $Models -Recurse -Force
    Copy-Item $CachedRec $Models -Recurse -Force
}

& (Join-Path $Root "audit-sampling.bat") doctor
if ($LASTEXITCODE -ne 0) { throw "环境检查失败。" }
Write-Host "WangEr Audit Sampling v1.2.0-beta Windows portable runtime is ready."
