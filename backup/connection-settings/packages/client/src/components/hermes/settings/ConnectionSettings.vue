<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { NSelect, NInput, NButton, useMessage, NAlert } from "naive-ui";
import { useI18n } from "vue-i18n";
import { setServerUrl, getBaseUrlValue, setApiKey, getApiKey, clearApiKey, request } from "@/api/client";

const { t } = useI18n();
const message = useMessage();

const deployMode = ref<"local" | "remote">("local");
const serverUrl = ref("");
const apiKey = ref("");
const showApiKey = ref(false);
const cliStatus = ref<{ hermes_cli_available: boolean; message?: string } | null>(null);
const cliStatusLoading = ref(true);
const testConnectionLoading = ref(false);
const testConnectionResult = ref<'success' | 'error' | null>(null);
const testConnectionMessage = ref("");

const isRemote = computed(() => deployMode.value === "remote");

async function fetchCliStatus() {
  try {
    cliStatusLoading.value = true;
    cliStatus.value = await request('/api/cli-status');
    console.log('[ConnectionSettings] CLI status fetched:', cliStatus.value);
  } catch (err) {
    console.error('[ConnectionSettings] Failed to fetch CLI status:', err);
    cliStatus.value = { hermes_cli_available: false, message: 'Failed to check Hermes CLI availability' };
  } finally {
    cliStatusLoading.value = false;
  }
}

onMounted(async () => {
  const url = getBaseUrlValue();
  console.log('[ConnectionSettings] onMounted - initial URL from localStorage:', url);
  serverUrl.value = url;
  deployMode.value = url ? "remote" : "local";
  apiKey.value = getApiKey();
  console.log('[ConnectionSettings] onMounted - deployMode set to:', deployMode.value);
  console.log('[ConnectionSettings] onMounted - apiKey loaded:', apiKey.value ? 'yes (masked)' : 'no');
  
  // Fetch CLI status only in local mode (remote servers don't have this endpoint)
  if (deployMode.value === "local") {
    await fetchCliStatus();
  }
});

async function handleModeChange(mode: "local" | "remote") {
  console.log('[ConnectionSettings] handleModeChange - called with mode:', mode);
  console.log('[ConnectionSettings] handleModeChange - previous mode:', deployMode.value);
  console.log('[ConnectionSettings] handleModeChange - current serverUrl:', serverUrl.value);
  console.log('[ConnectionSettings] handleModeChange - current apiKey:', getApiKey() ? 'yes (masked)' : 'no');

  // 切出远程模式前，先把当前输入的 URL 持久化到 localStorage
  if (deployMode.value === "remote" && serverUrl.value.trim()) {
    let url = serverUrl.value.trim();
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "http://" + url;
    }
    url = url.replace(/\/+$/, "");
    setServerUrl(url);
    console.log('[ConnectionSettings] handleModeChange - persisted URL before mode switch:', url);
  }

  deployMode.value = mode;

  if (mode === "local") {
    console.log('[ConnectionSettings] handleModeChange - switching to LOCAL mode');
    const oldUrl = serverUrl.value;
    serverUrl.value = "";
    // 不清空 localStorage，保留配置以便切回远程模式时恢复
    console.log('[ConnectionSettings] handleModeChange - cleared serverUrl from:', oldUrl, 'to empty');
    console.log('[ConnectionSettings] handleModeChange - localStorage hermes_server_url now:', getBaseUrlValue());
    
    await fetchCliStatus();
    
    if (cliStatus.value && !cliStatus.value.hermes_cli_available) {
      message.warning(t("settings.connection.localModeCliMissing"));
      console.log('[ConnectionSettings] Warning: Local mode selected but hermes CLI not available');
    } else {
      message.success(t("settings.connection.switchToLocal"));
    }
    console.log('[ConnectionSettings] handleModeChange - success message shown');
  } else {
    console.log('[ConnectionSettings] handleModeChange - switching to REMOTE mode');
    // 从 localStorage 恢复已保存的远程 URL
    if (!serverUrl.value.trim()) {
      const savedUrl = getBaseUrlValue();
      if (savedUrl) {
        serverUrl.value = savedUrl;
      }
    }
    console.log('[ConnectionSettings] handleModeChange - serverUrl input value:', serverUrl.value);
    console.log('[ConnectionSettings] handleModeChange - apiKey input value:', apiKey.value ? 'yes (masked)' : 'no');
    
    if (serverUrl.value.trim()) {
      let url = serverUrl.value.trim();
      if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = "http://" + url;
      }
      url = url.replace(/\/+$/, "");
      setServerUrl(url);
      console.log('[ConnectionSettings] handleModeChange - auto-saved serverUrl:', url);
    }
    
    if (apiKey.value.trim()) {
      setApiKey(apiKey.value.trim());
      console.log('[ConnectionSettings] handleModeChange - auto-saved apiKey');
    }
    
    message.success(t("settings.connection.switchToRemote"));
    console.log('[ConnectionSettings] handleModeChange - success message shown');
  }

  console.log('[ConnectionSettings] handleModeChange - final deployMode:', deployMode.value);
  console.log('[ConnectionSettings] handleModeChange - final isRemote:', isRemote.value);
}

