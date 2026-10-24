import axios from 'axios'

// In dev, requests to /api/* go through the Vite proxy configured in
// vite.config.js, so the default base URL can stay empty (relative paths).
// Empty stays relative ('/api/...'), which resolves correctly for both
// the Web build (served from the same origin as the API, or behind a
// reverse proxy that forwards /api) and the Desktop build (pywebview
// loads this from the SAME FastAPI process — see desktop_app/main.py —
// so it's always same-origin too). Only set VITE_API_BASE_URL for a Web
// deployment where the frontend and backend are on different hosts.
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

const client = axios.create({ baseURL })

function unwrapError(error) {
  const detail = error.response?.data?.detail
  const message = typeof detail === 'string' ? detail : error.message
  return new Error(message)
}

export const api = {
  async getHealth() {
    const { data } = await client.get('/api/health')
    return data
  },

  async getTeams() {
    try {
      const { data } = await client.get('/api/teams')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async predict({ homeTeam, awayTeam, hostCountry, tournament }) {
    try {
      const { data } = await client.post('/api/predictions', {
        home_team: homeTeam,
        away_team: awayTeam,
        host_country: hostCountry,
        tournament,
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  // Same request shape as predict(), but not recorded in prediction history.
  async getUpsetRisk({ homeTeam, awayTeam, hostCountry, tournament }) {
    try {
      const { data } = await client.post('/api/upsets/risk', {
        home_team: homeTeam,
        away_team: awayTeam,
        host_country: hostCountry,
        tournament,
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getTeamUpsets(teamName, limit = 20) {
    try {
      const { data } = await client.get(`/api/upsets/teams/${encodeURIComponent(teamName)}`, {
        params: { limit },
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getHistory(limit = 50) {
    try {
      const { data } = await client.get('/api/history', { params: { limit } })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getDatasets() {
    try {
      const { data } = await client.get('/api/datasets')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async uploadDataset(file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await client.post('/api/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async activateDataset(datasetId) {
    try {
      const { data } = await client.post(`/api/datasets/${datasetId}/activate`)
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async deleteDataset(datasetId) {
    try {
      await client.delete(`/api/datasets/${datasetId}`)
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getModels() {
    try {
      const { data } = await client.get('/api/models')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async trainModel({ datasetId, modelType, featureVersion }) {
    try {
      const { data } = await client.post('/api/models/train', {
        dataset_id: datasetId,
        model_type: modelType,
        feature_version: featureVersion,
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async activateModel(modelVersionId) {
    try {
      const { data } = await client.post(`/api/models/${modelVersionId}/activate`)
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async deleteModel(modelVersionId) {
    try {
      await client.delete(`/api/models/${modelVersionId}`)
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async deleteHistoryItem(predictionId) {
    try {
      await client.delete(`/api/history/${predictionId}`)
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async clearHistory() {
    try {
      const { data } = await client.delete('/api/history')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getHistoryStats() {
    try {
      const { data } = await client.get('/api/history/stats')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getAllTeams() {
    try {
      const { data } = await client.get('/api/team-stats/teams')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getTeamMatches(teamName, limit) {
    try {
      const { data } = await client.get(
        `/api/team-stats/${encodeURIComponent(teamName)}/matches`,
        { params: limit ? { limit } : {} },
      )
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async getTeamStats(teamName) {
    try {
      const { data } = await client.get(
        `/api/team-stats/${encodeURIComponent(teamName)}/stats`,
      )
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async compareTeams(teamNames) {
    try {
      const { data } = await client.post('/api/team-stats/compare', {
        team_names: teamNames,
      })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  // Desktop-only (see desktop_app/main.py's register_system_routes) — 404s
  // on the Web edition. getSystemInfo() is used as the "am I running as
  // the Desktop app?" probe; callers should treat its rejection as "hide
  // desktop-only UI," not as an error to surface to the user.
  async getSystemInfo() {
    const { data } = await client.get('/api/system/info')
    return data
  },

  async getSystemLog(lines = 500) {
    // Plain text response (see desktop_app/main.py) — must override
    // axios's default JSON responseType or it mishandles the body.
    const { data } = await client.get('/api/system/log', {
      params: { lines },
      responseType: 'text',
    })
    return data
  },

  async clearSystemLog() {
    try {
      const { data } = await client.delete('/api/system/log')
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },

  async setLogFolder(folder) {
    try {
      const { data } = await client.post('/api/system/log/folder', { folder })
      return data
    } catch (error) {
      throw unwrapError(error)
    }
  },
}
