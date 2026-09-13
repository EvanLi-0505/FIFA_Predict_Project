<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../services/api'

const isDesktop = ref(null) // null = still checking, true/false once known
const systemInfo = ref(null)
const infoError = ref(null)

const logText = ref('')
const logLoading = ref(false)
const logError = ref(null)

const clearing = ref(false)
const clearError = ref(null)

const changingFolder = ref(false)
const folderError = ref(null)

// window.pywebview is only present inside the actual pywebview shell (see
// desktop_app/main.py's DesktopJsApi) — a plain browser tab pointed at the
// same URL for debugging has no native folder-picker to call. It's
// injected asynchronously after the page loads, so this is re-checked on
// the 'pywebviewready' event, not just once at mount.
const canPickFolder = ref(!!window.pywebview?.api?.choose_log_folder)
window.addEventListener('pywebviewready', () => {
  canPickFolder.value = !!window.pywebview?.api?.choose_log_folder
})

onMounted(async () => {
  try {
    systemInfo.value = await api.getSystemInfo()
    isDesktop.value = true
  } catch {
    // 404 (or any other failure) on this probe just means "not the
    // Desktop app" — see api.js's getSystemInfo doc comment.
    isDesktop.value = false
  }
})

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function loadLog() {
  logLoading.value = true
  logError.value = null
  try {
    logText.value = await api.getSystemLog(500)
  } catch (error) {
    logError.value = error.message
  } finally {
    logLoading.value = false
  }
}

async function changeLogFolder() {
  if (!canPickFolder.value) return
  folderError.value = null

  const folder = await window.pywebview.api.choose_log_folder()
  if (!folder) return // user cancelled the native dialog

  changingFolder.value = true
  try {
    await api.setLogFolder(folder)
    systemInfo.value = await api.getSystemInfo()
    logText.value = ''
  } catch (error) {
    folderError.value = error.message
  } finally {
    changingFolder.value = false
  }
}

async function clearLog() {
  if (!confirm('Clear the log file? This cannot be undone.')) return
  clearing.value = true
  clearError.value = null
  try {
    await api.clearSystemLog()
    logText.value = ''
    systemInfo.value = await api.getSystemInfo()
  } catch (error) {
    clearError.value = error.message
  } finally {
    clearing.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Settings</h1>
      <p class="muted">Application info and diagnostics.</p>
    </div>

    <div v-if="isDesktop === false" class="card">
      <p class="muted">
        Log management is a Desktop-app-only feature — this browser session
        is talking to a Web deployment, which has no local log file to show
        here (its logs go wherever the hosting platform captures stdout).
      </p>
    </div>

    <template v-else-if="isDesktop">
      <div class="card">
        <h3>Application data</h3>
        <table>
          <tbody>
            <tr>
              <td class="muted">Data directory</td>
              <td><code>{{ systemInfo.data_dir }}</code></td>
            </tr>
            <tr>
              <td class="muted">Log file</td>
              <td><code>{{ systemInfo.log_path }}</code></td>
            </tr>
            <tr>
              <td class="muted">Log size</td>
              <td>{{ formatBytes(systemInfo.log_size_bytes) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="muted">
          Everything above lives inside this app's own folder by default —
          deleting that folder removes it completely, nothing is left
          elsewhere on your system. The log also rotates automatically
          (older entries are dropped once it reaches a few MB), so it never
          grows unbounded — but you can also clear it immediately below.
        </p>
        <button v-if="canPickFolder" class="secondary" :disabled="changingFolder" @click="changeLogFolder">
          {{ changingFolder ? 'Applying…' : 'Change log folder…' }}
        </button>
        <p v-if="folderError" class="error-text">{{ folderError }}</p>
      </div>

      <div class="card">
        <h3>Log</h3>
        <div class="log-actions">
          <button class="secondary" :disabled="logLoading" @click="loadLog">
            {{ logLoading ? 'Loading…' : 'View recent log' }}
          </button>
          <button class="danger" :disabled="clearing" @click="clearLog">
            {{ clearing ? 'Clearing…' : 'Clear log' }}
          </button>
        </div>
        <p v-if="logError" class="error-text">{{ logError }}</p>
        <p v-if="clearError" class="error-text">{{ clearError }}</p>
        <pre v-if="logText" class="log-view">{{ logText }}</pre>
      </div>
    </template>
  </div>
</template>

<style scoped>
table {
  margin-bottom: 12px;
}

td {
  padding: 4px 12px 4px 0;
  border: none;
}

.log-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.log-view {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  max-height: 420px;
  overflow: auto;
  font-size: 0.78rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
