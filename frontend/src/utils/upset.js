// Upset ("black swan") risk = probability the underdog wins outright. The
// backend computes it (core/analytics/upset.py) and returns it on every
// prediction and history record as upset_probability / upset_risk_level /
// upset_favorite_outcome; this file only maps that onto teams and labels.

import { api } from '../services/api'

export const RISK_LEVEL_LABELS = {
  low: 'Low risk',
  medium: 'Medium risk',
  high: 'High risk',
}

export const RISK_LEVEL_LABELS_ZH = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
}

export function upsetSummary(item) {
  const homeIsFavorite = item.upset_favorite_outcome === 'Home Win'
  return {
    probability: item.upset_probability,
    level: item.upset_risk_level,
    favoriteTeam: homeIsFavorite ? item.home_team : item.away_team,
    underdogTeam: homeIsFavorite ? item.away_team : item.home_team,
  }
}

export async function fetchUpsetHistory(homeTeam, awayTeam, limit = 5) {
  const [home, away] = await Promise.all([
    api.getTeamUpsets(homeTeam, limit),
    api.getTeamUpsets(awayTeam, limit),
  ])
  return { home, away }
}
