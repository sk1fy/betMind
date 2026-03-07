"""Advanced CS2 match prediction engine with parameterized weights."""

import random
import math
from typing import Dict, List, Optional, Tuple

from .data_types import (
    TeamData, MapStats, EngineParameters,
    MapPrediction, MatchPrediction, MatchFormat,
)


class PredictionEngine:
    """Core prediction engine with tunable parameters."""

    def __init__(self, params: Optional[EngineParameters] = None):
        self.params = params or EngineParameters()

    def predict_map(
        self,
        team1: TeamData,
        team2: TeamData,
        map_name: str,
        picked_by: Optional[str] = None,
        num_simulations: int = 1000,
    ) -> MapPrediction:
        """Predict outcome for a single map."""
        p = self.params

        # Base probability from rankings
        rank_diff = team2.ranking - team1.ranking  # positive = team1 is better
        rank_factor = rank_diff * p.rank_weight
        base_prob = 0.5 + rank_factor

        # Map win rate factor
        t1_map = team1.get_map_stats(map_name)
        t2_map = team2.get_map_stats(map_name)
        t1_wr = self._smooth_winrate(t1_map.win_rate, t1_map.total_games, p.smooth_base)
        t2_wr = self._smooth_winrate(t2_map.win_rate, t2_map.total_games, p.smooth_base)
        map_factor = (t1_wr - t2_wr) * p.map_weight

        # Pick bonus
        pick_factor = 0.0
        if picked_by == team1.name:
            pick_factor = p.pick_bonus
        elif picked_by == team2.name:
            pick_factor = -p.pick_bonus

        # Form factor
        t1_form = team1.form_score if team1.form_score else team1.form_from_results
        t2_form = team2.form_score if team2.form_score else team2.form_from_results
        form_factor = (t1_form - t2_form) * p.form_multiplier * 10

        # Odds factor (implied probability)
        if team1.odds > 0 and team2.odds > 0:
            t1_implied = 1.0 / team1.odds
            t2_implied = 1.0 / team2.odds
            total_implied = t1_implied + t2_implied
            t1_fair = t1_implied / total_implied if total_implied > 0 else 0.5
            odds_factor = (t1_fair - 0.5) * p.odds_weight * 2
        else:
            odds_factor = 0.0

        # Pistol round advantage
        t1_pistol = t1_map.pistol_win_rate
        t2_pistol = t2_map.pistol_win_rate
        pistol_factor = (t1_pistol - t2_pistol) * p.pistol_weight * 0.05

        # Combine all factors
        team1_win_prob = base_prob + map_factor + pick_factor + form_factor + odds_factor + pistol_factor

        # Clamp probability
        team1_win_prob = max(0.05, min(0.95, team1_win_prob))
        team2_win_prob = 1.0 - team1_win_prob

        # Simulate rounds to get predicted score
        t1_rounds, t2_rounds = self._simulate_rounds(
            team1_win_prob, team1, team2, map_name, num_simulations
        )

        # Confidence level
        prob_diff = abs(team1_win_prob - 0.5)
        if prob_diff > 0.15:
            confidence = 0.85
        elif prob_diff > 0.08:
            confidence = 0.65
        else:
            confidence = 0.45

        return MapPrediction(
            map_name=map_name,
            team1_win_prob=team1_win_prob,
            team2_win_prob=team2_win_prob,
            predicted_score_t1=t1_rounds,
            predicted_score_t2=t2_rounds,
            total_rounds=t1_rounds + t2_rounds,
            confidence=confidence,
            picked_by=picked_by,
        )

    def predict_match(
        self,
        team1: TeamData,
        team2: TeamData,
        maps: List[Dict[str, str]],
        match_format: str = "BO3",
        num_simulations: int = 1000,
    ) -> MatchPrediction:
        """Predict full match outcome.

        Args:
            maps: List of dicts with keys 'name' and optionally 'picked_by'
        """
        map_predictions = []
        for m in maps:
            mp = self.predict_map(
                team1, team2,
                map_name=m["name"],
                picked_by=m.get("picked_by"),
                num_simulations=num_simulations,
            )
            map_predictions.append(mp)

        # Count map wins
        t1_map_wins = sum(1 for mp in map_predictions if mp.team1_win_prob > 0.5)
        t2_map_wins = len(map_predictions) - t1_map_wins

        # Match winner
        if match_format == "BO1":
            winner = team1.name if map_predictions[0].team1_win_prob > 0.5 else team2.name
            winner_prob = max(map_predictions[0].team1_win_prob, map_predictions[0].team2_win_prob)
            score = "1:0" if winner == team1.name else "0:1"
        else:
            # BO3 / BO5 simulation
            winner, winner_prob, score = self._simulate_series(
                team1, team2, map_predictions, match_format, num_simulations
            )

        # Total rounds across maps
        total_rounds = sum(mp.total_rounds for mp in map_predictions)
        avg_rounds_per_map = total_rounds / len(map_predictions) if map_predictions else 26

        # Over/Under
        over_line = 26.5
        over_prob = self._calc_over_prob(map_predictions, over_line)

        # Confidence
        if winner_prob > 0.65:
            confidence = "High"
        elif winner_prob > 0.55:
            confidence = "Medium"
        else:
            confidence = "Low"

        return MatchPrediction(
            team1=team1.name,
            team2=team2.name,
            match_format=match_format,
            winner=winner,
            winner_probability=winner_prob,
            map_predictions=map_predictions,
            predicted_score=score,
            total_rounds_prediction=avg_rounds_per_map,
            over_under_line=over_line,
            over_probability=over_prob,
            confidence=confidence,
        )

    def _smooth_winrate(self, wr: float, games: int, base: float) -> float:
        """Smooth win rate towards 0.5 for low sample sizes."""
        weight = games / (games + base)
        return wr * weight + 0.5 * (1 - weight)

    def _simulate_rounds(
        self,
        team1_map_prob: float,
        team1: TeamData,
        team2: TeamData,
        map_name: str,
        n: int,
    ) -> Tuple[int, int]:
        """Simulate map rounds and return average score."""
        p = self.params
        total_t1 = 0
        total_t2 = 0

        # Round win probability (derived from map win probability)
        # A team with 60% map win prob wins ~52-53% of rounds
        round_prob = 0.5 + (team1_map_prob - 0.5) * p.rounds_bias_multiplier * 20

        for _ in range(n):
            t1_rounds = 0
            t2_rounds = 0

            # Simulate up to 30 rounds (regulation)
            for rnd in range(1, 31):
                # Pistol rounds (1 and 16)
                if rnd in (1, 16):
                    t1_map = team1.get_map_stats(map_name)
                    t2_map = team2.get_map_stats(map_name)
                    pistol_prob = round_prob + (t1_map.pistol_win_rate - t2_map.pistol_win_rate) * 0.1
                else:
                    pistol_prob = round_prob

                # Economy factor (simplified)
                if rnd > 1:
                    pistol_prob += random.gauss(0, p.day_form_variance * 0.5)

                pistol_prob = max(0.2, min(0.8, pistol_prob))

                if random.random() < pistol_prob:
                    t1_rounds += 1
                else:
                    t2_rounds += 1

                # Check win condition (first to 13, MR12)
                if t1_rounds >= 13 and t1_rounds - t2_rounds >= 1:
                    break
                if t2_rounds >= 13 and t2_rounds - t1_rounds >= 1:
                    break

            # Overtime (simplified)
            while t1_rounds == t2_rounds or (t1_rounds >= 13 and t2_rounds >= 13 and abs(t1_rounds - t2_rounds) < 2):
                if t1_rounds >= 13 and t2_rounds >= 13:
                    if random.random() < round_prob:
                        t1_rounds += 1
                    else:
                        t2_rounds += 1
                    if abs(t1_rounds - t2_rounds) >= 2 and (t1_rounds + t2_rounds - 24) % 6 == 0:
                        break
                else:
                    break

            total_t1 += t1_rounds
            total_t2 += t2_rounds

        avg_t1 = round(total_t1 / n)
        avg_t2 = round(total_t2 / n)

        # Ensure valid score
        if avg_t1 == avg_t2:
            if team1_map_prob > 0.5:
                avg_t1 = max(avg_t1, 13)
            else:
                avg_t2 = max(avg_t2, 13)

        return avg_t1, avg_t2

    def _simulate_series(
        self,
        team1: TeamData,
        team2: TeamData,
        map_predictions: List[MapPrediction],
        match_format: str,
        n: int,
    ) -> Tuple[str, float, str]:
        """Simulate BO3/BO5 series."""
        maps_to_win = 2 if match_format == "BO3" else 3
        t1_series_wins = 0

        for _ in range(n):
            t1_maps = 0
            t2_maps = 0
            for mp in map_predictions:
                if random.random() < mp.team1_win_prob:
                    t1_maps += 1
                else:
                    t2_maps += 1
                if t1_maps >= maps_to_win or t2_maps >= maps_to_win:
                    break
            if t1_maps >= maps_to_win:
                t1_series_wins += 1

        t1_prob = t1_series_wins / n
        if t1_prob > 0.5:
            winner = team1.name
            winner_prob = t1_prob
            # Most likely score
            if match_format == "BO3":
                score = "2:0" if t1_prob > 0.65 else "2:1"
            else:
                score = "3:0" if t1_prob > 0.75 else ("3:1" if t1_prob > 0.6 else "3:2")
        else:
            winner = team2.name
            winner_prob = 1 - t1_prob
            if match_format == "BO3":
                score = "0:2" if winner_prob > 0.65 else "1:2"
            else:
                score = "0:3" if winner_prob > 0.75 else ("1:3" if winner_prob > 0.6 else "2:3")

        return winner, winner_prob, score

    def _calc_over_prob(self, map_predictions: List[MapPrediction], line: float) -> float:
        """Calculate probability of total rounds going over the line."""
        # Average total from predictions
        avg_total = sum(mp.total_rounds for mp in map_predictions) / len(map_predictions)
        # Simple logistic approximation
        diff = avg_total - line
        return 1.0 / (1.0 + math.exp(-diff * 0.5))
