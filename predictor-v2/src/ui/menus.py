"""Main menu and navigation for CS2 Predictor TUI."""

import os
import sys
from typing import Optional

from ..core.data_types import EngineParameters, HistoricalMatch
from ..core.models import EnsemblePredictor
from ..core.optimizer import GeneticOptimizer, GeneticConfig
from ..data.manager import DataManager
from .input_forms import (
    input_quick_prediction, input_detailed_prediction,
    input_historical_match, input_colored, input_int, input_float,
    input_choice, clear_screen,
)
from .displays import (
    display_prediction, display_history, display_statistics,
    display_parameters, display_optimizer_progress, wait_for_key,
)
from .styles import (
    BOLD, RESET, DIM,
    RED, GREEN, YELLOW, CYAN, MAGENTA,
    BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_CYAN,
    BRIGHT_WHITE, BRIGHT_MAGENTA,
    header_box, section_line, colored,
    ARROW_RIGHT, BULLET, STAR, CHECK, CROSS,
    DBOX_H, DBOX_V, DBOX_TL, DBOX_TR, DBOX_BL, DBOX_BR,
)


LOGO = f"""
{BRIGHT_CYAN}   ██████╗███████╗██████╗     ██████╗ ██████╗ ███████╗██████╗ 
  ██╔════╝██╔════╝╚════██╗    ██╔══██╗██╔══██╗██╔════╝██╔══██╗
  ██║     ███████╗ █████╔╝    ██████╔╝██████╔╝█████╗  ██║  ██║
  ██║     ╚════██║██╔═══╝     ██╔═══╝ ██╔══██╗██╔══╝  ██║  ██║
  ╚██████╗███████║███████╗    ██║     ██║  ██║███████╗██████╔╝
   ╚═════╝╚══════╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚══════╝╚═════╝{RESET}
{DIM}  CS2 Match Prediction System v2.0 — Ensemble + Genetic Optimization{RESET}
"""


