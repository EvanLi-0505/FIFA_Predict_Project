<script setup>
import { reactive, computed, watch } from 'vue'
import TeamSelector from './TeamSelector.vue'
import { TOURNAMENT_OPTIONS } from '../stores/predictionStore'

const props = defineProps({
  teams: { type: Array, default: () => [] },
  submitting: { type: Boolean, default: false },
  submitLabel: { type: String, default: 'Predict' },
  submittingLabel: { type: String, default: 'Predicting…' },
  // { homeTeam, awayTeam, hostCountry, tournament } — overwrites the fields
  // whenever a new object is passed (e.g. picking a history record).
  prefill: { type: Object, default: null },
})

const emit = defineEmits(['submit'])

const form = reactive({
  homeTeam: '',
  awayTeam: '',
  hostCountry: '',
  tournament: 'FIFA World Cup',
})

watch(
  () => props.prefill,
  (values) => {
    if (values) Object.assign(form, values)
  },
)

const isValid = computed(
  () =>
    form.homeTeam.trim() !== '' &&
    form.awayTeam.trim() !== '' &&
    form.hostCountry.trim() !== '' &&
    form.homeTeam.trim() !== form.awayTeam.trim(),
)

function useHomeTeamAsHost() {
  form.hostCountry = form.homeTeam
}

function handleSubmit() {
  if (!isValid.value) return
  emit('submit', {
    homeTeam: form.homeTeam.trim(),
    awayTeam: form.awayTeam.trim(),
    hostCountry: form.hostCountry.trim(),
    tournament: form.tournament,
  })
}
</script>

<template>
  <form class="prediction-form" @submit.prevent="handleSubmit">
    <div class="grid-2">
      <TeamSelector v-model="form.homeTeam" label="Home Team" list-id="home-team" :teams="teams" />
      <TeamSelector v-model="form.awayTeam" label="Away Team" list-id="away-team" :teams="teams" />
    </div>

    <div class="grid-2">
      <div>
        <div class="host-label-row">
          <label for="host-country">Host Country</label>
          <button type="button" class="link-button" @click="useHomeTeamAsHost">
            same as home team
          </button>
        </div>
        <TeamSelector
          v-model="form.hostCountry"
          label=""
          list-id="host-country"
          :teams="teams"
          placeholder="Type or pick a host country"
        />
      </div>

      <div class="field">
        <label for="tournament">Tournament</label>
        <select id="tournament" v-model="form.tournament">
          <option v-for="option in TOURNAMENT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>

    <p v-if="form.homeTeam && form.homeTeam === form.awayTeam" class="error-text">
      Home team and away team must be different.
    </p>

    <button type="submit" :disabled="!isValid || submitting">
      {{ submitting ? submittingLabel : submitLabel }}
    </button>
  </form>
</template>

<style scoped>
.host-label-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.link-button {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-primary);
  cursor: pointer;
}

.link-button:hover {
  text-decoration: underline;
}
</style>
