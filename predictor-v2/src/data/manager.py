"""Data manager for loading/saving predictions, history, and configs."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from ..core.data_types import (
    EngineParameters, HistoricalMatch, MatchPrediction, MapPrediction,
)


class DataManager:
    """Manages all data persistence (JSON files)."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__))
        self.base_dir = Path(base_dir)
        self.configs_dir = self.base_dir / "configs"
        self.historical_dir = self.base_dir / "historical"
        self.history_dir = self.base_dir / "history"
        self.results_dir = self.base_dir.parent / "results"

        # Ensure directories exist
        for d in [self.configs_dir, self.historical_dir, self.history_dir, self.results_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # --- Parameters ---

    def load_parameters(self) -> EngineParameters:
        """Load engine parameters from JSON config."""
        path = self.configs_dir / "parameters.json"
        if not path.exists():
            params = EngineParameters()
            self.save_parameters(params)
            return params
        with open(path, "r") as f:
            data = json.load(f)
        return EngineParameters.from_dict(data)

    def save_parameters(self, params: EngineParameters) -> None:
        """Save engine parameters to JSON config."""
        path = self.configs_dir / "parameters.json"
        with open(path, "w") as f:
            json.dump(params.to_dict(), f, indent=2)

    # --- Historical matches ---

    def load_historical_matches(self) -> List[HistoricalMatch]:
        """Load historical matches for optimizer training."""
        path = self.historical_dir / "matches.json"
        if not path.exists():
            return []
        with open(path, "r") as f:
            data = json.load(f)
        matches = []
        for d in data:
            matches.append(HistoricalMatch(**d))
        return matches

    def save_historical_matches(self, matches: List[HistoricalMatch]) -> None:
        """Save historical matches."""
        path = self.historical_dir / "matches.json"
        data = []
        for m in matches:
            data.append({
                "team1": m.team1,
                "team2": m.team2,
                "team1_ranking": m.team1_ranking,
                "team2_ranking": m.team2_ranking,
                "map_name": m.map_name,
                "team1_map_winrate": m.team1_map_winrate,
                "team2_map_winrate": m.team2_map_winrate,
                "team1_form": m.team1_form,
                "team2_form": m.team2_form,
                "team1_odds": m.team1_odds,
                "team2_odds": m.team2_odds,
                "picked_by": m.picked_by,
                "actual_winner": m.actual_winner,
                "actual_score_t1": m.actual_score_t1,
                "actual_score_t2": m.actual_score_t2,
                "team1_pistol_wr": m.team1_pistol_wr,
                "team2_pistol_wr": m.team2_pistol_wr,
            })
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def add_historical_match(self, match: HistoricalMatch) -> None:
        """Add a single historical match."""
        matches = self.load_historical_matches()
        matches.append(match)
        self.save_historical_matches(matches)

    # --- Prediction history ---

    def load_prediction_history(self) -> List[Dict]:
        """Load prediction history."""
        path = self.history_dir / "predictions.json"
        if not path.exists():
            return []
        with open(path, "r") as f:
            return json.load(f)

    def save_prediction(self, prediction: MatchPrediction) -> None:
        """Save a prediction to history."""
        history = self.load_prediction_history()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "team1": prediction.team1,
            "team2": prediction.team2,
            "match_format": prediction.match_format,
            "winner": prediction.winner,
            "winner_probability": prediction.winner_probability,
            "predicted_score": prediction.predicted_score,
            "total_rounds": prediction.total_rounds_prediction,
            "over_under_line": prediction.over_under_line,
            "over_probability": prediction.over_probability,
            "confidence": prediction.confidence,
            "maps": [
                {
                    "map_name": mp.map_name,
                    "team1_win_prob": mp.team1_win_prob,
                    "predicted_score": f"{mp.predicted_score_t1}:{mp.predicted_score_t2}",
                    "total_rounds": mp.total_rounds,
                }
                for mp in prediction.map_predictions
            ],
            "model_breakdown": prediction.model_breakdown,
            "actual_result": None,  # To be filled later
        }
        history.append(entry)

        path = self.history_dir / "predictions.json"
        with open(path, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def update_prediction_result(self, index: int, actual_winner: str,
                                  actual_score: str) -> None:
        """Update a prediction with the actual result."""
        history = self.load_prediction_history()
        if 0 <= index < len(history):
            history[index]["actual_result"] = {
                "winner": actual_winner,
                "score": actual_score,
                "correct": history[index]["winner"] == actual_winner,
            }
            path = self.history_dir / "predictions.json"
            with open(path, "w") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

    # --- Statistics ---

    def get_accuracy_stats(self) -> Dict:
        """Calculate accuracy statistics from prediction history."""
        history = self.load_prediction_history()
        total = 0
        correct = 0
        by_confidence = {"High": [0, 0], "Medium": [0, 0], "Low": [0, 0]}

        for entry in history:
            if entry.get("actual_result"):
                total += 1
                is_correct = entry["actual_result"]["correct"]
                if is_correct:
                    correct += 1
                conf = entry.get("confidence", "Medium")
                if conf in by_confidence:
                    by_confidence[conf][1] += 1
                    if is_correct:
                        by_confidence[conf][0] += 1

        return {
            "total_predictions": len(history),
            "verified_predictions": total,
            "correct_predictions": correct,
            "accuracy": correct / total if total > 0 else 0.0,
            "by_confidence": {
                k: v[0] / v[1] if v[1] > 0 else 0.0
                for k, v in by_confidence.items()
            },
        }

    # --- Export ---

    def export_to_markdown(self, prediction: MatchPrediction) -> str:
        """Export prediction to markdown format."""
        lines = [
            f"# {prediction.team1} vs {prediction.team2}",
            f"**Format:** {prediction.match_format}",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Prediction",
            f"- **Winner:** {prediction.winner} ({prediction.winner_probability:.1%})",
            f"- **Score:** {prediction.predicted_score}",
            f"- **Confidence:** {prediction.confidence}",
            "",
            "## Maps",
        ]

        for mp in prediction.map_predictions:
            winner = prediction.team1 if mp.team1_win_prob > 0.5 else prediction.team2
            lines.append(
                f"- **{mp.map_name}:** {winner} "
                f"({max(mp.team1_win_prob, mp.team2_win_prob):.1%}) "
                f"[{mp.predicted_score_t1}:{mp.predicted_score_t2}]"
            )

        lines.extend([
            "",
            "## Totals",
            f"- Avg rounds per map: {prediction.total_rounds_prediction:.1f}",
            f"- Over {prediction.over_under_line}: {prediction.over_probability:.1%}",
        ])

        if prediction.model_breakdown:
            lines.extend(["", "## Model Breakdown"])
            for model, prob in prediction.model_breakdown.items():
                lines.append(f"- {model}: {prob:.1%}")

        return "\n".join(lines)
