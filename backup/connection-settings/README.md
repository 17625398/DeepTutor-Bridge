# hermes-web-ui-switch

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/17625398/hermes-web-ui-switch.git
cd hermes-web-ui-switch
```

### 2. 应用修改到 Hermes Web UI

将本项目的代码文件复制到 Hermes Web UI 的对应位置：

```powershell
# === 客户端必要文件 ===

# Socket.IO 连接（开发模式直连 Koa，不走 Vite 代理）
copy "packages/client/src/api/hermes/chat.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\hermes\"
copy "packages/client/src/api/hermes/group-chat.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\hermes\"

# API 客户端配置
copy "packages/client/src/api/client.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\"

# 连接设置组件
copy "packages/client/src/components/hermes/settings/ConnectionSettings.vue" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\components\hermes\settings\"

# 设置页面视图
copy "packages/client/src/views/hermes/SettingsView.vue" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\views\hermes\"

# 开发模式 localStorage 初始化
copy "packages/client/src/main.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\"

# 翻译文件
copy "packages/client/src/i18n/locales/zh.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\i18n\locales\"
copy "packages/client/src/i18n/locales/en.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\i18n\locales\"

# === 服务端文件 ===

# Koa 入口（包含 .env 加载器）
copy "packages/server/src/index.ts" `
     "<HERMES_WEB_UI_DIR>\packages\server\src\"

# 代理中间件（分离部署时使用 VITE_HERMES_GATEWAY_URL 作为上游）
copy "packages/server/src/routes/hermes/proxy-handler.ts" `
     "<HERMES_WEB_UI_DIR>\packages\server\src\routes\hermes\"

# === 项目配置文件 ===

copy "vite.config.ts" "<HERMES_WEB_UI_DIR>\"
copy ".env.example" "<HERMES_WEB_UI_DIR>\"
```

### 3. 运行 Hermes Web UI

```bash
cd <HERMES_WEB_UI_DIR>
npm install
npm run dev
```

### 4. 访问设置页面

打开浏览器访问 Web UI，进入「设置」页面，即可看到新增的「连接」标签页。

### 5. 环境变量配置（可选）

可以通过 `.env` 文件配置默认的远程服务器地址：

```bash
# 在 Hermes Web UI 目录下创建 .env 文件
cd <HERMES_WEB_UI_DIR>
copy .env.example .env
```

编辑 `.env` 文件，设置远程服务器地址：

```env
# 开发模式分离部署配置
VITE_HERMES_GATEWAY_URL=http://your-server-ip:8642
VITE_HERMES_GATEWAY_API_KEY=your-api-key
```

**配置说明：**

#### 开发模式（npm run dev）

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `VITE_HERMES_GATEWAY_URL` | 远程 hermes-agent gateway 地址，Vite 代理和 Koa 代理中间件共同使用 | `http://127.0.0.1:8648` |
| `VITE_HERMES_GATEWAY_API_KEY` | 远程 agent 的 API Key，必须与 agent 端 `API_SERVER_KEY` 一致 | 空 |
| `PORT` | Web UI 服务端口 | 8648 |
| `AUTH_TOKEN` | 认证 Token（如果 agent 需要） | 空 |

设置 `VITE_HERMES_GATEWAY_URL` 后，dev 模式下：
- Vite 代理将 `/api`、`/v1`、`/health` 等 HTTP 请求转发到远程 agent
- Koa 后端的代理中间件将 Socket.IO 聊天产生的 `/v1/responses` 等请求转发到远程 agent（绕过本地 GatewayManager）
- Socket.IO 客户端直连 Koa 后端 (`127.0.0.1:8648`)，不再走 Vite 代理

#### 生产模式（hermes-web-ui start）

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `HERMES_GATEWAY_URL` | 远程 hermes-agent gateway 地址 | 空（本地模式） |
| `HERMES_GATEWAY_API_KEY` | 远程 agent 的 API Key | 空 |
| `PORT` | Web UI 服务端口 | 8648 |
| `AUTH_TOKEN` | 认证 Token | 空 |

> **注意**：环境变量配置是初始默认值，用户仍可通过设置页面的「连接」标签页在运行时动态切换部署模式。

### 6. 通过 UI 切换部署模式

Web UI 设置页面提供了**连接**标签页，可在运行时动态切换本地/分离部署模式：

