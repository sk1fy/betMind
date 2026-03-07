"""Data types for CS2 match prediction system."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class MapName(Enum):
    MIRAGE = "Mirage"
    INFERNO = "Inferno"
    NUKE = "Nuke"
    OVERPASS = "Overpass"
    ANCIENT = "Ancient"
    ANUBIS = "Anubis"
    DUST2 = "Dust2"
    VERTIGO = "Vertigo"
    TRAIN = "Train"


class MatchFormat(Enum):
    BO1 = "BO1"
    BO3 = "BO3"
    BO5 = "BO5"


class BetType(Enum):
    WINNER = "winner"
    TOTAL_OVER = "total_over"
    TOTAL_UNDER = "total_under"
    HANDICAP = "handicap"
    MAP_WINNER = "map_winner"


@dataclass
class MapStats:
    """Team stats on a specific map."""
    map_name: str
    wins: int = 0
    losses: int = 0
    rounds_won: int = 0
    rounds_lost: int = 0
    ct_wins: int = 0
    ct_losses: int = 0
    t_wins: int = 0
    t_losses: int = 0
    pistol_wins: int = 0
    pistol_total: int = 0

    @property
    def total_games(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.5
        return self.wins / self.total_games

    @property
    def round_win_rate(self) -> float:
        total = self.rounds_won + self.rounds_lost
        if total == 0:
            return 0.5
        return self.rounds_won / total

    @property
    def pistol_win_rate(self) -> float:
        if self.pistol_total == 0:
            return 0.5
        return self.pistol_wins / self.pistol_total


@dataclass
class TeamData:
    """All data for a team."""
    name: str
    ranking: int = 50
    form_score: float = 0.5  # 0.0 - 1.0 (recent results)
    map_stats: Dict[str, MapStats] = field(default_factory=dict)
    recent_results: List[str] = field(default_factory=list)  # ["W", "L", "W", ...]
    odds: float = 2.0  # Bookmaker odds

    @property
    def form_from_results(self) -> float:
        """Calculate form from recent results (last 5 games)."""
        if not self.recent_results:
            return 0.5
        last5 = self.recent_results[-5:]
        return sum(1 for r in last5 if r.upper() == "W") / len(last5)

    def get_map_stats(self, map_name: str) -> MapStats:
        if map_name not in self.map_stats:
            self.map_stats[map_name] = MapStats(map_name=map_name)
        return self.map_stats[map_name]


@dataclass
class EngineParameters:
    """All tunable parameters for the prediction engine."""
    rank_weight: float = 0.0015
    map_weight: float = 0.18
    pick_bonus: float = 0.04
    form_multiplier: float = 0.025
    odds_weight: float = 0.10
    rounds_bias_multiplier: float = 0.015
    pistol_weight: float = 1.0
    smooth_base: float = 5.0
    day_form_variance: float = 0.06
    force_buy_penalty: float = 0.15
    eco_penalty: float = 0.22
    tilt_resilience: float = 0.25
    snowball_limit: float = 0.15

    # Parameter bounds for optimization
    BOUNDS = {
        "rank_weight": (0.001, 0.005),
        "map_weight": (0.10, 0.30),
        "pick_bonus": (0.02, 0.08),
        "form_multiplier": (0.01, 0.05),
        "odds_weight": (0.05, 0.20),
        "rounds_bias_multiplier": (0.01, 0.03),
        "pistol_weight": (0.5, 1.5),
        "smooth_base": (3.0, 10.0),
        "day_form_variance": (0.02, 0.12),
        "force_buy_penalty": (0.10, 0.20),
        "eco_penalty": (0.15, 0.30),
        "tilt_resilience": (0.15, 0.35),
        "snowball_limit": (0.10, 0.20),
    }

    def to_dict(self) -> Dict[str, float]:
        return {
            "rank_weight": self.rank_weight,
            "map_weight": self.map_weight,
            "pick_bonus": self.pick_bonus,
            "form_multiplier": self.form_multiplier,
            "odds_weight": self.odds_weight,
            "rounds_bias_multiplier": self.rounds_bias_multiplier,
            "pistol_weight": self.pistol_weight,
            "smooth_base": self.smooth_base,
            "day_form_variance": self.day_form_variance,
            "force_buy_penalty": self.force_buy_penalty,
            "eco_penalty": self.eco_penalty,
            "tilt_resilience": self.tilt_resilience,
            "snowball_limit": self.snowball_limit,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "EngineParameters":
        return cls(**{k: v for k, v in d.items() if k in cls.BOUNDS})

    @classmethod
    def from_array(cls, arr: list, keys: Optional[List[str]] = None) -> "EngineParameters":
        if keys is None:
            keys = list(cls.BOUNDS.keys())
        return cls(**{k: v for k, v in zip(keys, arr)})

    def to_array(self, keys: Optional[List[str]] = None) -> list:
        if keys is None:
            keys = list(self.BOUNDS.keys())
        d = self.to_dict()
        return [d[k] for k in keys]


@dataclass
class MapPrediction:
    """Prediction for a single map."""
    map_name: str
    team1_win_prob: float
    team2_win_prob: float
    predicted_score_t1: int
    predicted_score_t2: int
    total_rounds: int
    confidence: float
    picked_by: Optional[str] = None  # team name that picked this map

    @property
    def predicted_winner_prob(self) -> float:
        return max(self.team1_win_prob, self.team2_win_prob)


@dataclass
class MatchPrediction:
    """Full match prediction result."""
    team1: str
    team2: str
    match_format: str
    winner: str
    winner_probability: float
    map_predictions: List[MapPrediction]
    predicted_score: str  # e.g., "2:1"
    total_rounds_prediction: float
    over_under_line: float = 26.5
    over_probability: float = 0.5
    model_breakdown: Dict[str, float] = field(default_factory=dict)
    confidence: str = "Medium"  # Low / Medium / High

    def summary(self) -> str:
        lines = [
            f"{'=' * 50}",
            f"  {self.team1} vs {self.team2} ({self.match_format})",
            f"{'=' * 50}",
            f"  Winner: {self.winner} ({self.winner_probability:.1%})",
            f"  Score:  {self.predicted_score}",
            f"  Confidence: {self.confidence}",
            f"{'─' * 50}",
        ]
        if self.map_predictions:
            lines.append("  Maps:")
            for mp in self.map_predictions:
                winner = self.team1 if mp.team1_win_prob > 0.5 else self.team2
                lines.append(
                    f"    {mp.map_name}: {winner} "
                    f"({max(mp.team1_win_prob, mp.team2_win_prob):.1%}) "
                    f"[{mp.predicted_score_t1}:{mp.predicted_score_t2}]"
                )
            lines.append(f"{'─' * 50}")
        lines.append(
            f"  Total Rounds: {self.total_rounds_prediction:.1f} "
            f"(Over {self.over_under_line}: {self.over_probability:.1%})"
        )
        if self.model_breakdown:
            lines.append(f"{'─' * 50}")
            lines.append("  Model Breakdown:")
            for model, prob in self.model_breakdown.items():
                lines.append(f"    {model}: {prob:.1%}")
        lines.append(f"{'=' * 50}")
        return "\n".join(lines)


@dataclass
class HistoricalMatch:
    """Historical match for optimizer training."""
    team1: str
    team2: str
    team1_ranking: int
    team2_ranking: int
    map_name: str
    team1_map_winrate: float
    team2_map_winrate: float
    team1_form: float
    team2_form: float
    team1_odds: float
    team2_odds: float
    picked_by: Optional[str] = None
    actual_winner: str = ""
    actual_score_t1: int = 0
    actual_score_t2: int = 0
    team1_pistol_wr: float = 0.5
    team2_pistol_wr: float = 0.5
