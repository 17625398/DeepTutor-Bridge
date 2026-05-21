<#
===========================================================================
              hermes-web-ui-switch - 部署模式切换功能备份脚本
===========================================================================

一、项目简介
------------
hermes-web-ui-switch 是 Hermes Web UI 的延伸功能，提供在运行时动态切换
本地/分离部署模式的能力。

二、脚本用途
-----------
本脚本用于备份 hermes-web-ui-switch 相关的自定义代码修改，
确保在 Hermes Web UI 升级时能够保留这些修改。

三、备份文件列表
---------------
以下文件会被备份：

1. chat.ts (客户端)
   - 路径: packages/client/src/api/hermes/chat.ts
   - 说明: Socket.IO 客户端连接，开发模式直连 Koa 后端 (127.0.0.1:8648)，而非通过 Vite 代理

2. group-chat.ts
   - 路径: packages/client/src/api/hermes/group-chat.ts
   - 说明: 群聊 Socket.IO 客户端连接，同上直连 Koa 后端

3. vite.config.ts
   - 路径: vite.config.ts
   - 说明: Vite 开发代理配置，移除了 /socket.io 代理规则（因为 Socket.IO 不再经过 Vite 代理）

4. index.ts (服务端)
   - 路径: packages/server/src/index.ts
   - 说明: Koa 服务端入口，添加了 .env 文件自动加载（使得 VITE_HERMES_GATEWAY_URL 对 Koa 可见）

5. proxy-handler.ts
   - 路径: packages/server/src/routes/hermes/proxy-handler.ts
   - 说明: Koa 代理中间件，resolveUpstream() 优先使用 VITE_HERMES_GATEWAY_URL 作为上游地址（分离部署时直接转发到远程 Agent），不再依赖本地 GatewayManager

6. main.ts
   - 路径: packages/client/src/main.ts
   - 说明: 开发模式 localStorage 初始化，仅当 localStorage 无值时设置默认值，保留用户已配置的连接设置

7. client.ts
   - 路径: packages/client/src/api/client.ts
   - 说明: API 客户端配置，包含开发模式代理和服务器地址管理

8. ConnectionSettings.vue
   - 路径: packages/client/src/components/hermes/settings/ConnectionSettings.vue
   - 说明: 连接设置组件，包含本地/分离部署模式切换功能

9. SettingsView.vue
   - 路径: packages/client/src/views/hermes/SettingsView.vue
   - 说明: 设置页面主视图，包含连接标签页配置

10. zh.ts
    - 路径: packages/client/src/i18n/locales/zh.ts
    - 说明: 中文国际化翻译文件（含连接设置相关翻译）

11. en.ts
    - 路径: packages/client/src/i18n/locales/en.ts
    - 说明: 英文国际化翻译文件（含连接设置相关翻译）

12. .env.example
    - 路径: .env.example
    - 说明: 环境变量模板，更新了架构说明（Koa 也读取 VITE_HERMES_GATEWAY_URL，Socket.IO 直连 Koa）

四、升级时恢复备份
------------------
当 Hermes Web UI 升级后，按以下步骤恢复 hermes-web-ui-switch 功能：

1. 确保备份目录存在: <BACKUP_DIR>/

2. 手动复制备份文件到对应位置：

   REM === 客户端文件 ===
   copy "<BACKUP_DIR>/packages/client/src/api/hermes/chat.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/api/hermes/"
   copy "<BACKUP_DIR>/packages/client/src/api/hermes/group-chat.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/api/hermes/"
   copy "<BACKUP_DIR>/packages/client/src/api/client.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/api/"
   copy "<BACKUP_DIR>/packages/client/src/main.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/"
   copy "<BACKUP_DIR>/packages/client/src/components/hermes/settings/ConnectionSettings.vue" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/components/hermes/settings/"
   copy "<BACKUP_DIR>/packages/client/src/views/hermes/SettingsView.vue" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/views/hermes/"
   copy "<BACKUP_DIR>/packages/client/src/i18n/locales/zh.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/i18n/locales/"
   copy "<BACKUP_DIR>/packages/client/src/i18n/locales/en.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/client/src/i18n/locales/"

   REM === 服务端文件 ===
   copy "<BACKUP_DIR>/packages/server/src/index.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/server/src/"
   copy "<BACKUP_DIR>/packages/server/src/routes/hermes/proxy-handler.ts" ^
        "<HERMES_WEB_UI_DIR>/packages/server/src/routes/hermes/"

   REM === 项目配置文件 ===
   copy "<BACKUP_DIR>/vite.config.ts" "<HERMES_WEB_UI_DIR>/"
   copy "<BACKUP_DIR>/.env.example" "<HERMES_WEB_UI_DIR>/"

