<script setup>
import { onMounted, reactive, ref } from 'vue'
import {
  useModelStore,
  MODEL_TYPE_OPTIONS,
  FEATURE_VERSION_OPTIONS,
  featureVersionLabel,
} from '../stores/modelStore'
import { useDatasetStore } from '../stores/datasetStore'

const modelStore = useModelStore()
const datasetStore = useDatasetStore()

const actionError = ref(null)
const actionBusyId = ref(null)

const trainForm = reactive({
  datasetId: '',
  modelType: 'logistic_regression',
  featureVersion: 'feature_v2',
})

onMounted(() => {
  modelStore.loadModels()
  datasetStore.loadDatasets()
})

async function handleTrain() {
  if (!trainForm.datasetId) return
  actionError.value = null
  try {
    await modelStore.trainModel({
      datasetId: Number(trainForm.datasetId),
      modelType: trainForm.modelType,
      featureVersion: trainForm.featureVersion,
    })
  } catch (error) {
    actionError.value = error.message
  }
}

async function activate(model) {
  actionError.value = null
  actionBusyId.value = model.id
  try {
    await modelStore.activateModel(model.id)
  } catch (error) {
    actionError.value = error.message
  } finally {
    actionBusyId.value = null
  }
}

async function remove(model) {
  if (!confirm(`Delete model "${model.model_id}"? This also deletes its saved artifact.`)) return
  actionError.value = null
  actionBusyId.value = model.id
  try {
    await modelStore.deleteModel(model.id)
  } catch (error) {
    actionError.value = error.message
  } finally {
    actionBusyId.value = null
  }
}

function datasetLabel(datasetId) {
  const dataset = datasetStore.datasets.find((d) => d.id === datasetId)
  return dataset ? dataset.version_label : `#${datasetId}`
}

function metric(model, split, name) {
  const value = model.metrics?.[split]?.[name]
  return typeof value === 'number' ? value : null
}

function percent(value) {
  return value === null ? '—' : `${(value * 100).toFixed(1)}%`
}

function decimal(value) {
  return value === null ? '—' : value.toFixed(3)
}
</script>

<template>
  <div class="model-manager">
    <div class="card">
      <h3>Train a new model</h3>
      <p class="muted">
        Always retrains on every completed match in the chosen dataset (matching the
        source notebook's Phase 13.1 retraining step), then evaluates the held-out
        chronological split for comparison metrics.
      </p>
      <div class="grid-2">
        <div class="field">
          <label for="train-dataset">Dataset</label>
          <select id="train-dataset" v-model="trainForm.datasetId">
            <option value="" disabled>Select a dataset…</option>
            <option v-for="dataset in datasetStore.datasets" :key="dataset.id" :value="dataset.id">
              {{ dataset.version_label }} ({{ dataset.row_count.toLocaleString() }} rows)
            </option>
          </select>
        </div>
        <div class="field">
          <label for="train-model-type">Model type</label>
          <select id="train-model-type" v-model="trainForm.modelType">
            <option v-for="option in MODEL_TYPE_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
        <div class="field">
          <label for="train-feature-version">Features</label>
          <select id="train-feature-version" v-model="trainForm.featureVersion">
            <option v-for="option in FEATURE_VERSION_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>
      <button :disabled="!trainForm.datasetId || modelStore.training" @click="handleTrain">
        {{ modelStore.training ? 'Training…' : 'Train model' }}
      </button>
      <p v-if="actionError" class="error-text">{{ actionError }}</p>
    </div>

    <div class="card">
      <h3>Model versions</h3>
      <p v-if="modelStore.loading" class="muted">Loading…</p>
      <p v-else-if="modelStore.error" class="error-text">{{ modelStore.error }}</p>
      <table v-else>
        <thead>
          <tr>
            <th>Model</th>
            <th>Features</th>
            <th>Dataset</th>
            <th>Accuracy</th>
            <th>World Cup Accuracy</th>
            <th>Macro F1</th>
            <th>Trained</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="model in modelStore.models" :key="model.id">
            <td>
              {{ model.model_id }}
              <span v-if="model.is_builtin" class="badge badge-builtin">Built-in · Protected</span>
              <span v-if="model.is_active" class="badge badge-active">Active</span>
            </td>
            <td>{{ featureVersionLabel(model.feature_version) }}</td>
            <td>{{ datasetLabel(model.dataset_id) }}</td>
            <td>{{ percent(metric(model, 'overall_test', 'accuracy')) }}</td>
            <td>{{ percent(metric(model, 'world_cup_test', 'accuracy')) }}</td>
            <td>{{ decimal(metric(model, 'overall_test', 'macro_f1')) }}</td>
            <td class="muted">{{ new Date(model.created_at).toLocaleString() }}</td>
            <td class="actions">
              <button
                class="secondary"
                :disabled="model.is_active || actionBusyId === model.id"
                @click="activate(model)"
              >
                Activate
              </button>
              <button
                v-if="!model.is_builtin"
                class="danger"
                :disabled="model.is_active || actionBusyId === model.id"
                @click="remove(model)"
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
.actions {
  display: flex;
  gap: 8px;
  white-space: nowrap;
}
</style>
