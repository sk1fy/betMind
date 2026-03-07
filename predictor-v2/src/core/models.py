"""Ensemble of prediction models for CS2 matches."""

import math
from typing import Dict, Optional

from .data_types import TeamData, EngineParameters, MapPrediction, MatchPrediction
from .engine import PredictionEngine


class SimulationModel:
    """Model 1: Monte-Carlo simulation engine."""

    WEIGHT = 0.30

    def __init__(self, params: Optional[EngineParameters] = None):
        self.engine = PredictionEngine(params)

    def predict_map(self, team1: TeamData, team2: TeamData, map_name: str,
                    picked_by: Optional[str] = None) -> float:
        result = self.engine.predict_map(team1, team2, map_name, picked_by)
        return result.team1_win_prob


class BookmakerModel:
    """Model 2: Reverse implied probabilities from odds."""

    WEIGHT = 0.25

    def predict_map(self, team1: TeamData, team2: TeamData, map_name: str,
                    picked_by: Optional[str] = None) -> float:
        if team1.odds <= 0 or team2.odds <= 0:
            return 0.5

        t1_implied = 1.0 / team1.odds
        t2_implied = 1.0 / team2.odds
        total = t1_implied + t2_implied
        t1_fair = t1_implied / total if total > 0 else 0.5

        # Adjust for rank difference
        rank_diff = team2.ranking - team1.ranking
        rank_adj = rank_diff * 0.002
        t1_fair = max(0.1, min(0.9, t1_fair + rank_adj))

        return t1_fair


class ExpertModel:
    """Model 3: Heuristic rules based on form, h2h, map pool."""

    WEIGHT = 0.20

    def predict_map(self, team1: TeamData, team2: TeamData, map_name: str,
                    picked_by: Optional[str] = None) -> float:
        score = 0.5

        # Form advantage
        t1_form = team1.form_score if team1.form_score else team1.form_from_results
        t2_form = team2.form_score if team2.form_score else team2.form_from_results
        form_diff = t1_form - t2_form
        score += form_diff * 0.15

        # Map pool strength
        t1_maps = team1.get_map_stats(map_name)
        t2_maps = team2.get_map_stats(map_name)
        if t1_maps.total_games >= 3 and t2_maps.total_games >= 3:
            wr_diff = t1_maps.win_rate - t2_maps.win_rate
            score += wr_diff * 0.20

        # Ranking tier bonus
        if team1.ranking <= 5 and team2.ranking > 15:
            score += 0.05
        elif team2.ranking <= 5 and team1.ranking > 15:
            score -= 0.05

        # Pick advantage
        if picked_by == team1.name:
            score += 0.03
        elif picked_by == team2.name:
            score -= 0.03

        return max(0.1, min(0.9, score))


class MomentumModel:
    """Model 4: Momentum/Economic model based on trends."""

    WEIGHT = 0.15

    def predict_map(self, team1: TeamData, team2: TeamData, map_name: str,
                    picked_by: Optional[str] = None) -> float:
        score = 0.5

        # Form trend (momentum)
        t1_form = team1.form_score if team1.form_score else team1.form_from_results
        t2_form = team2.form_score if team2.form_score else team2.form_from_results

        # Recent results streak
        t1_streak = self._calc_streak(team1.recent_results)
        t2_streak = self._calc_streak(team2.recent_results)
        streak_diff = (t1_streak - t2_streak) * 0.03
        score += streak_diff

        # Form momentum
        score += (t1_form - t2_form) * 0.1

        # Pistol advantage (strong predictor of map economy)
        t1_map = team1.get_map_stats(map_name)
        t2_map = team2.get_map_stats(map_name)
        pistol_diff = t1_map.pistol_win_rate - t2_map.pistol_win_rate
        score += pistol_diff * 0.08

        # Map pool synergy (how many strong maps a team has)
        t1_strong = sum(1 for ms in team1.map_stats.values() if ms.win_rate > 0.55)
        t2_strong = sum(1 for ms in team2.map_stats.values() if ms.win_rate > 0.55)
        score += (t1_strong - t2_strong) * 0.01

        return max(0.1, min(0.9, score))

    def _calc_streak(self, results: list) -> int:
        """Calculate current win/loss streak. Positive = win, negative = loss."""
        if not results:
            return 0
        streak = 0
        last = results[-1].upper()
        for r in reversed(results):
            if r.upper() == last:
                streak += 1 if last == "W" else -1
            else:
                break
        return streak


