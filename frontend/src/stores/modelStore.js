import { defineStore } from 'pinia'
import { api } from '../services/api'

export const MODEL_TYPE_OPTIONS = [
  { value: 'logistic_regression', label: 'Logistic Regression (recommended)' },
  { value: 'soft_voting', label: 'Ensemble: Soft Voting (LR + GB + HistGB, slower)' },
  { value: 'gradient_boosting', label: 'Gradient Boosting' },
  { value: 'random_forest', label: 'Random Forest' },
  { value: 'decision_tree', label: 'Decision Tree (original notebook model)' },
  { value: 'knn', label: 'K-Nearest Neighbors' },
  { value: 'naive_bayes', label: 'Naive Bayes' },
  { value: 'adaboost', label: 'AdaBoost' },
]

export const FEATURE_VERSION_OPTIONS = [
  { value: 'feature_v2', label: 'Team form + Elo ratings (recommended)' },
  { value: 'feature_v1', label: 'Team form only (original notebook, 23 features)' },
]

export function featureVersionLabel(value) {
  return value === 'feature_v2' ? 'Form + Elo' : value === 'feature_v1' ? 'Form only' : value
}

export const useModelStore = defineStore('model', {
  state: () => ({
    models: [],
    loading: false,
    error: null,

    training: false,
    trainError: null,

    deleteError: null,
  }),

  getters: {
    activeModel: (state) => state.models.find((m) => m.is_active) ?? null,
  },

  actions: {
    async loadModels() {
      this.loading = true
      this.error = null
      try {
        this.models = await api.getModels()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async trainModel({ datasetId, modelType, featureVersion }) {
      this.training = true
      this.trainError = null
      try {
        const model = await api.trainModel({ datasetId, modelType, featureVersion })
        await this.loadModels()
        return model
      } catch (error) {
        this.trainError = error.message
        throw error
      } finally {
        this.training = false
      }
    },

    async activateModel(modelVersionId) {
      await api.activateModel(modelVersionId)
      await this.loadModels()
    },

    async deleteModel(modelVersionId) {
      this.deleteError = null
      try {
        await api.deleteModel(modelVersionId)
        await this.loadModels()
      } catch (error) {
        this.deleteError = error.message
        throw error
      }
    },
  },
})
