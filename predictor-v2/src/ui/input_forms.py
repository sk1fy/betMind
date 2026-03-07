"""Input forms for CS2 match data entry."""

import os
import sys
from typing import Dict, List, Optional, Tuple

from ..core.data_types import (
    TeamData, MapStats, MapName, MatchFormat, HistoricalMatch,
)
from .styles import (
    BOLD, RESET, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW,
    BRIGHT_WHITE, DIM, GREEN, RED, YELLOW, CYAN,
    header_box, section_line, colored, bold, dim,
    BOX_V, ARROW_RIGHT, BULLET, CHECK,
)


CS2_MAPS = [
    "Mirage", "Inferno", "Nuke", "Overpass",
    "Ancient", "Anubis", "Dust2", "Vertigo", "Train",
]


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def input_colored(prompt: str) -> str:
    """Input with colored prompt."""
    return input(f"{BRIGHT_CYAN}{ARROW_RIGHT}{RESET} {prompt}").strip()


def input_float(prompt: str, default: float = 0.0, min_val: float = -999,
                max_val: float = 999) -> float:
    """Input a float with validation."""
    while True:
        raw = input_colored(f"{prompt} [{default}]: ")
        if not raw:
            return default
        try:
            val = float(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  {RED}Value must be between {min_val} and {max_val}{RESET}")
        except ValueError:
            print(f"  {RED}Invalid number{RESET}")


def input_int(prompt: str, default: int = 0, min_val: int = -999,
              max_val: int = 999) -> int:
    """Input an integer with validation."""
    while True:
        raw = input_colored(f"{prompt} [{default}]: ")
        if not raw:
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  {RED}Value must be between {min_val} and {max_val}{RESET}")
        except ValueError:
            print(f"  {RED}Invalid number{RESET}")


def input_choice(prompt: str, options: List[str], allow_empty: bool = False) -> Optional[str]:
    """Show numbered options and get user choice."""
    for i, opt in enumerate(options, 1):
        print(f"  {DIM}{i}.{RESET} {opt}")
    while True:
        raw = input_colored(f"{prompt}: ")
        if not raw and allow_empty:
            return None
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            # Try matching by name
            for opt in options:
                if opt.lower().startswith(raw.lower()):
                    return opt
        print(f"  {RED}Invalid choice{RESET}")


def input_team_data(team_label: str) -> TeamData:
    """Full form to input team data."""
    print(f"\n{BOLD}{BRIGHT_GREEN}  {BULLET} {team_label} Data{RESET}")
    print(f"  {section_line(40)}")

    name = input_colored(f"Team name: ")
    if not name:
        name = team_label

    ranking = input_int("HLTV Ranking", default=30, min_val=1, max_val=500)
    form = input_float("Form score (0.0-1.0)", default=0.5, min_val=0.0, max_val=1.0)
    odds = input_float("Bookmaker odds", default=2.0, min_val=1.01, max_val=50.0)

    # Recent results
    results_raw = input_colored("Recent results (e.g. WWLWL) [empty to skip]: ")
    recent_results = list(results_raw.upper()) if results_raw else []

    return TeamData(
        name=name,
        ranking=ranking,
        form_score=form,
        odds=odds,
        recent_results=recent_results,
    )


def input_map_stats_for_team(team: TeamData, map_name: str) -> None:
    """Input map-specific stats for a team."""
    print(f"\n  {DIM}{team.name} on {map_name}:{RESET}")
    wins = input_int(f"  Wins on {map_name}", default=5, min_val=0, max_val=100)
    losses = input_int(f"  Losses on {map_name}", default=5, min_val=0, max_val=100)
    pistol_wins = input_int(f"  Pistol round wins", default=4, min_val=0, max_val=50)
    pistol_total = input_int(f"  Pistol round total", default=8, min_val=0, max_val=100)

    team.map_stats[map_name] = MapStats(
        map_name=map_name,
        wins=wins,
        losses=losses,
        pistol_wins=pistol_wins,
        pistol_total=max(pistol_total, 1),
    )


def input_maps(team1_name: str, team2_name: str) -> Tuple[List[Dict[str, str]], str]:
    """Input maps for the match."""
    print(f"\n{BOLD}{BRIGHT_YELLOW}  Map Selection{RESET}")
    print(f"  {section_line(40)}")

    # Match format
    print(f"\n  Match format:")
    fmt_options = ["BO1", "BO3", "BO5"]
    match_format = input_choice("Format", fmt_options) or "BO3"

    num_maps = {"BO1": 1, "BO3": 3, "BO5": 5}[match_format]

    print(f"\n  Available maps:")
    maps = []
    for i in range(num_maps):
        print(f"\n  {BOLD}Map {i + 1}/{num_maps}:{RESET}")
        map_name = input_choice("Select map", CS2_MAPS) or CS2_MAPS[0]

        # Who picked this map?
        pick_options = [team1_name, team2_name, "Decider (no pick)"]
        picked_raw = input_choice("Picked by", pick_options, allow_empty=True)
        picked_by = None
        if picked_raw and picked_raw != "Decider (no pick)":
            picked_by = picked_raw

        maps.append({"name": map_name, "picked_by": picked_by})

    return maps, match_format


def input_quick_prediction() -> Tuple[TeamData, TeamData, List[Dict[str, str]], str]:
    """Quick prediction with minimal input."""
    clear_screen()
    print(header_box("Quick Prediction"))
    print()

    # Team 1
    t1_name = input_colored("Team 1 name: ") or "Team A"
    t1_rank = input_int("Team 1 ranking", default=20, min_val=1, max_val=500)
    t1_odds = input_float("Team 1 odds", default=1.8, min_val=1.01, max_val=50.0)

    print()

    # Team 2
    t2_name = input_colored("Team 2 name: ") or "Team B"
    t2_rank = input_int("Team 2 ranking", default=25, min_val=1, max_val=500)
    t2_odds = input_float("Team 2 odds", default=2.1, min_val=1.01, max_val=50.0)

    team1 = TeamData(name=t1_name, ranking=t1_rank, odds=t1_odds)
    team2 = TeamData(name=t2_name, ranking=t2_rank, odds=t2_odds)

    # Maps
    maps, match_format = input_maps(t1_name, t2_name)

    return team1, team2, maps, match_format


def input_detailed_prediction() -> Tuple[TeamData, TeamData, List[Dict[str, str]], str]:
    """Detailed prediction with full stats input."""
    clear_screen()
    print(header_box("Detailed Prediction"))
    print()

    # Team 1
    team1 = input_team_data("Team 1")
    print()

    # Team 2
    team2 = input_team_data("Team 2")

    # Maps
    maps, match_format = input_maps(team1.name, team2.name)

    # Map-specific stats
    print(f"\n{BOLD}{BRIGHT_YELLOW}  Map Statistics{RESET}")
    enter_stats = input_colored("Enter map-specific stats? (y/n) [n]: ").lower()
    if enter_stats == "y":
        for m in maps:
            input_map_stats_for_team(team1, m["name"])
            input_map_stats_for_team(team2, m["name"])

    return team1, team2, maps, match_format


def input_historical_match() -> HistoricalMatch:
    """Form to input a historical match for training the optimizer."""
    clear_screen()
    print(header_box("Add Historical Match"))
    print()

    team1 = input_colored("Team 1 name: ") or "Team A"
    team2 = input_colored("Team 2 name: ") or "Team B"
    t1_rank = input_int("Team 1 ranking", default=20, min_val=1, max_val=500)
    t2_rank = input_int("Team 2 ranking", default=25, min_val=1, max_val=500)
    map_name = input_choice("Map played", CS2_MAPS) or CS2_MAPS[0]
    t1_wr = input_float(f"Team 1 win% on {map_name} (0-1)", default=0.5, min_val=0.0, max_val=1.0)
    t2_wr = input_float(f"Team 2 win% on {map_name} (0-1)", default=0.5, min_val=0.0, max_val=1.0)
    t1_form = input_float("Team 1 form (0-1)", default=0.5, min_val=0.0, max_val=1.0)
    t2_form = input_float("Team 2 form (0-1)", default=0.5, min_val=0.0, max_val=1.0)
    t1_odds = input_float("Team 1 odds", default=1.8, min_val=1.01, max_val=50.0)
    t2_odds = input_float("Team 2 odds", default=2.1, min_val=1.01, max_val=50.0)

    winner_options = [team1, team2]
    actual_winner = input_choice("Actual winner", winner_options) or team1
    t1_score = input_int("Team 1 rounds", default=13, min_val=0, max_val=30)
    t2_score = input_int("Team 2 rounds", default=10, min_val=0, max_val=30)

    return HistoricalMatch(
        team1=team1,
        team2=team2,
        team1_ranking=t1_rank,
        team2_ranking=t2_rank,
        map_name=map_name,
        team1_map_winrate=t1_wr,
        team2_map_winrate=t2_wr,
        team1_form=t1_form,
        team2_form=t2_form,
        team1_odds=t1_odds,
        team2_odds=t2_odds,
        actual_winner=actual_winner,
        actual_score_t1=t1_score,
        actual_score_t2=t2_score,
    )