1. 打开 Web UI，进入**设置**页面
2. 点击**连接**标签页
3. 选择部署模式：
   - **本地模式**：Web UI 自动启动本地 agent bridge
   - **分离部署**：输入远程服务器地址和 API Key
4. 点击**保存**生效

> **提示**：通过 `.env` 配置的远程地址会作为默认值加载，但仍可在 UI 中临时覆盖。

### 7. 测试远程连接

在分离部署模式下，可以使用「测试连接」功能验证服务器配置：

1. 输入服务器地址（如 `http://your-server-ip:8642`）
2. （可选）输入 API Key
3. 点击**测试连接**按钮
4. 等待测试结果：
   - ✅ **成功**：显示"连接测试成功"提示
   - ❌ **失败**：显示错误状态码和错误信息

> **提示**：测试连接在分离部署模式下访问服务器的 `/health` 端点，本地模式下访问 `/api/cli-status` 端点，验证服务器是否可达。

## 项目简介

**hermes-web-ui-switch** 是 Hermes Web UI 的延伸功能项目，提供在运行时动态切换**本地/分离部署模式**的能力。

通过设置页面的「连接」标签页，用户可以灵活选择：
- **本地模式**：连接本地 Hermes CLI
- **分离部署模式**：连接远程 API 服务器

## 备份文件结构

```
backup/hermes-web-ui-switch/
├── README.md                         # 项目说明文档
├── backup.ps1                        # 备份脚本
├── vite.config.ts                    # Vite 代理配置（移除 /socket.io 规则）
├── .env.example                      # 环境变量模板（更新 Koa 读取说明）
└── packages/
    ├── client/
    │   └── src/
    │       ├── main.ts               # 开发模式 localStorage 初始化
    │       ├── api/
    │       │   ├── client.ts         # API 客户端配置
    │       │   └── hermes/
    │       │       ├── chat.ts       # Socket.IO 连接（直连 Koa 后端）
    │       │       └── group-chat.ts # 群聊 Socket.IO 连接
    │       ├── components/hermes/settings/
    │       │   └── ConnectionSettings.vue
    │       ├── views/hermes/
    │       │   └── SettingsView.vue
    │       └── i18n/locales/
    │           ├── zh.ts
    │           └── en.ts
    └── server/
        └── src/
            ├── index.ts                       # Koa 入口（添加 .env 加载器）
            └── routes/hermes/
                └── proxy-handler.ts           # 代理中间件（远程上游支持）
```

## 备份文件说明

| 文件 | 路径 | 说明 |
|------|------|------|
| chat.ts | `packages/client/src/api/hermes/` | Socket.IO 客户端连接，dev 模式直连 Koa 后端 (`127.0.0.1:8648`) |
| group-chat.ts | `packages/client/src/api/hermes/` | 群聊 Socket.IO 客户端连接，同上直连 Koa |
| vite.config.ts | 项目根目录 | Vite 代理配置，移除了 `/socket.io` 规则 |
| index.ts (服务端) | `packages/server/src/` | Koa 入口，添加 .env 文件自动加载 |
| proxy-handler.ts | `packages/server/src/routes/hermes/` | 代理中间件，`resolveUpstream()` 优先使用 `VITE_HERMES_GATEWAY_URL` |
| main.ts | `packages/client/src/` | 开发模式 localStorage 初始化，仅无值时设置默认值 |
| client.ts | `packages/client/src/api/` | API 客户端配置，包含开发模式代理和服务器地址管理 |
| ConnectionSettings.vue | `packages/client/src/components/hermes/settings/` | 连接设置组件，包含本地/分离部署模式切换功能 |
| SettingsView.vue | `packages/client/src/views/hermes/` | 设置页面主视图，包含连接标签页配置 |
| zh.ts | `packages/client/src/i18n/locales/` | 中文国际化翻译文件 |
| en.ts | `packages/client/src/i18n/locales/` | 英文国际化翻译文件 |
| .env.example | 项目根目录 | 环境变量模板，更新了架构说明 |

## 工作路由流程

### 本地模式

