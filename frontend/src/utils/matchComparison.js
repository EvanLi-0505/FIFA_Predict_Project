// Shared by the Dashboard page and the downloadable prediction report: both
// need the same "home team vs away team" comparison data (lifetime
// win/draw/loss rates + recent per-match goal-difference trend).

import { api } from '../services/api'
import { computeGoalDiffSeries, FORM_CHART_MATCH_COUNT } from './teamForm'

export async function fetchTeamComparisonData(homeTeam, awayTeam) {
  const [homeStats, awayStats, homeMatches, awayMatches] = await Promise.all([
    api.getTeamStats(homeTeam),
    api.getTeamStats(awayTeam),
    api.getTeamMatches(homeTeam, 200),
    api.getTeamMatches(awayTeam, 200),
  ])

  return {
    home: {
      stats: homeStats,
      series: computeGoalDiffSeries(homeMatches, FORM_CHART_MATCH_COUNT),
    },
    away: {
      stats: awayStats,
      series: computeGoalDiffSeries(awayMatches, FORM_CHART_MATCH_COUNT),
    },
  }
}