function handleUrlSave() {
  console.log('[ConnectionSettings] handleUrlSave - called');
  console.log('[ConnectionSettings] handleUrlSave - raw serverUrl:', serverUrl.value);

  if (!serverUrl.value.trim()) {
    console.log('[ConnectionSettings] handleUrlSave - validation failed: empty URL');
    message.error(t("settings.connection.urlRequired"));
    return;
  }

  let url = serverUrl.value.trim();
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    console.log('[ConnectionSettings] handleUrlSave - auto-prefixing http://');
    url = "http://" + url;
  }
  url = url.replace(/\/+$/, "");
  console.log('[ConnectionSettings] handleUrlSave - normalized URL:', url);

  setServerUrl(url);
  console.log('[ConnectionSettings] handleUrlSave - setServerUrl called');
  console.log('[ConnectionSettings] handleUrlSave - verify localStorage:', getBaseUrlValue());

  message.success(t("settings.saved") + ' ' + t("settings.connection.pageRefresh"));
  console.log('[ConnectionSettings] handleUrlSave - success message shown');
  
  // 刷新页面使配置生效
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

function handleApiKeySave() {
  console.log('[ConnectionSettings] handleApiKeySave - called');
  console.log('[ConnectionSettings] handleApiKeySave - apiKey value:', apiKey.value ? 'yes (masked)' : 'empty');

  if (!apiKey.value.trim()) {
    console.log('[ConnectionSettings] handleApiKeySave - clearing API key');
    clearApiKey();
    console.log('[ConnectionSettings] handleApiKeySave - verify localStorage after clear:', getApiKey() ? 'yes' : 'no');
    message.success(t("settings.saved"));
    return;
  }

  setApiKey(apiKey.value.trim());
  console.log('[ConnectionSettings] handleApiKeySave - setApiKey called');
  console.log('[ConnectionSettings] handleApiKeySave - verify localStorage:', getApiKey() ? 'yes (masked)' : 'no');
  message.success(t("settings.saved"));
  console.log('[ConnectionSettings] handleApiKeySave - success message shown');
}

async function testConnection() {
  console.log('[ConnectionSettings] testConnection - called');

  testConnectionLoading.value = true;
  testConnectionResult.value = null;
  testConnectionMessage.value = "";

  try {
    let testUrl: string;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (isRemote.value) {
      // 远程模式：测试远程服务器
      if (!serverUrl.value.trim()) {
        console.log('[ConnectionSettings] testConnection - validation failed: empty URL');
        message.error(t("settings.connection.urlRequired"));
        return;
      }

      let url = serverUrl.value.trim();
      if (!url.startsWith("http://") && !url.startsWith("https://")) {
        url = "http://" + url;
      }
      url = url.replace(/\/+$/, "");

      if (import.meta.env.DEV) {
        // 开发环境：通过 Vite 代理避免 CORS 问题
        // 代理目标由 .env 中的 VITE_HERMES_GATEWAY_URL 控制
        // 远程 agent 的 /health 已被代理规则转发
        testUrl = '/health';
        console.log('[ConnectionSettings] testConnection - dev mode, testing remote via proxy to', testUrl);
      } else {
        // 生产环境：直接请求远程 URL
        testUrl = `${url}/health`;
        console.log('[ConnectionSettings] testConnection - testing remote URL:', testUrl);
      }

      if (apiKey.value.trim()) {
        headers['Authorization'] = `Bearer ${apiKey.value.trim()}`;
        console.log('[ConnectionSettings] testConnection - using API key');
      }
    } else {
      // 本地模式：测试本地服务
      if (import.meta.env.DEV) {
        // 开发环境：通过 Vite 代理避免 CORS 问题
        testUrl = '/api/cli-status';
        console.log('[ConnectionSettings] testConnection - dev mode, testing local via proxy');
      } else {
        // 生产环境：直接请求本地服务
        testUrl = 'http://127.0.0.1:8648/api/cli-status';
        console.log('[ConnectionSettings] testConnection - testing local directly');
      }
    }

    const response = await fetch(testUrl, {
      method: 'GET',
      headers: headers,
      timeout: 10000,
    });

    if (response.ok) {
      const data = await response.json();
      console.log('[ConnectionSettings] testConnection - success:', data);
      testConnectionResult.value = 'success';
      
      if (isRemote.value) {
        testConnectionMessage.value = t("settings.connection.testSuccess");
        message.success(t("settings.connection.testSuccess"));
      } else {
        testConnectionMessage.value = data.hermes_cli_available 
          ? t("settings.connection.testSuccess") + ' - Hermes CLI 可用'
          : t("settings.connection.testFailed") + ' - Hermes CLI 不可用';
        message[data.hermes_cli_available ? 'success' : 'warning'](testConnectionMessage.value);
      }
    } else {
      const text = await response.text().catch(() => '');
      console.error('[ConnectionSettings] testConnection - failed:', response.status, text);
      testConnectionResult.value = 'error';
      testConnectionMessage.value = `${t("settings.connection.testFailed")}: ${response.status} - ${text || response.statusText}`;
      message.error(testConnectionMessage.value);
    }
  } catch (error: any) {
    console.error('[ConnectionSettings] testConnection - error:', error);
    testConnectionResult.value = 'error';
    testConnectionMessage.value = `${t("settings.connection.testError")}: ${error.message || 'Unknown error'}`;
    message.error(testConnectionMessage.value);
  } finally {
    testConnectionLoading.value = false;
    console.log('[ConnectionSettings] testConnection - completed');
  }
}
</script>

