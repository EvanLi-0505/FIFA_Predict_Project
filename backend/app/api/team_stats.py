from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.team import TeamCompareRequest, TeamMatchResponse, TeamStatsResponse
from backend.app.services import team_stats_service
from backend.app.services.team_stats_service import NoActiveDatasetError, TooManyTeamsError
from core.analytics.team_stats import TeamStats

# Separate prefix from /api/teams (which backs prediction-form dropdowns and
# reflects the ACTIVE MODEL's training dataset) to avoid any confusion with
# this router, which reflects the ACTIVE DATASET directly — see
# team_stats_service's module docstring.
router = APIRouter(prefix="/api/team-stats", tags=["team-stats"])


def _to_stats_response(stats: TeamStats) -> TeamStatsResponse:
    return TeamStatsResponse(
        team_name=stats.team_name,
        matches_played=stats.matches_played,
        wins=stats.wins,
        draws=stats.draws,
        losses=stats.losses,
        win_rate=stats.win_rate,
        draw_rate=stats.draw_rate,
        loss_rate=stats.loss_rate,
        goals_for=stats.goals_for,
        goals_against=stats.goals_against,
        goals_for_avg=stats.goals_for_avg,
        goals_against_avg=stats.goals_against_avg,
        goal_diff_avg=stats.goal_diff_avg,
        points_per_game=stats.points_per_game,
        recent_form=stats.recent_form,
        recent_points_per_game=stats.recent_points_per_game,
        rating=stats.rating,
        small_sample=stats.small_sample,
    )


@router.get("/teams", response_model=list[str])
def list_teams(session: Session = Depends(get_session)) -> list[str]:
    try:
        return team_stats_service.list_teams(session)
    except NoActiveDatasetError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/{team_name}/matches", response_model=list[TeamMatchResponse])
def get_team_matches(
    team_name: str,
    limit: int | None = Query(default=None, ge=1, le=2000),
    session: Session = Depends(get_session),
) -> list[TeamMatchResponse]:
    try:
        matches = team_stats_service.get_team_matches(session, team_name, limit=limit)
    except NoActiveDatasetError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return [
        TeamMatchResponse(
            date=m.date,
            opponent=m.opponent,
            is_home=m.is_home,
            tournament=m.tournament,
            neutral=m.neutral,
            team_score=m.team_score,
            opponent_score=m.opponent_score,
            outcome=m.outcome,
        )
        for m in matches
    ]


@router.get("/{team_name}/stats", response_model=TeamStatsResponse)
def get_team_stats(team_name: str, session: Session = Depends(get_session)) -> TeamStatsResponse:
    try:
        stats = team_stats_service.get_team_stats(session, team_name)
    except NoActiveDatasetError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    if stats is None:
        raise HTTPException(status_code=404, detail=f"No matches found for team {team_name!r}.")

    return _to_stats_response(stats)


@router.post("/compare", response_model=list[TeamStatsResponse])
def compare_teams(
    request: TeamCompareRequest, session: Session = Depends(get_session)
) -> list[TeamStatsResponse]:
    try:
        results = team_stats_service.compare_teams(session, request.team_names)
    except NoActiveDatasetError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except TooManyTeamsError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return [_to_stats_response(stats) for stats in results]
