<script setup>
import { onMounted } from 'vue'
import { useDatasetStore } from '../stores/datasetStore'
import { useModelStore } from '../stores/modelStore'
import { usePredictionStore } from '../stores/predictionStore'
import PredictionForm from '../components/PredictionForm.vue'
import PredictionResult from '../components/PredictionResult.vue'

const datasetStore = useDatasetStore()
const modelStore = useModelStore()
const predictionStore = usePredictionStore()

onMounted(() => {
  datasetStore.loadDatasets()
  modelStore.loadModels()
  predictionStore.loadTeams()
})

async function handlePredict(payload) {
  try {
    await predictionStore.predict(payload)
  } catch {
    // error already surfaced via predictionStore.predictError
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>FIFA World Cup Match Prediction</h1>
      <p class="muted">
        Predicts international football match outcomes (Home Win / Draw / Home Loss)
        using a Decision Tree trained on historical team form, goal statistics, and
        tournament context — the same methodology validated in the original Data
        Mining project notebook.
      </p>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Active dataset</h3>
        <template v-if="datasetStore.activeDataset">
          <p>
            <strong>{{ datasetStore.activeDataset.version_label }}</strong>
            <span v-if="datasetStore.activeDataset.is_builtin" class="badge badge-builtin">
              Built-in · Protected
            </span>
          </p>
          <p class="muted">{{ datasetStore.activeDataset.row_count.toLocaleString() }} matches</p>
        </template>
        <p v-else class="muted">Loading…</p>
      </div>

      <div class="card">
        <h3>Active model</h3>
        <template v-if="modelStore.activeModel">
          <p><strong>{{ modelStore.activeModel.model_id }}</strong></p>
          <p class="muted">
            World Cup Macro F1:
            {{ modelStore.activeModel.metrics?.world_cup_test?.macro_f1?.toFixed(4) ?? '—' }}
          </p>
        </template>
        <p v-else class="muted">Loading…</p>
      </div>
    </div>

    <div class="card">
      <h3>Quick prediction</h3>
      <PredictionForm
        :teams="predictionStore.teams"
        :submitting="predictionStore.predicting"
        @submit="handlePredict"
      />
      <p v-if="predictionStore.teamsError" class="error-text">{{ predictionStore.teamsError }}</p>
      <p v-if="predictionStore.predictError" class="error-text">{{ predictionStore.predictError }}</p>
    </div>

    <div v-if="predictionStore.result" class="card">
      <PredictionResult :result="predictionStore.result" />
    </div>
  </div>
</template>