```
┌──────────┐   HTTP (/api, /v1, /health)    ┌──────────────────┐
│  Browser ├─────────────────────────────────► Vite Dev Server  │
│ (:5173)  │  (通过 Vite 代理转发到 Koa)     │   (:5173)        │
└────┬─────┘                                  └────────┬─────────┘
     │                                                  │
     │ Socket.IO (/chat-run)                            │ proxy to
     │ (直连 Koa :8648)                                 │ Koa :8648
     │                                                  │
     ▼                                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Koa 后端 / BFF Server (:8648)               │
│                                                              │
│  ┌──────────────┐   ┌────────────────┐   ┌───────────────┐  │
│  │ Socket.IO    │   │ Koa 路由/控制器  │   │ Koa 代理中间件 │  │
│  │ /chat-run    │   │ (session,model, │   │ /api/hermes/* │  │
│  │ ChatRunSocket│   │  settings, ...) │   │ /v1/*         │  │
│  └──────┬───────┘   └───────┬────────┘   └──────┬────────┘  │
│         │                   │                    │           │
│         └───────────────────┼────────────────────┘           │
│                             │                                │
│                             ▼                                │
│                    ┌────────────────┐                        │
│                    │ GatewayManager │                        │
│                    │ getUpstream()  │                        │
│                    │ → 127.0.0.1    │                        │
│                    │   :18765       │                        │
│                    └───────┬────────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ 本地 Hermes    │
                    │ Agent Gateway  │
                    │ (:18765)       │
                    └────────────────┘
```

**说明：**
- 浏览器 **HTTP 请求**（如获取模型列表、会话管理）走 Vite 代理 → Koa → GatewayManager → 本地 Agent
- 浏览器 **Socket.IO** 直连 Koa 的 `/chat-run` 命名空间
- Koa 的 `ChatRunSocket` 收到聊天消息后，调用 `fetch('/v1/responses')`，该请求被 Koa 代理中间件拦截
- 代理中间件通过 `GatewayManager.getUpstream()` 获取本地 Agent 地址（如 `127.0.0.1:18765`），转发请求
- **不设置 `VITE_HERMES_GATEWAY_URL`**（或设为 `http://127.0.0.1:8648`）时走此路径

### 分离部署模式

```
┌──────────┐   HTTP (/api, /v1, /health)    ┌──────────────────┐
│  Browser ├─────────────────────────────────► Vite Dev Server  │
│ (:5173)  │  (通过 Vite 代理转发到远程)     │   (:5173)        │
└────┬─────┘                                  └────────┬─────────┘
     │                                                  │ proxy to
     │ Socket.IO (/chat-run)                            │ VITE_HERMES_
     │ (直连 Koa :8648)                                 │ GATEWAY_URL
     │                                                  │ (192.168.0.39)
     ▼                                                  ▼
┌─────────────────────────────────────────┐    ┌────────────────┐
│   Koa 后端 / BFF Server (:8648)          │    │  远程 Hermes  │
│                                          │    │  Agent        │
│  ┌──────────────┐  ┌────────────────┐    │    │  (:8642)      │
│  │ Socket.IO    │  │ Koa 代理中间件  │    │    │               │
│  │ /chat-run    │  │ resolveUpstream│    │    │ GET /health   │
│  │ ChatRunSocket│  │ → 直接返回     │    │    │ POST /v1/     │
│  └──────┬───────┘  │ VITE_HERMES_  │    │    │   responses   │
│         │          │ GATEWAY_URL   ├─────────►│ GET /v1/      │
│         │          │ (绕过          │    │    │   models      │
│         │          │  GatewayMgr)   │    │    │ ...           │
│         └──────────┴────────────────┘    │    └────────────────┘
└─────────────────────────────────────────┘
```

**说明：**
- 浏览器 **HTTP 请求** 走 Vite 代理 → 直接转发到远程 Agent（`VITE_HERMES_GATEWAY_URL`）
- 浏览器 **Socket.IO** 直连 Koa 的 `/chat-run` 命名空间
- Koa 的 `ChatRunSocket` 收到聊天消息后，调用 `fetch('/v1/responses')`，该请求被 Koa 代理中间件拦截
- 代理中间件的 `resolveUpstream()` 检测到 `VITE_HERMES_GATEWAY_URL` 已设置，**直接返回该地址**，绕过本地 `GatewayManager`
- 请求被转发到远程 Agent（如 `192.168.0.39:8642`），远程 Agent 响应后 Koa 通过 Socket.IO 流式返回给浏览器
- **`VITE_HERMES_GATEWAY_URL` 指向远程 Address** 时走此路径

### 关键修改点

