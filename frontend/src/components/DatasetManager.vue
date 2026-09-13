<script setup>
import { onMounted, ref } from 'vue'
import { useDatasetStore } from '../stores/datasetStore'

const store = useDatasetStore()
const fileInput = ref(null)
const actionError = ref(null)
const actionBusyId = ref(null)

onMounted(() => {
  store.loadDatasets()
})

async function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  actionError.value = null
  try {
    await store.uploadDataset(file)
  } catch (error) {
    actionError.value = error.message
  } finally {
    event.target.value = ''
  }
}

async function activate(dataset) {
  actionError.value = null
  actionBusyId.value = dataset.id
  try {
    await store.activateDataset(dataset.id)
  } catch (error) {
    actionError.value = error.message
  } finally {
    actionBusyId.value = null
  }
}

async function remove(dataset) {
  if (!confirm(`Delete dataset "${dataset.name}" (${dataset.version_label})?`)) return
  actionError.value = null
  actionBusyId.value = dataset.id
  try {
    await store.deleteDataset(dataset.id)
  } catch (error) {
    actionError.value = error.message
  } finally {
    actionBusyId.value = null
  }
}
</script>

<template>
  <div class="dataset-manager">
    <div class="card">
      <h3>Upload a new dataset version</h3>
      <p class="muted">
        Uploading never modifies the built-in dataset — it always creates a new version
        that you must activate explicitly before it affects predictions or training.
      </p>
      <div class="requirements">
        <p><strong>Required CSV format</strong> (header row, exactly these 9 columns, any order in the file is fine as long as the names match):</p>
        <table class="spec-table">
          <thead>
            <tr><th>Column</th><th>Type</th><th>Notes</th></tr>
          </thead>
          <tbody>
            <tr><td><code>date</code></td><td>date</td><td><code>YYYY-MM-DD</code> or <code>YYYY/M/D</code> (year first, unambiguous)</td></tr>
            <tr><td><code>home_team</code></td><td>text</td><td>Non-empty; must differ from away_team</td></tr>
            <tr><td><code>away_team</code></td><td>text</td><td>Non-empty; must differ from home_team</td></tr>
            <tr><td><code>home_score</code></td><td>integer</td><td>≥ 0; leave blank only for a not-yet-played fixture</td></tr>
            <tr><td><code>away_score</code></td><td>integer</td><td>≥ 0; leave blank only for a not-yet-played fixture</td></tr>
            <tr><td><code>tournament</code></td><td>text</td><td>e.g. <code>Friendly</code>, <code>FIFA World Cup</code>, <code>FIFA World Cup qualification</code> — anything else is grouped as "Other Competitive"</td></tr>
            <tr><td><code>city</code></td><td>text</td><td>Host city</td></tr>
            <tr><td><code>country</code></td><td>text</td><td>Host country</td></tr>
            <tr><td><code>neutral</code></td><td>boolean</td><td><code>TRUE</code>/<code>FALSE</code> — whether the match was played at a neutral venue</td></tr>
          </tbody>
        </table>
        <p class="example">Example row: <code>2024-06-14,Germany,Scotland,5,1,FIFA World Cup,Munich,Germany,FALSE</code></p>
        <p class="muted">
          Files are checked for exact duplicate rows, non-numeric or negative scores, blank
          team names, and unparseable dates before they can be activated — you'll see the
          exact problems listed below after upload if validation fails.
        </p>
      </div>
      <input ref="fileInput" type="file" accept=".csv" @change="handleFileChange" :disabled="store.uploading" />
      <p v-if="store.uploading" class="muted">Uploading and validating…</p>
      <p v-if="actionError" class="error-text">{{ actionError }}</p>
      <div v-if="store.lastUploadResult && !store.uploading" class="upload-result">
        <p>
          <strong>{{ store.lastUploadResult.dataset.version_label }}</strong> —
          <span
            class="badge"
            :class="store.lastUploadResult.dataset.validation_status === 'valid' ? 'badge-valid' : 'badge-invalid'"
          >
            {{ store.lastUploadResult.dataset.validation_status }}
          </span>
        </p>
        <ul v-if="store.lastUploadResult.validation_issues.length" class="issues">
          <li v-for="issue in store.lastUploadResult.validation_issues" :key="issue">{{ issue }}</li>
        </ul>
      </div>
    </div>

    <div class="card">
      <h3>Dataset versions</h3>
      <p v-if="store.loading" class="muted">Loading…</p>
      <p v-else-if="store.error" class="error-text">{{ store.error }}</p>
      <table v-else>
        <thead>
          <tr>
            <th>Version</th>
            <th>Rows</th>
            <th>Status</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dataset in store.datasets" :key="dataset.id">
            <td>
              {{ dataset.version_label }}
              <span v-if="dataset.is_builtin" class="badge badge-builtin">Built-in · Protected</span>
              <span v-if="dataset.is_active" class="badge badge-active">Active</span>
            </td>
            <td>{{ dataset.row_count.toLocaleString() }}</td>
            <td>
              <span class="badge" :class="dataset.validation_status === 'valid' ? 'badge-valid' : 'badge-invalid'">
                {{ dataset.validation_status }}
              </span>
            </td>
            <td class="muted">{{ new Date(dataset.created_at).toLocaleString() }}</td>
            <td class="actions">
              <button
                class="secondary"
                :disabled="dataset.is_active || dataset.validation_status !== 'valid' || actionBusyId === dataset.id"
                @click="activate(dataset)"
              >
                Activate
              </button>
              <button
                v-if="!dataset.is_builtin"
                class="danger"
                :disabled="dataset.is_active || actionBusyId === dataset.id"
                @click="remove(dataset)"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.badge {
  margin-left: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.upload-result {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.issues {
  margin: 8px 0 0;
  padding-left: 18px;
  color: var(--color-danger);
  font-size: 0.85rem;
}

.requirements {
  margin-bottom: 16px;
  padding: 14px 16px;
  background: var(--color-surface-raised);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.spec-table {
  font-size: 0.8rem;
  margin: 8px 0;
}

.spec-table th, .spec-table td {
  padding: 5px 8px;
}

.example {
  font-size: 0.8rem;
  word-break: break-all;
}
</style>
