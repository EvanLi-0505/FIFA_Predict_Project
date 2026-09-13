import { defineStore } from 'pinia'
import { api } from '../services/api'

export const MAX_COMPARE_TEAMS = 5

export const useTeamStatsStore = defineStore('teamStats', {
  state: () => ({
    allTeams: [],
    allTeamsLoaded: false,
    allTeamsError: null,

    selectedTeam: '',
    matches: [],
    stats: null,
    detailLoading: false,
    detailError: null,

    compareSelection: [],
    compareResults: [],
    comparing: false,
    compareError: null,
  }),

  actions: {
    async loadAllTeams() {
      this.allTeamsError = null
      try {
        this.allTeams = await api.getAllTeams()
        this.allTeamsLoaded = true
      } catch (error) {
        this.allTeamsError = error.message
      }
    },

    async loadTeamDetail(teamName) {
      this.selectedTeam = teamName
      this.detailLoading = true
      this.detailError = null
      try {
        const [matches, stats] = await Promise.all([
          api.getTeamMatches(teamName, 200),
          api.getTeamStats(teamName),
        ])
        this.matches = matches
        this.stats = stats
      } catch (error) {
        this.detailError = error.message
        this.matches = []
        this.stats = null
      } finally {
        this.detailLoading = false
      }
    },

    toggleCompareSelection(teamName) {
      const index = this.compareSelection.indexOf(teamName)
      if (index >= 0) {
        this.compareSelection.splice(index, 1)
        return
      }
      if (this.compareSelection.length >= MAX_COMPARE_TEAMS) return
      this.compareSelection.push(teamName)
    },

    clearCompareSelection() {
      this.compareSelection = []
      this.compareResults = []
    },

    async runComparison() {
      if (this.compareSelection.length === 0) return
      this.comparing = true
      this.compareError = null
      try {
        this.compareResults = await api.compareTeams(this.compareSelection)
      } catch (error) {
        this.compareError = error.message
      } finally {
        this.comparing = false
      }
    },
  },
})
