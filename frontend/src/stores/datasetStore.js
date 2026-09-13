import { defineStore } from 'pinia'
import { api } from '../services/api'

export const useDatasetStore = defineStore('dataset', {
  state: () => ({
    datasets: [],
    loading: false,
    error: null,

    uploading: false,
    uploadError: null,
    lastUploadResult: null,
  }),

  getters: {
    builtinDataset: (state) => state.datasets.find((d) => d.is_builtin) ?? null,
    activeDataset: (state) => state.datasets.find((d) => d.is_active) ?? null,
  },

  actions: {
    async loadDatasets() {
      this.loading = true
      this.error = null
      try {
        this.datasets = await api.getDatasets()
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async uploadDataset(file) {
      this.uploading = true
      this.uploadError = null
      try {
        this.lastUploadResult = await api.uploadDataset(file)
        await this.loadDatasets()
        return this.lastUploadResult
      } catch (error) {
        this.uploadError = error.message
        throw error
      } finally {
        this.uploading = false
      }
    },

    async activateDataset(datasetId) {
      await api.activateDataset(datasetId)
      await this.loadDatasets()
    },

    async deleteDataset(datasetId) {
      await api.deleteDataset(datasetId)
      await this.loadDatasets()
    },
  },
})