<template>
  <section class="settings-section">
    <div class="mode-selector">
      <NSelect
        :value="deployMode"
        :options="[
          { label: t('settings.connection.localMode'), value: 'local' },
          { label: t('settings.connection.remoteMode'), value: 'remote' },
        ]"
        size="small"
        :consistent-menu-width="false"
        class="input-sm"
        @update:value="handleModeChange"
      />
    </div>

    <template v-if="isRemote">
      <div class="setting-row">
        <div class="setting-info">
          <label class="setting-label">{{ t("settings.connection.serverUrl") }}</label>
          <p class="setting-hint">{{ t("settings.connection.serverUrlHint") }}</p>
        </div>
        <div class="setting-control">
          <NInput
            v-model:value="serverUrl"
            :placeholder="t('settings.connection.serverUrlPlaceholder')"
            size="small"
            class="input-sm"
          />
        </div>
      </div>
      <div class="setting-actions">
        <NButton type="primary" size="small" @click="handleUrlSave">
          {{ t("common.save") }}
        </NButton>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <label class="setting-label">{{ t("settings.connection.apiKey") }}</label>
          <p class="setting-hint">{{ t("settings.connection.apiKeyHint") }}</p>
        </div>
        <div class="setting-control">
          <NInput
            v-model:value="apiKey"
            :type="showApiKey ? 'text' : 'password'"
            :placeholder="t('settings.connection.apiKeyPlaceholder')"
            size="small"
            class="input-sm"
          />
        </div>
      </div>
      <div class="setting-actions">
        <NButton size="small" @click="showApiKey = !showApiKey">
          {{ showApiKey ? t("settings.connection.hide") : t("settings.connection.show") }}
        </NButton>
        <NButton type="primary" size="small" @click="handleApiKeySave">
          {{ t("common.save") }}
        </NButton>
      </div>

    </template>

    <div v-else>
      <div v-if="cliStatus && !cliStatus.hermes_cli_available" class="cli-warning">
        <NAlert type="warning" :title="t('settings.connection.cliUnavailableTitle')" closable>
          {{ cliStatus.message || t('settings.connection.cliUnavailableMessage') }}
        </NAlert>
      </div>
      <div class="local-hint">
        {{ t("settings.connection.localHint") }}
      </div>
    </div>

    <!-- 测试连接按钮 - 在本地和远程模式下都显示 -->
    <div class="test-section">
      <div class="test-actions">
        <NButton 
          type="success" 
          size="small" 
          :loading="testConnectionLoading"
          @click="testConnection"
          :disabled="isRemote && !serverUrl.trim()"
        >
          {{ t("settings.connection.testConnection") }}
        </NButton>
      </div>
      <div v-if="testConnectionMessage" class="test-result">
        <NAlert 
          :type="testConnectionResult === 'success' ? 'success' : 'error'" 
          :closable="true"
          class="test-alert"
        >
          {{ testConnectionMessage }}
        </NAlert>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use "@/styles/variables" as *;

.settings-section {
  margin-top: 16px;
}

.mode-selector {
  margin-bottom: 16px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid $border-light;

  &:last-child {
    border-bottom: none;
  }
}

.setting-info {
  flex: 1;
  margin-right: 16px;
}

.setting-label {
  font-size: 13px;
  color: $text-primary;
  display: block;
}

.setting-hint {
  font-size: 12px;
  color: $text-muted;
  margin-top: 2px;
}

.setting-control {
  flex-shrink: 0;
  width: 280px;
}

.setting-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 8px 0;
}

.local-hint {
  padding: 12px;
  background: rgba(0, 128, 0, 0.1);
  border-radius: 4px;
  font-size: 13px;
  color: $text-muted;
  margin-top: 8px;
}

.cli-warning {
  margin-bottom: 12px;
}

.test-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid $border-light;
}

.test-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.test-result {
  margin-top: 8px;
}

.test-alert {
  margin-bottom: 0;
}

@media (max-width: $breakpoint-mobile) {
  .setting-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .setting-info {
    margin-right: 0;
  }

  .setting-control {
    width: 100%;
  }
}
</style>
