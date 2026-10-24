<script setup>
import { computed, ref } from 'vue'
import ProbabilityChart from './ProbabilityChart.vue'
import UpsetRiskBadge from './UpsetRiskBadge.vue'
import { downloadPredictionReportMarkdown, downloadPredictionReportPdf } from '../utils/report'
import { fetchTeamComparisonData } from '../utils/matchComparison'
import { fetchUpsetHistory, upsetSummary } from '../utils/upset'

const props = defineProps({
  result: { type: Object, required: true },
})

const upset = computed(() => upsetSummary(props.result))

const OUTCOME_BADGE_CLASS = {
  'Home Win': 'badge-active',
  Draw: 'badge-inactive',
  'Home Loss': 'badge-invalid',
}

const downloadingFormat = ref(null) // null | 'md' | 'pdf'

async function buildReportPayload() {
  // The comparison charts are a nice-to-have addition — if fetching them
  // fails, still produce a report with just the probability breakdown.
  let comparison
  try {
    comparison = await fetchTeamComparisonData(props.result.home_team, props.result.away_team)
  } catch {
    comparison = undefined
  }
  let upsetHistory
  try {
    upsetHistory = await fetchUpsetHistory(props.result.home_team, props.result.away_team)
  } catch {
    upsetHistory = undefined
  }

  return {
    homeTeam: props.result.home_team,
    awayTeam: props.result.away_team,
    hostCountry: props.result.host_country,
    tournament: props.result.tournament,
    tournamentCategory: props.result.tournament_category,
    neutral: props.result.neutral,
    probabilities: props.result.probabilities,
    predictedOutcome: props.result.predicted_outcome,
    confidence: props.result.confidence,
    modelVersion: props.result.model_version,
    datasetVersion: props.result.dataset_version,
    comparison,
    upset: { ...upset.value, history: upsetHistory },
  }
}

async function downloadMarkdown() {
  downloadingFormat.value = 'md'
  try {
    downloadPredictionReportMarkdown(await buildReportPayload())
  } finally {
    downloadingFormat.value = null
  }
}

async function downloadPdf() {
  downloadingFormat.value = 'pdf'
  try {
    downloadPredictionReportPdf(await buildReportPayload())
  } finally {
    downloadingFormat.value = null
  }
}
</script>

<template>
  <div class="result">
    <div class="result-header">
      <h3>{{ result.home_team }} vs {{ result.away_team }}</h3>
      <span class="badge" :class="OUTCOME_BADGE_CLASS[result.predicted_outcome]">
        {{ result.predicted_outcome }}
      </span>
    </div>
    <p class="muted">
      Host: {{ result.host_country }} · Tournament: {{ result.tournament }}
      ({{ result.tournament_category }}) · {{ result.neutral ? 'Neutral venue' : 'Home venue' }}
    </p>

    <div v-if="upset.level === 'high'" class="high-risk-banner">
      <span>⚠</span>
      <div>
        HIGH-RISK PREDICTION / 高风险预测
        <small>
          {{ (upset.probability * 100).toFixed(1) }}% chance that {{ upset.underdogTeam }} beats
          {{ upset.favoriteTeam }} — see the Upset Risk page for each team's upset history.
        </small>
      </div>
    </div>
    <p class="upset-line">
      <UpsetRiskBadge :probability="upset.probability" :level="upset.level" />
      <span class="muted">chance {{ upset.underdogTeam }} (underdog) wins outright</span>
    </p>

    <ProbabilityChart
      :probabilities="result.probabilities"
      :predicted-outcome="result.predicted_outcome"
    />

    <div class="result-footer">
      <p class="muted">
        Model: <code>{{ result.model_version }}</code> · Dataset: <code>{{ result.dataset_version }}</code>
        · Confidence: {{ (result.confidence * 100).toFixed(1) }}%
      </p>
      <div class="download-actions">
        <button class="secondary" :disabled="!!downloadingFormat" @click="downloadMarkdown">
          {{ downloadingFormat === 'md' ? 'Preparing…' : 'Download Markdown' }}
        </button>
        <button class="secondary" :disabled="!!downloadingFormat" @click="downloadPdf">
          {{ downloadingFormat === 'pdf' ? 'Preparing…' : 'Download PDF' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.result-header h3 {
  margin: 0;
}

.upset-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 12px;
}

.result-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.download-actions {
  display: flex;
  gap: 10px;
}

code {
  background: var(--color-surface-raised);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}
</style>
