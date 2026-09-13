<script setup>
import { onMounted } from 'vue'
import { usePredictionStore } from '../stores/predictionStore'
import PredictionForm from '../components/PredictionForm.vue'
import PredictionResult from '../components/PredictionResult.vue'

const predictionStore = usePredictionStore()

onMounted(() => {
  if (!predictionStore.teamsLoaded) {
    predictionStore.loadTeams()
  }
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
      <h1>Match Prediction</h1>
      <p class="muted">
        Select two teams, a host country, and a tournament type. Host country vs.
        home team determines whether the match is treated as a neutral venue.
      </p>
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
