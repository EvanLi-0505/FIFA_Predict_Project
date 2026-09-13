// Shared helper for the "recent form" line chart (Team Explorer + Dashboard
// + downloadable reports): turns a team's match list (most-recent-first,
// as returned by GET /api/team-stats/{team}/matches) into a chronological
// per-match goal-difference series — "score one goal = +1, concede one
// goal = -1" per the product spec, i.e. simply (goals for - goals against)
// for that single match, plotted oldest-to-newest for the most recent N
// matches.

export const FORM_CHART_MATCH_COUNT = 20

export function computeGoalDiffSeries(matches, limit = FORM_CHART_MATCH_COUNT) {
  const recent = matches.slice(0, limit)
  return recent
    .slice()
    .reverse() // matches arrives most-recent-first; chart reads oldest -> newest
    .map((match) => ({
      date: match.date,
      opponent: match.opponent,
      value: match.team_score - match.opponent_score,
    }))
}