class ConsensusModel:
    """Model 5: Average of other models (meta-model)."""

    WEIGHT = 0.10

    def predict_map(self, predictions: list) -> float:
        if not predictions:
            return 0.5
        return sum(predictions) / len(predictions)


class EnsemblePredictor:
    """Ensemble predictor combining all models."""

    def __init__(self, params: Optional[EngineParameters] = None):
        self.simulation = SimulationModel(params)
        self.bookmaker = BookmakerModel()
        self.expert = ExpertModel()
        self.momentum = MomentumModel()
        self.consensus = ConsensusModel()
        self.engine = PredictionEngine(params)

    def predict_map(
        self,
        team1: TeamData,
        team2: TeamData,
        map_name: str,
        picked_by: Optional[str] = None,
    ) -> Dict:
        """Get ensemble prediction for a single map."""
        sim_prob = self.simulation.predict_map(team1, team2, map_name, picked_by)
        book_prob = self.bookmaker.predict_map(team1, team2, map_name, picked_by)
        expert_prob = self.expert.predict_map(team1, team2, map_name, picked_by)
        mom_prob = self.momentum.predict_map(team1, team2, map_name, picked_by)

        # Consensus from first 4 models
        consensus_prob = self.consensus.predict_map([sim_prob, book_prob, expert_prob, mom_prob])

        # Weighted ensemble
        final_prob = (
            sim_prob * SimulationModel.WEIGHT
            + book_prob * BookmakerModel.WEIGHT
            + expert_prob * ExpertModel.WEIGHT
            + mom_prob * MomentumModel.WEIGHT
            + consensus_prob * ConsensusModel.WEIGHT
        )

        return {
            "team1_win_prob": final_prob,
            "team2_win_prob": 1.0 - final_prob,
            "breakdown": {
                "Simulation": sim_prob,
                "Bookmaker": book_prob,
                "Expert": expert_prob,
                "Momentum": mom_prob,
                "Consensus": consensus_prob,
            },
        }

    def predict_match(
        self,
        team1: TeamData,
        team2: TeamData,
        maps: list,
        match_format: str = "BO3",
    ) -> "MatchPrediction":
        """Get ensemble prediction for a full match."""
        map_results = []
        model_breakdown = {}

        for m in maps:
            result = self.predict_map(
                team1, team2,
                map_name=m["name"],
                picked_by=m.get("picked_by"),
            )
            map_results.append({
                "map_name": m["name"],
                "team1_win_prob": result["team1_win_prob"],
                "breakdown": result["breakdown"],
            })

            # Accumulate breakdown
            for model_name, prob in result["breakdown"].items():
                if model_name not in model_breakdown:
                    model_breakdown[model_name] = []
                model_breakdown[model_name].append(prob)

        # Average breakdown across maps
        avg_breakdown = {
            k: sum(v) / len(v) for k, v in model_breakdown.items()
        }

        # Get the full simulation-based prediction for detailed stats
        engine_result = self.engine.predict_match(team1, team2, maps, match_format)

        # Override winner probability with ensemble
        avg_t1_prob = sum(r["team1_win_prob"] for r in map_results) / len(map_results)

        if avg_t1_prob > 0.5:
            engine_result.winner = team1.name
            engine_result.winner_probability = avg_t1_prob
        else:
            engine_result.winner = team2.name
            engine_result.winner_probability = 1.0 - avg_t1_prob

        engine_result.model_breakdown = avg_breakdown

        # Recalculate confidence
        if engine_result.winner_probability > 0.65:
            engine_result.confidence = "High"
        elif engine_result.winner_probability > 0.55:
            engine_result.confidence = "Medium"
        else:
            engine_result.confidence = "Low"

        return engine_result
