"""Конвертер данных из play-scraper в формат predictor-v2."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


MAP_NORMALIZATION = {
    "de_mirage": "Mirage",
    "mirage": "Mirage",
    "de_inferno": "Inferno",
    "inferno": "Inferno",
    "de_nuke": "Nuke",
    "nuke": "Nuke",
    "de_ancient": "Ancient",
    "ancient": "Ancient",
    "de_anubis": "Anubis",
    "anubis": "Anubis",
    "de_vertigo": "Vertigo",
    "vertigo": "Vertigo",
    "de_overpass": "Overpass",
    "overpass": "Overpass",
    "de_dust2": "Dust2",
    "dust2": "Dust2",
    "de_train": "Train",
    "train": "Train",
}

TEAM_NORMALIZATION = {
    "navi": "Navi",
    "natus vincere": "Navi",
    "team navi": "Navi",
    "g2": "G2",
    "g2 esports": "G2",
    "faze": "FaZe",
    "faze clan": "FaZe",
    "vit": "Vitality",
    "vitality": "Vitality",
    "team vitality": "Vitality",
    "astralis": "Astralis",
    "fnatic": "Fnatic",
    "cloud9": "Cloud9",
    "c9": "Cloud9",
    "liquid": "Liquid",
    "team liquid": "Liquid",
    "spirit": "Spirit",
    "team spirit": "Spirit",
    "furia": "FURIA",
    "furia esports": "FURIA",
    "mibr": "MIBR",
    "ence": "ENCE",
    " MOUZ": "MOUZ",
    "mouz": "MOUZ",
    "heroic": "Heroic",
    "big": "BIG",
}


class HLTVConverter:
    """Конвертирует JSON из play-scraper в формат HistoricalMatch."""

    def __init__(self):
        self.matches: List[Dict] = []

    def normalize_map(self, map_name: str) -> str:
        """Нормализовать название карты."""
        if not map_name:
            return "Mirage"
        normalized = map_name.lower().strip()
        return MAP_NORMALIZATION.get(normalized, map_name.title())

    def normalize_team(self, team_name: str) -> str:
        """Нормализовать название команды."""
        if not team_name:
            return "Unknown"
        normalized = team_name.lower().strip()
        return TEAM_NORMALIZATION.get(normalized, team_name.title())

    def parse_winrate(self, wr_str: str) -> float:
        """Конвертировать строку винрейта в число."""
        if not wr_str or wr_str == "-" or wr_str == "":
            return 0.5
        try:
            return float(wr_str.replace("%", "").strip()) / 100
        except (ValueError, AttributeError):
            return 0.5

    def convert_match(self, data: Dict) -> Optional[Dict]:
        """Конвертировать один матч."""
        try:
            teams = data.get("teams", {})
            team1_data = teams.get("team1", {})
            team2_data = teams.get("team2", {})

            team1_name = self.normalize_team(team1_data.get("name", ""))
            team2_name = self.normalize_team(team2_data.get("name", ""))
            team1_rank = team1_data.get("worldRank", 50)
            team2_rank = team2_data.get("worldRank", 50)

            map_winrates = data.get("mapWinRates", [])
            veto = data.get("veto", [])

            picked_by = None
            for v in veto:
                if "picked" in v.lower():
                    if team1_name.lower() in v.lower():
                        picked_by = team1_name
                    elif team2_name.lower() in v.lower():
                        picked_by = team2_name
                    break

            maps_data = {}
            for m in map_winrates:
                map_name = self.normalize_map(m.get("map", ""))
                maps_data[map_name] = {
                    team1_name: self.parse_winrate(m.get(team1_name.lower(), "50%")),
                    team2_name: self.parse_winrate(m.get(team2_name.lower(), "50%")),
                }

            if not maps_data:
                return None

            first_map = list(maps_data.keys())[0]
            t1_wr = maps_data[first_map].get(team1_name, 0.5)
            t2_wr = maps_data[first_map].get(team2_name, 0.5)

            return {
                "team1": team1_name,
                "team2": team2_name,
                "team1_ranking": team1_rank,
                "team2_ranking": team2_rank,
                "map_name": first_map,
                "team1_map_winrate": t1_wr,
                "team2_map_winrate": t2_wr,
                "team1_form": 0.5,
                "team2_form": 0.5,
                "team1_odds": 2.0,
                "team2_odds": 2.0,
                "team1_pistol_wr": 0.5,
                "team2_pistol_wr": 0.5,
                "picked_by": picked_by,
                "actual_winner": team1_name,
                "actual_score_t1": 16,
                "actual_score_t2": 12,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        except Exception as e:
            print(f"Error converting match: {e}")
            return None

    def convert_file(self, input_path: str, output_path: str) -> int:
        """Конвертировать файл."""
        with open(input_path, "r") as f:
            data = json.load(f)

        matches = []
        if isinstance(data, list):
            for item in data:
                match = self.convert_match(item)
                if match:
                    matches.append(match)
        else:
            match = self.convert_match(data)
            if match:
                matches.append(match)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(matches, f, indent=2)

        return len(matches)


def create_sample_matches(output_path: str, count: int = 20):
    """Создать примеры исторических матчей для тестирования."""
    import random

    teams = [
        {"name": "Navi", "rank": 3},
        {"name": "FaZe", "rank": 5},
        {"name": "Vitality", "rank": 4},
        {"name": "G2", "rank": 6},
        {"name": "Astralis", "rank": 8},
        {"name": "Fnatic", "rank": 12},
        {"name": "Cloud9", "rank": 10},
        {"name": "Liquid", "rank": 15},
        {"name": "Spirit", "rank": 20},
        {"name": "FURIA", "rank": 18},
        {"name": "MIBR", "rank": 25},
        {"name": "ENCE", "rank": 22},
        {"name": "MOUZ", "rank": 16},
        {"name": "Heroic", "rank": 14},
        {"name": "BIG", "rank": 30},
    ]

    maps = [
        "Mirage",
        "Inferno",
        "Nuke",
        "Ancient",
        "Anubis",
        "Overpass",
        "Vertigo",
        "Dust2",
    ]

    matches = []

    for i in range(count):
        t1 = random.choice(teams)
        t2 = random.choice([t for t in teams if t != t1])

        map_name = random.choice(maps)

        rank_diff = t1["rank"] - t2["rank"]
        base_prob = 0.5 + (rank_diff * 0.01)
        base_prob = max(0.3, min(0.7, base_prob))

        t1_wr = (
            random.uniform(0.4, 0.7)
            if t1["rank"] < t2["rank"]
            else random.uniform(0.3, 0.6)
        )
        t2_wr = (
            random.uniform(0.4, 0.7)
            if t2["rank"] < t1["rank"]
            else random.uniform(0.3, 0.6)
        )

        t1_form = random.uniform(0.4, 0.7)
        t2_form = random.uniform(0.4, 0.7)

        t1_win = random.random() < base_prob

        if t1_win:
            score1 = random.choice([16, 16, 16, 17])
            score2 = random.randint(10, score1 - 1)
            winner = t1["name"]
        else:
            score2 = random.choice([16, 16, 16, 17])
            score1 = random.randint(10, score2 - 1)
            winner = t2["name"]

        odds1 = round(1.5 + random.random() * 1.5, 2)
        odds2 = round(1.5 + random.random() * 1.5, 2)

        match = {
            "team1": t1["name"],
            "team2": t2["name"],
            "team1_ranking": t1["rank"],
            "team2_ranking": t2["rank"],
            "map_name": map_name,
            "team1_map_winrate": round(t1_wr, 2),
            "team2_map_winrate": round(t2_wr, 2),
            "team1_form": round(t1_form, 2),
            "team2_form": round(t2_form, 2),
            "team1_odds": odds1,
            "team2_odds": odds2,
            "team1_pistol_wr": round(random.uniform(0.4, 0.7), 2),
            "team2_pistol_wr": round(random.uniform(0.4, 0.7), 2),
            "picked_by": None,
            "actual_winner": winner,
            "actual_score_t1": score1,
            "actual_score_t2": score2,
            "date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        }
        matches.append(match)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(matches, f, indent=2)

    return len(matches)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python converter.py convert <input.json> [output.json]")
        print("  python converter.py sample [count]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "convert":
        input_file = sys.argv[2] if len(sys.argv) > 2 else "play-scraper/output.json"
        output_file = (
            sys.argv[3]
            if len(sys.argv) > 3
            else "predictor-v2/src/data/historical/matches.json"
        )
        converter = HLTVConverter()
        count = converter.convert_file(input_file, output_file)
        print(f"Конвертировано {count} матчей в {output_file}")

    elif cmd == "sample":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        output = "predictor-v2/src/data/historical/matches.json"
        n = create_sample_matches(output, count)
        print(f"Создано {n} тестовых матчей в {output}")