| 组件 | 本地模式 | 分离部署模式 |
|------|---------|-------------|
| `VITE_HERMES_GATEWAY_URL` | `http://127.0.0.1:8648`（或不设置） | `http://<远程 IP>:8642` |
| `proxy-handler.ts:resolveUpstream()` | 调用 `GatewayManager.getUpstream()` → 本地 Agent | 直接返回 `VITE_HERMES_GATEWAY_URL` |
| Socket.IO 连接地址 | `http://127.0.0.1:8648/chat-run`（直连 Koa） | `http://127.0.0.1:8648/chat-run`（直连 Koa） |
| Vite HTTP 代理目标 | `http://127.0.0.1:8648`（Koa 后端） | `http://<远程 IP>:8642`（远程 Agent） |
| `.env` 加载 | Koa 尝试加载但无远程配置 | Koa 加载 `VITE_HERMES_GATEWAY_URL` 并用于代理 |

## 功能特性

- **部署模式切换**：在本地模式和分离部署模式之间动态切换
- **本地模式**：连接本地 Hermes CLI，适合开发和单机部署
- **分离部署模式**：连接远程 API 服务器，适合分布式部署场景
- **服务器配置**：配置远程服务器 URL 和 API Key
- **CLI 状态检测**：切换到本地模式时自动检测 Hermes CLI 是否可用
- **连接测试**：测试远程服务器连接是否正常，验证服务器可达性和 API Key 有效性
- **Socket.IO 直连**：开发模式浏览器 Socket.IO 直连 Koa 后端，不走 Vite 代理，避免代理导致的 WebSocket 连接问题
- **Koa 远程代理支持**：Koa 服务端启动时自动加载 `.env`，代理中间件优先使用 `VITE_HERMES_GATEWAY_URL` 作为上游地址，分离部署时直接转发请求到远程 Agent

## 升级时恢复备份

当 Hermes Web UI 升级后，按以下步骤恢复 hermes-web-ui-switch 功能：

### 步骤 1：确认备份目录

确保备份目录存在：
```
<BACKUP_DIR>\
```

### 步骤 2：复制备份文件

执行以下命令将备份文件复制到对应位置：

```powershell
# === 客户端文件 ===

copy "<BACKUP_DIR>\packages\client\src\api\hermes\chat.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\hermes\"
copy "<BACKUP_DIR>\packages\client\src\api\hermes\group-chat.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\hermes\"
copy "<BACKUP_DIR>\packages\client\src\api\client.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\api\"
copy "<BACKUP_DIR>\packages\client\src\main.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\"
copy "<BACKUP_DIR>\packages\client\src\components\hermes\settings\ConnectionSettings.vue" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\components\hermes\settings\"
copy "<BACKUP_DIR>\packages\client\src\views\hermes\SettingsView.vue" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\views\hermes\"
copy "<BACKUP_DIR>\packages\client\src\i18n\locales\zh.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\i18n\locales\"
copy "<BACKUP_DIR>\packages\client\src\i18n\locales\en.ts" `
     "<HERMES_WEB_UI_DIR>\packages\client\src\i18n\locales\"

# === 服务端文件 ===

copy "<BACKUP_DIR>\packages\server\src\index.ts" `
     "<HERMES_WEB_UI_DIR>\packages\server\src\"
copy "<BACKUP_DIR>\packages\server\src\routes\hermes\proxy-handler.ts" `
     "<HERMES_WEB_UI_DIR>\packages\server\src\routes\hermes\"

# === 项目配置文件 ===

copy "<BACKUP_DIR>\vite.config.ts" "<HERMES_WEB_UI_DIR>\"
copy "<BACKUP_DIR>\.env.example" "<HERMES_WEB_UI_DIR>\"
```

### 步骤 3：重启服务

重启 Web UI 服务使修改生效。

## 创建新备份

如需创建新的备份，运行备份脚本：

```powershell
cd <BACKUP_DIR>
.\backup.ps1
```

## 注意事项

1. 升级前建议先运行备份脚本创建最新备份
2. 恢复备份后需要重启 Web UI 服务
3. 备份文件仅包含自定义修改，不包含原始框架代码
4. 如果升级后文件结构发生变化，可能需要手动调整恢复步骤

## 项目标识

- **项目名称**: hermes-web-ui-switch
- **所属项目**: Hermes Web UI
- **功能定位**: 部署模式切换扩展功能
- **备份目录**: `<BACKUP_DIR>\`