<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { NSelect, NInput, NButton, useMessage } from "naive-ui";
import { useI18n } from "vue-i18n";
import { setServerUrl, getBaseUrlValue, setApiKey, getApiKey, clearApiKey } from "@/api/client";

const { t } = useI18n();
const message = useMessage();

const deployMode = ref<"local" | "remote">("local");
const serverUrl = ref("");
const apiKey = ref("");
const showApiKey = ref(false);

const isRemote = computed(() => deployMode.value === "remote");

onMounted(() => {
  const url = getBaseUrlValue();
  serverUrl.value = url;
  deployMode.value = url ? "remote" : "local";
  apiKey.value = getApiKey();
});

function handleModeChange(mode: "local" | "remote") {
  deployMode.value = mode;
  if (mode === "local") {
    serverUrl.value = "";
    setServerUrl("");
    message.success(t("settings.connection.switchToLocal"));
  }
}

function handleUrlSave() {
  if (!serverUrl.value.trim()) {
    message.error(t("settings.connection.urlRequired"));
    return;
  }
  let url = serverUrl.value.trim();
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "http://" + url;
  }
  url = url.replace(/\/+$/, "");
  setServerUrl(url);
  message.success(t("settings.saved"));
}

function handleApiKeySave() {
  if (!apiKey.value.trim()) {
    clearApiKey();
    message.success(t("settings.saved"));
    return;
  }
  setApiKey(apiKey.value.trim());
  message.success(t("settings.saved"));
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

    <div v-else class="local-hint">
      {{ t("settings.connection.localHint") }}
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