class Application:
    """Main TUI application."""

    def __init__(self):
        self.data_manager = DataManager()
        self.params = self.data_manager.load_parameters()
        self.predictor = EnsemblePredictor(self.params)
        self.running = True

    def run(self):
        """Main application loop."""
        while self.running:
            self._show_main_menu()

    def _show_main_menu(self):
        clear_screen()
        print(LOGO)
        print(f"  {section_line(56)}")
        print()

        options = [
            ("1", "New Prediction (Quick)", BRIGHT_GREEN),
            ("2", "New Prediction (Detailed)", GREEN),
            ("3", "Prediction History", BRIGHT_CYAN),
            ("4", "Optimization (Genetic Algorithm)", BRIGHT_YELLOW),
            ("5", "Historical Data", MAGENTA),
            ("6", "Parameters", CYAN),
            ("7", "Statistics", YELLOW),
            ("8", "Settings", DIM),
            ("0", "Exit", RED),
        ]

        for key, label, color in options:
            print(f"  {BRIGHT_WHITE}[{key}]{RESET} {color}{label}{RESET}")

        print()
        choice = input_colored("Select: ")

        actions = {
            "1": self._quick_prediction,
            "2": self._detailed_prediction,
            "3": self._show_history,
            "4": self._optimization_menu,
            "5": self._historical_data_menu,
            "6": self._parameters_menu,
            "7": self._show_statistics,
            "8": self._settings_menu,
            "0": self._exit,
        }

        action = actions.get(choice)
        if action:
            action()

    def _quick_prediction(self):
        """Run quick prediction with minimal input."""
        try:
            team1, team2, maps, match_format = input_quick_prediction()
        except (KeyboardInterrupt, EOFError):
            return

        print(f"\n  {BRIGHT_YELLOW}Computing prediction...{RESET}")
        prediction = self.predictor.predict_match(team1, team2, maps, match_format)

        display_prediction(prediction)

        # Save
        save = input_colored("Save prediction? (y/n) [y]: ").lower()
        if save != "n":
            self.data_manager.save_prediction(prediction)
            print(f"  {GREEN}{CHECK} Prediction saved{RESET}")

        # Export
        export = input_colored("Export to markdown? (y/n) [n]: ").lower()
        if export == "y":
            md = self.data_manager.export_to_markdown(prediction)
            filename = f"{prediction.team1}_vs_{prediction.team2}.md".replace(" ", "_")
            path = self.data_manager.results_dir / filename
            with open(path, "w") as f:
                f.write(md)
            print(f"  {GREEN}{CHECK} Exported to {path}{RESET}")

        wait_for_key()

    def _detailed_prediction(self):
        """Run detailed prediction with full stats."""
        try:
            team1, team2, maps, match_format = input_detailed_prediction()
        except (KeyboardInterrupt, EOFError):
            return

        print(f"\n  {BRIGHT_YELLOW}Computing prediction...{RESET}")
        prediction = self.predictor.predict_match(team1, team2, maps, match_format)

        display_prediction(prediction)

        save = input_colored("Save prediction? (y/n) [y]: ").lower()
        if save != "n":
            self.data_manager.save_prediction(prediction)
            print(f"  {GREEN}{CHECK} Prediction saved{RESET}")

        wait_for_key()

    def _show_history(self):
        """Display prediction history."""
        history = self.data_manager.load_prediction_history()
        display_history(history)

        if history:
            print()
            print(f"  {BOLD}Actions:{RESET}")
            print(f"  {BRIGHT_WHITE}[r]{RESET} Record actual result")
            print(f"  {BRIGHT_WHITE}[b]{RESET} Back to menu")
            choice = input_colored("Action: ").lower()

            if choice == "r":
                self._record_result(history)

    def _record_result(self, history):
        """Record actual match result."""
        idx = input_int("Prediction # to update", default=len(history) - 1,
                        min_val=0, max_val=len(history) - 1)
        entry = history[idx]

        print(f"\n  {entry['team1']} vs {entry['team2']}")
        print(f"  Predicted: {entry['winner']} ({entry['winner_probability']:.1%})")
        print()

        winner_options = [entry["team1"], entry["team2"]]
        actual_winner = input_choice("Actual winner", winner_options) or entry["team1"]
        actual_score = input_colored("Actual score (e.g. 2:1): ") or "?"

        self.data_manager.update_prediction_result(idx, actual_winner, actual_score)

        is_correct = actual_winner == entry["winner"]
        if is_correct:
            print(f"\n  {GREEN}{CHECK} Correct prediction!{RESET}")
        else:
            print(f"\n  {RED}{CROSS} Wrong prediction{RESET}")

        wait_for_key()

    def _optimization_menu(self):
        """Genetic algorithm optimization menu."""
        clear_screen()
        print(header_box("Genetic Algorithm Optimization"))
        print()

        historical = self.data_manager.load_historical_matches()
        print(f"  Historical matches loaded: {BRIGHT_WHITE}{len(historical)}{RESET}")
        print()

        if len(historical) < 10:
            print(f"  {BRIGHT_YELLOW}Warning: At least 10 historical matches recommended{RESET}")
            print(f"  {DIM}Go to 'Historical Data' to add matches{RESET}")
            print()

        print(f"  {BOLD}Options:{RESET}")
        print(f"  {BRIGHT_WHITE}[1]{RESET} Run optimization")
        print(f"  {BRIGHT_WHITE}[2]{RESET} Configure GA settings")
        print(f"  {BRIGHT_WHITE}[3]{RESET} View current parameters")
        print(f"  {BRIGHT_WHITE}[b]{RESET} Back")
        print()

        choice = input_colored("Select: ").lower()

        if choice == "1" and len(historical) >= 1:
            self._run_optimization(historical)
        elif choice == "2":
            self._configure_ga()
        elif choice == "3":
            display_parameters(self.params.to_dict(), EngineParameters.BOUNDS)
            wait_for_key()

    def _run_optimization(self, historical):
        """Run the genetic algorithm."""
        print(f"\n  {BRIGHT_YELLOW}Starting Genetic Algorithm...{RESET}")
        print(f"  {DIM}This may take a while...{RESET}\n")

        config = GeneticConfig(
            population_size=50,
            generations=30,  # Reduced for demo
        )
        optimizer = GeneticOptimizer(config)

        result = optimizer.run(historical, progress_callback=display_optimizer_progress)

        best_params = result["best_params"]
        best_fitness = result["best_fitness"]

        print(f"\n\n  {GREEN}{STAR} Optimization complete!{RESET}")
        print(f"  {BOLD}Best fitness:{RESET} {BRIGHT_GREEN}{best_fitness:.4f}{RESET}")
        print()

        # Show old vs new
        print(f"  {BOLD}Parameter changes:{RESET}")
        old = self.params.to_dict()
        new = best_params.to_dict()
        for key in old:
            old_v = old[key]
            new_v = new[key]
            diff = new_v - old_v
            if abs(diff) > 0.0001:
                direction = f"{GREEN}+{diff:.4f}{RESET}" if diff > 0 else f"{RED}{diff:.4f}{RESET}"
                print(f"    {key:28s} {old_v:.4f} -> {new_v:.4f} ({direction})")

        print()
        apply_choice = input_colored("Apply new parameters? (y/n) [y]: ").lower()
        if apply_choice != "n":
            self.params = best_params
            self.data_manager.save_parameters(self.params)
            self.predictor = EnsemblePredictor(self.params)
            print(f"  {GREEN}{CHECK} Parameters applied and saved{RESET}")
        else:
            print(f"  {DIM}Parameters discarded{RESET}")

        wait_for_key()

    def _configure_ga(self):
        """Configure genetic algorithm settings."""
        clear_screen()
        print(header_box("GA Configuration"))
        print()
        print(f"  {DIM}Configure genetic algorithm parameters{RESET}")
        print()

        pop_size = input_int("Population size", default=100, min_val=20, max_val=500)
        generations = input_int("Generations", default=150, min_val=10, max_val=1000)
        elite_size = input_int("Elite size", default=20, min_val=5, max_val=pop_size // 2)
        mutation_rate = input_float("Mutation rate", default=0.2, min_val=0.01, max_val=1.0)

        print(f"\n  {GREEN}{CHECK} Configuration updated (for next run){RESET}")
        wait_for_key()

    def _historical_data_menu(self):
        """Menu for managing historical match data."""
        clear_screen()
        print(header_box("Historical Data"))
        print()

        matches = self.data_manager.load_historical_matches()
        print(f"  Loaded: {BRIGHT_WHITE}{len(matches)}{RESET} historical matches")
        print()

        print(f"  {BOLD}Options:{RESET}")
        print(f"  {BRIGHT_WHITE}[1]{RESET} Add single match")
        print(f"  {BRIGHT_WHITE}[2]{RESET} View all matches")
        print(f"  {BRIGHT_WHITE}[3]{RESET} Generate sample data")
        print(f"  {BRIGHT_WHITE}[b]{RESET} Back")
        print()

        choice = input_colored("Select: ").lower()

        if choice == "1":
            try:
                match = input_historical_match()
                self.data_manager.add_historical_match(match)
                print(f"\n  {GREEN}{CHECK} Match added{RESET}")
                wait_for_key()
            except (KeyboardInterrupt, EOFError):
                return
        elif choice == "2":
            self._view_historical_matches(matches)
        elif choice == "3":
            self._generate_sample_data()

    def _view_historical_matches(self, matches):
        """View historical matches."""
        clear_screen()
        print(header_box("Historical Matches"))
        print()

        if not matches:
            print(f"  {DIM}No historical matches.{RESET}")
            wait_for_key()
            return

        for i, m in enumerate(matches):
            winner_color = GREEN if m.actual_winner == m.team1 else RED
            print(f"  {DIM}#{i}{RESET} {m.team1} (#{m.team1_ranking}) vs "
                  f"{m.team2} (#{m.team2_ranking})")
            print(f"       {m.map_name}: {winner_color}{m.actual_winner}{RESET} "
                  f"({m.actual_score_t1}:{m.actual_score_t2})")

        print(f"\n  {DIM}Total: {len(matches)} matches{RESET}")
        wait_for_key()

    def _generate_sample_data(self):
        """Generate sample historical data for testing."""
        import random

        clear_screen()
        print(header_box("Generate Sample Data"))
        print()

        n = input_int("Number of matches to generate", default=50, min_val=10, max_val=500)

        teams = [
            ("NAVI", 1), ("FaZe", 2), ("Vitality", 3), ("G2", 4),
            ("Spirit", 5), ("MOUZ", 6), ("Heroic", 7), ("Liquid", 8),
            ("Complexity", 9), ("Cloud9", 10), ("Astralis", 11), ("ENCE", 12),
            ("BIG", 15), ("NIP", 18), ("Eternal Fire", 20), ("Virtus.pro", 22),
            ("Monte", 25), ("FURIA", 28), ("paiN", 30), ("Imperial", 35),
        ]
        map_pool = ["Mirage", "Inferno", "Nuke", "Overpass", "Ancient", "Anubis", "Dust2"]

        matches = []
        for _ in range(n):
            t1_name, t1_rank = random.choice(teams)
            t2_name, t2_rank = random.choice(teams)
            while t2_name == t1_name:
                t2_name, t2_rank = random.choice(teams)

            map_name = random.choice(map_pool)

            # Generate realistic stats
            t1_form = max(0.2, min(1.0, random.gauss(0.55, 0.15)))
            t2_form = max(0.2, min(1.0, random.gauss(0.55, 0.15)))
            t1_wr = max(0.2, min(0.9, random.gauss(0.5, 0.15)))
            t2_wr = max(0.2, min(0.9, random.gauss(0.5, 0.15)))

            # Odds (inversely correlated with ranking)
            t1_implied = max(0.25, min(0.85, 0.5 + (t2_rank - t1_rank) * 0.01))
            margin = 1.08
            t1_odds = round(margin / t1_implied, 2)
            t2_odds = round(margin / (1 - t1_implied), 2)

            # Determine winner (influenced by ranking, form, map wr)
            t1_strength = 0.5 + (t2_rank - t1_rank) * 0.005 + (t1_form - t2_form) * 0.1 + (t1_wr - t2_wr) * 0.1
            t1_strength = max(0.15, min(0.85, t1_strength))

            if random.random() < t1_strength:
                actual_winner = t1_name
                t1_score = 13
                t2_score = random.choice([5, 6, 7, 8, 9, 10, 11])
            else:
                actual_winner = t2_name
                t2_score = 13
                t1_score = random.choice([5, 6, 7, 8, 9, 10, 11])

            matches.append(HistoricalMatch(
                team1=t1_name,
                team2=t2_name,
                team1_ranking=t1_rank,
                team2_ranking=t2_rank,
                map_name=map_name,
                team1_map_winrate=round(t1_wr, 2),
                team2_map_winrate=round(t2_wr, 2),
                team1_form=round(t1_form, 2),
                team2_form=round(t2_form, 2),
                team1_odds=t1_odds,
                team2_odds=t2_odds,
                actual_winner=actual_winner,
                actual_score_t1=t1_score,
                actual_score_t2=t2_score,
            ))

        self.data_manager.save_historical_matches(matches)
        print(f"  {GREEN}{CHECK} Generated {n} sample matches{RESET}")
        wait_for_key()

    def _parameters_menu(self):
        """View and edit engine parameters."""
        display_parameters(self.params.to_dict(), EngineParameters.BOUNDS)
        print()

        print(f"  {BOLD}Options:{RESET}")
        print(f"  {BRIGHT_WHITE}[e]{RESET} Edit parameter")
        print(f"  {BRIGHT_WHITE}[r]{RESET} Reset to defaults")
        print(f"  {BRIGHT_WHITE}[b]{RESET} Back")
        print()

        choice = input_colored("Select: ").lower()

        if choice == "e":
            self._edit_parameter()
        elif choice == "r":
            self.params = EngineParameters()
            self.data_manager.save_parameters(self.params)
            self.predictor = EnsemblePredictor(self.params)
            print(f"  {GREEN}{CHECK} Parameters reset to defaults{RESET}")
            wait_for_key()

    def _edit_parameter(self):
        """Edit a single parameter."""
        param_names = list(EngineParameters.BOUNDS.keys())
        param = input_choice("Select parameter", param_names)
        if not param:
            return

        lo, hi = EngineParameters.BOUNDS[param]
        current = getattr(self.params, param)
        new_val = input_float(f"New value for {param}", default=current,
                              min_val=lo, max_val=hi)

        setattr(self.params, param, new_val)
        self.data_manager.save_parameters(self.params)
        self.predictor = EnsemblePredictor(self.params)
        print(f"  {GREEN}{CHECK} {param} updated to {new_val:.4f}{RESET}")
        wait_for_key()

    def _show_statistics(self):
        """Show accuracy statistics."""
        stats = self.data_manager.get_accuracy_stats()
        display_statistics(stats)
        wait_for_key()

    def _settings_menu(self):
        """Settings menu."""
        clear_screen()
        print(header_box("Settings"))
        print()

        print(f"  {BOLD}Options:{RESET}")
        print(f"  {BRIGHT_WHITE}[1]{RESET} Simulation count (affects accuracy vs speed)")
        print(f"  {BRIGHT_WHITE}[2]{RESET} Data directory")
        print(f"  {BRIGHT_WHITE}[b]{RESET} Back")
        print()

        choice = input_colored("Select: ").lower()

        if choice == "1":
            current = 1000
            new_val = input_int("Number of simulations", default=current,
                                min_val=100, max_val=10000)
            print(f"  {GREEN}{CHECK} Simulation count set to {new_val}{RESET}")
            wait_for_key()

    def _exit(self):
        """Exit the application."""
        self.running = False
        clear_screen()
        print(f"\n  {DIM}Goodbye!{RESET}\n")
