import { defineStore } from 'pinia'
import { api } from '../services/api'

// Raw tournament values sent to the backend. `categorize_tournament()`
// (core/feature_engineering/tournament.py) maps exactly these three special
// cases; any other string — including the literal "Other Competitive" used
// here — falls through to the "Other Competitive" category, so this list
// covers all four categories the model was trained on.
export const TOURNAMENT_OPTIONS = [
  { value: 'Friendly', label: 'Friendly' },
  { value: 'FIFA World Cup', label: 'FIFA World Cup' },
  { value: 'FIFA World Cup qualification', label: 'FIFA World Cup Qualification' },
  { value: 'Other Competitive', label: 'Other Competitive' },
]

export const usePredictionStore = defineStore('prediction', {
  state: () => ({
    teams: [],
    teamsLoaded: false,
    teamsError: null,

    result: null,
    predicting: false,
    predictError: null,

    history: [],
    historyLoading: false,
    historyError: null,
    historyActionError: null,

    stats: null,
    statsLoading: false,
    statsError: null,
  }),

  actions: {
    async loadTeams() {
      this.teamsError = null
      try {
        this.teams = await api.getTeams()
        this.teamsLoaded = true
      } catch (error) {
        this.teamsError = error.message
      }
    },

    async predict(payload) {
      this.predicting = true
      this.predictError = null
      try {
        this.result = await api.predict(payload)
        return this.result
      } catch (error) {
        this.predictError = error.message
        throw error
      } finally {
        this.predicting = false
      }
    },

    async loadHistory(limit = 50) {
      this.historyLoading = true
      this.historyError = null
      try {
        this.history = await api.getHistory(limit)
      } catch (error) {
        this.historyError = error.message
      } finally {
        this.historyLoading = false
      }
    },

    async deleteHistoryItem(predictionId) {
      this.historyActionError = null
      try {
        await api.deleteHistoryItem(predictionId)
        this.history = this.history.filter((item) => item.id !== predictionId)
      } catch (error) {
        this.historyActionError = error.message
        throw error
      }
    },

    async clearHistory() {
      this.historyActionError = null
      try {
        await api.clearHistory()
        this.history = []
      } catch (error) {
        this.historyActionError = error.message
        throw error
      }
    },

    async loadStats() {
      this.statsLoading = true
      this.statsError = null
      try {
        this.stats = await api.getHistoryStats()
      } catch (error) {
        this.statsError = error.message
      } finally {
        this.statsLoading = false
      }
    },
  },
})