3. 重启 Web UI 服务使修改生效

五、执行备份
------------
直接运行此脚本即可创建备份：
.\backup.ps1

> **注意**：首次运行前请修改脚本中的 `$sourceBase` 和 `$backupBase` 变量，设置为您的实际路径。

备份目录: <BACKUP_DIR>/

===========================================================================
#>

# ========== 请根据您的实际环境修改以下路径 ==========
# Hermes Web UI 项目目录
$sourceBase = "D:\Doubao\DeepTutor\data\user\integrations\hermes-web-ui"
# 备份目录
$backupBase = "D:\Doubao\DeepTutor\backup\connection-settings"
# ====================================================

Write-Host "==========================================================================="
Write-Host "              hermes-web-ui-switch - 部署模式切换功能备份脚本"
Write-Host "==========================================================================="
Write-Host ""

# 创建备份目录
if (-not (Test-Path $backupBase)) {
    New-Item -ItemType Directory -Path $backupBase -Force | Out-Null
    Write-Host "创建备份目录: $backupBase"
}

# 备份的文件列表
$filesToBackup = @(
    # Socket.IO 直连 Koa 后端（不再走 Vite 代理）
    "packages/client/src/api/hermes/chat.ts",
    "packages/client/src/api/hermes/group-chat.ts",
    # Vite 代理配置（移除了 /socket.io 规则）
    "vite.config.ts",
    # Koa 后端 .env 加载器 + 代理中间件远程上游支持
    "packages/server/src/index.ts",
    "packages/server/src/routes/hermes/proxy-handler.ts",
    # 客户端连接设置
    "packages/client/src/main.ts",
    "packages/client/src/api/client.ts",
    "packages/client/src/components/hermes/settings/ConnectionSettings.vue",
    "packages/client/src/views/hermes/SettingsView.vue",
    # 国际化翻译
    "packages/client/src/i18n/locales/zh.ts",
    "packages/client/src/i18n/locales/en.ts",
    # 环境变量文档
    ".env.example"
)

Write-Host "开始备份文件..."
Write-Host ""

foreach ($file in $filesToBackup) {
    $sourcePath = Join-Path $sourceBase $file
    $backupPath = Join-Path $backupBase $file
    
    if (Test-Path $sourcePath) {
        # 创建目标目录
        $backupDir = Split-Path $backupPath -Parent
        if (-not (Test-Path $backupDir)) {
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        }
        
        # 复制文件
        Copy-Item -Path $sourcePath -Destination $backupPath -Force
        Write-Host "✓ 已备份: $file"
    } else {
        Write-Host "✗ 文件不存在: $file"
    }
}

Write-Host ""
Write-Host "==========================================================================="
Write-Host "备份完成！"
Write-Host "备份目录: $backupBase"
Write-Host ""
Write-Host "升级时恢复方法:"
Write-Host "1. 将备份文件复制到 hermes-web-ui 项目对应位置"
Write-Host ""
Write-Host "   必要文件（连接设置 + 代理配置 + Socket.IO 直连）:"
Write-Host "   - packages/client/src/api/hermes/chat.ts"
Write-Host "   - packages/client/src/api/hermes/group-chat.ts"
Write-Host "   - packages/client/src/api/client.ts"
Write-Host "   - packages/client/src/components/hermes/settings/ConnectionSettings.vue"
Write-Host "   - packages/client/src/views/hermes/SettingsView.vue"
Write-Host "   - packages/client/src/main.ts"
Write-Host "   - packages/client/src/i18n/locales/zh.ts"
Write-Host "   - packages/client/src/i18n/locales/en.ts"
Write-Host ""
Write-Host "   服务端文件（分离部署代理 + .env 加载）:"
Write-Host "   - packages/server/src/index.ts"
Write-Host "   - packages/server/src/routes/hermes/proxy-handler.ts"
Write-Host ""
Write-Host "   项目配置文件:"
Write-Host "   - vite.config.ts"
Write-Host "   - .env.example"
Write-Host ""
Write-Host "2. 重启 Web UI 服务"
Write-Host "==========================================================================="