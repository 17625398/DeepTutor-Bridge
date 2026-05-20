# hermes-web-ui 打包脚本 - 用于内网部署
# 生成包含 dist 和 node_modules 的压缩包

$ErrorActionPreference = "Stop"

$PROJECT_DIR = "d:\Doubao\DeepTutor\data\user\integrations\hermes-web-ui"
$OUTPUT_DIR = "d:\Doubao\DeepTutor\data\user\integrations"
$VERSION = "0.5.31"
$PACKAGE_NAME = "hermes-web-ui-v${VERSION}-prod"
$PACKAGE_DIR = Join-Path $OUTPUT_DIR $PACKAGE_NAME
$ZIP_FILE = Join-Path $OUTPUT_DIR "${PACKAGE_NAME}.zip"

Write-Host "=== hermes-web-ui 打包工具 ===" -ForegroundColor Cyan
Write-Host "Version: $VERSION" -ForegroundColor Cyan
Write-Host ""

# 1. Check if dist exists
if (-not (Test-Path (Join-Path $PROJECT_DIR "dist"))) {
    Write-Host "[1/5] Building project..." -ForegroundColor Yellow
    Set-Location $PROJECT_DIR
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[1/5] dist exists, skipping build" -ForegroundColor Green
}

# 2. Check if node_modules exists
if (-not (Test-Path (Join-Path $PROJECT_DIR "node_modules"))) {
    Write-Host "[2/5] Installing production dependencies..." -ForegroundColor Yellow
    Set-Location $PROJECT_DIR
    npm install --omit=dev
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Dependency installation failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[2/5] node_modules exists, skipping install" -ForegroundColor Green
}

# 3. Create package directory
Write-Host "[3/5] Creating package directory..." -ForegroundColor Yellow
if (Test-Path $PACKAGE_DIR) {
    Remove-Item -Recurse -Force $PACKAGE_DIR
}
New-Item -ItemType Directory -Path $PACKAGE_DIR -Force | Out-Null

# 4. Copy necessary files
Write-Host "[4/5] Copying files..." -ForegroundColor Yellow
$itemsToCopy = @(
    "dist",
    "node_modules",
    "bin",
    "package.json",
    ".env.example"
)

foreach ($item in $itemsToCopy) {
    $src = Join-Path $PROJECT_DIR $item
    $dst = Join-Path $PACKAGE_DIR $item
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Recurse -Force
        Write-Host "  Copied: $item" -ForegroundColor Gray
    } else {
        Write-Host "  Skipped (not found): $item" -ForegroundColor DarkGray
    }
}

# Create .env template
$envLines = @(
    "# hermes-web-ui environment configuration",
    "# Copy this file to .env and modify values",
    "",
    "# ============================",
    "# Remote deployment config",
    "# ============================",
    "",
    "# Remote hermes-agent address (gateway port, default 8642)",
    "HERMES_GATEWAY_URL=http://192.168.0.39:8642",
    "",
    "# Remote agent API Key (must match API_SERVER_KEY in remote agent config.yaml)",
    "HERMES_GATEWAY_API_KEY=your-secret-key",
    "",
    "# ============================",
    "# Other optional config",
    "# ============================",
    "",
    "# Web UI service port",
    "# PORT=8648",
    "",
    "# Auth Token",
    "AUTH_TOKEN=123456"
)
$envLines -join "`n" | Out-File -FilePath (Join-Path $PACKAGE_DIR ".env") -Encoding utf8
Write-Host "  Created: .env template" -ForegroundColor Gray

# Create start.bat
$startLines = @(
    "@echo off",
    "echo ========================================",
    "echo   hermes-web-ui startup script",
    "echo ========================================",
    "echo.",
    "",
    "REM Read environment variables from .env file",
    "for /f ""tokens=1,* delims=="" %%a in (.env) do (",
    "    if not ""%%a""=="""" (",
    "        if not ""%%a:~0,1""==""#"" (",
    "            set %%a=%%b",
    "        )",
    "    )",
    ")",
    "",
    "echo Starting hermes-web-ui...",
    "echo URL: http://localhost:8648",
    "echo.",
    "",
    "node dist\server\index.js",
    "",
    "pause"
)
$startLines -join "`n" | Out-File -FilePath (Join-Path $PACKAGE_DIR "start.bat") -Encoding utf8
Write-Host "  Created: start.bat" -ForegroundColor Gray

# Create README.md
$readmeLines = @(
    "# hermes-web-ui v${VERSION}",
    "",
    "## Quick Start",
    "",
    "1. Modify .env file to configure remote agent address and API Key",
    "2. Double-click start.bat to start the service",
    "3. Visit http://localhost:8648",
    "",
    "## Environment Variables",
    "",
    "- HERMES_GATEWAY_URL: Remote hermes-agent address",
    "- HERMES_GATEWAY_API_KEY: Remote agent API Key",
    "- AUTH_TOKEN: Web UI auth token",
    "- PORT: Web UI service port (default 8648)",
    "",
    "## Manual Start",
    "",
    "Windows PowerShell:",
    "`$env:HERMES_GATEWAY_URL=`"http://192.168.0.39:8642`"",
    "`$env:HERMES_GATEWAY_API_KEY=`"your-api-key`"",
    "node dist\server\index.js",
    "",
    "Linux/Mac:",
    "HERMES_GATEWAY_URL=http://192.168.0.39:8642 HERMES_GATEWAY_API_KEY=your-api-key node dist/server/index.js"
)
$readmeLines -join "`n" | Out-File -FilePath (Join-Path $PACKAGE_DIR "README.md") -Encoding utf8
Write-Host "  Created: README.md" -ForegroundColor Gray

# 5. Compress
Write-Host "[5/5] Compressing..." -ForegroundColor Yellow
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}
Compress-Archive -Path $PACKAGE_DIR -DestinationPath $ZIP_FILE -Force

# Clean up temp directory
Remove-Item -Recurse -Force $PACKAGE_DIR

# Show results
$zipSize = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host ""
Write-Host "=== Package Complete ===" -ForegroundColor Green
Write-Host "Output file: $ZIP_FILE" -ForegroundColor Green
Write-Host "File size: ${zipSize} MB" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment instructions:" -ForegroundColor Cyan
Write-Host "1. Copy the zip file to the intranet server" -ForegroundColor White
Write-Host "2. Extract the zip file" -ForegroundColor White
Write-Host "3. Modify .env file configuration" -ForegroundColor White
Write-Host "4. Double-click start.bat to start the service" -ForegroundColor White
