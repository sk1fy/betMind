"""Display screens for prediction results, history, and statistics."""

import os
from typing import Dict, List

from ..core.data_types import MatchPrediction, MapPrediction
from .styles import (
    BOLD, RESET, DIM,
    RED, GREEN, YELLOW, BLUE, CYAN, MAGENTA, WHITE,
    BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE,
    BRIGHT_CYAN, BRIGHT_WHITE, BRIGHT_MAGENTA,
    header_box, section_line, colored, bold, dim,
    progress_bar, probability_bar,
    BOX_V, BOX_H, BOX_TL, BOX_TR, BOX_BL, BOX_BR, BOX_L, BOX_R,
    DBOX_H, DBOX_V, DBOX_TL, DBOX_TR, DBOX_BL, DBOX_BR,
    ARROW_RIGHT, BULLET, CHECK, CROSS, STAR, CIRCLE,
    BAR_FULL, BAR_EMPTY,
)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def display_prediction(prediction: MatchPrediction):
    """Display a full match prediction with visual elements."""
    clear_screen()
    w = 58

    # Header
    print(header_box(f"{prediction.team1} vs {prediction.team2}", w))
    print(f"  {DIM}Format: {prediction.match_format}{RESET}")
    print()

    # Winner
    if prediction.winner == prediction.team1:
        winner_color = BRIGHT_GREEN
    else:
        winner_color = BRIGHT_CYAN

    conf_color = {
        "High": BRIGHT_GREEN,
        "Medium": BRIGHT_YELLOW,
        "Low": BRIGHT_RED,
    }.get(prediction.confidence, YELLOW)

    print(f"  {BOLD}{BRIGHT_WHITE}WINNER:{RESET} {winner_color}{BOLD}{prediction.winner}{RESET}")
    print(f"  {BOLD}{BRIGHT_WHITE}Score:{RESET}  {prediction.predicted_score}")
    print(f"  {BOLD}{BRIGHT_WHITE}Confidence:{RESET} {conf_color}{prediction.confidence}{RESET}")
    print()

    # Probability bar
    if prediction.winner == prediction.team1:
        prob = prediction.winner_probability
    else:
        prob = 1.0 - prediction.winner_probability

    t1_width = int(prob * 40)
    t2_width = 40 - t1_width
    bar = f"{GREEN}{BAR_FULL * t1_width}{RED}{BAR_FULL * t2_width}{RESET}"
    print(f"  {BRIGHT_GREEN}{prediction.team1}{RESET}")
    print(f"  {bar}")
    print(f"  {GREEN}{prob:.1%}{RESET}{' ' * 30}{RED}{1 - prob:.1%}{RESET}")
    print(f"  {' ' * 36}{BRIGHT_RED}{prediction.team2}{RESET}")
    print()

    # Map predictions
    print(f"  {section_line(w - 4)}")
    print(f"  {BOLD}{BRIGHT_YELLOW}MAP PREDICTIONS{RESET}")
    print(f"  {section_line(w - 4)}")

    for mp in prediction.map_predictions:
        is_t1 = mp.team1_win_prob > 0.5
        winner = prediction.team1 if is_t1 else prediction.team2
        win_prob = max(mp.team1_win_prob, mp.team2_win_prob)
        color = GREEN if is_t1 else RED

        pick_tag = ""
        if mp.picked_by:
            pick_tag = f" {DIM}(pick: {mp.picked_by}){RESET}"

        print(f"\n  {BOLD}{CYAN}{mp.map_name}{RESET}{pick_tag}")
        print(f"    Winner: {color}{winner}{RESET} ({win_prob:.1%})")
        print(f"    Score:  {mp.predicted_score_t1}:{mp.predicted_score_t2} "
              f"({mp.total_rounds} rounds)")

        # Mini probability bar
        t1_w = int(mp.team1_win_prob * 20)
        t2_w = 20 - t1_w
        mini_bar = f"{GREEN}{BAR_FULL * t1_w}{RED}{BAR_FULL * t2_w}{RESET}"
        print(f"    {mini_bar}")

    print()

    # Totals
    print(f"  {section_line(w - 4)}")
    print(f"  {BOLD}{BRIGHT_YELLOW}TOTALS{RESET}")
    print(f"  {section_line(w - 4)}")
    print(f"    Avg rounds/map:  {prediction.total_rounds_prediction:.1f}")
    print(f"    Over/Under line: {prediction.over_under_line}")

    over_color = GREEN if prediction.over_probability > 0.5 else RED
    under_color = RED if prediction.over_probability > 0.5 else GREEN
    print(f"    Over:  {over_color}{prediction.over_probability:.1%}{RESET}")
    print(f"    Under: {under_color}{1 - prediction.over_probability:.1%}{RESET}")

    # Model breakdown
    if prediction.model_breakdown:
        print()
        print(f"  {section_line(w - 4)}")
        print(f"  {BOLD}{BRIGHT_YELLOW}MODEL BREAKDOWN{RESET}")
        print(f"  {section_line(w - 4)}")

        for model_name, prob in prediction.model_breakdown.items():
            is_t1 = prob > 0.5
            color = GREEN if is_t1 else RED
            team = prediction.team1 if is_t1 else prediction.team2
            bar_w = int(abs(prob - 0.5) * 40)
            bar = f"{color}{BAR_FULL * bar_w}{RESET}"

            print(f"    {model_name:12s} {bar} {color}{prob:.1%}{RESET} ({team})")

    print()
    print(f"  {section_line(w - 4)}")


def display_history(history: List[Dict]):
    """Display prediction history."""
    clear_screen()
    print(header_box("Prediction History"))
    print()

    if not history:
        print(f"  {DIM}No predictions yet.{RESET}")
        return

    for i, entry in enumerate(reversed(history)):
        idx = len(history) - 1 - i
        ts = entry.get("timestamp", "")[:16]
        t1 = entry["team1"]
        t2 = entry["team2"]
        winner = entry["winner"]
        prob = entry["winner_probability"]
        conf = entry["confidence"]

        # Result check
        result_tag = ""
        if entry.get("actual_result"):
            ar = entry["actual_result"]
            if ar["correct"]:
                result_tag = f" {GREEN}{CHECK} CORRECT{RESET}"
            else:
                result_tag = f" {RED}{CROSS} WRONG (was: {ar['winner']}){RESET}"
        else:
            result_tag = f" {DIM}{CIRCLE} unverified{RESET}"

        conf_color = {"High": GREEN, "Medium": YELLOW, "Low": RED}.get(conf, WHITE)

        print(f"  {DIM}#{idx}{RESET} {DIM}{ts}{RESET}")
        print(f"    {t1} vs {t2} ({entry.get('match_format', 'BO3')})")
        print(f"    {ARROW_RIGHT} {BOLD}{winner}{RESET} ({prob:.1%}) "
              f"[{conf_color}{conf}{RESET}]{result_tag}")
        print(f"    Score: {entry.get('predicted_score', '?')}")

        if entry.get("maps"):
            for m in entry["maps"]:
                print(f"      {DIM}{m['map_name']}: {m.get('predicted_score', '?')} "
                      f"({m['team1_win_prob']:.0%}){RESET}")
        print()

    print(f"  {DIM}Total: {len(history)} predictions{RESET}")


def display_statistics(stats: Dict):
    """Display accuracy statistics."""
    clear_screen()
    print(header_box("Statistics"))
    print()

    total = stats["total_predictions"]
    verified = stats["verified_predictions"]
    correct = stats["correct_predictions"]
    accuracy = stats["accuracy"]

    print(f"  {BOLD}Total predictions:{RESET}    {total}")
    print(f"  {BOLD}Verified results:{RESET}     {verified}")
    print(f"  {BOLD}Correct predictions:{RESET}  {correct}")
    print()

    if verified > 0:
        acc_color = GREEN if accuracy >= 0.52 else (YELLOW if accuracy >= 0.45 else RED)
        print(f"  {BOLD}Overall Accuracy:{RESET}  {acc_color}{accuracy:.1%}{RESET}")
        print(f"  {progress_bar(accuracy, width=40, color=acc_color)}")
        print()

        # By confidence
        print(f"  {BOLD}By Confidence Level:{RESET}")
        for conf_level in ["High", "Medium", "Low"]:
            conf_acc = stats["by_confidence"].get(conf_level, 0.0)
            conf_color = {"High": GREEN, "Medium": YELLOW, "Low": RED}[conf_level]
            bar = progress_bar(conf_acc, width=25, color=conf_color)
            print(f"    {conf_level:8s} {bar} {conf_acc:.1%}")

        # Target line
        print()
        target = 0.52
        if accuracy >= target:
            print(f"  {GREEN}{CHECK} Above target ({target:.0%}){RESET}")
        else:
            diff = target - accuracy
            print(f"  {RED}{CROSS} Below target ({target:.0%}) by {diff:.1%}{RESET}")
    else:
        print(f"  {DIM}No verified predictions. Add actual results to see accuracy.{RESET}")


def display_parameters(params_dict: Dict[str, float], bounds: Dict):
    """Display current engine parameters."""
    clear_screen()
    print(header_box("Engine Parameters"))
    print()

    for key, value in params_dict.items():
        lo, hi = bounds.get(key, (0, 1))
        # Normalize to 0-1 for bar display
        norm = (value - lo) / (hi - lo) if hi > lo else 0.5
        bar = progress_bar(norm, width=20)
        print(f"  {CYAN}{key:28s}{RESET} {bar} {BRIGHT_WHITE}{value:.4f}{RESET} "
              f"{DIM}[{lo:.3f} - {hi:.3f}]{RESET}")

    print()


def display_optimizer_progress(gen: int, total: int, best: float, avg: float):
    """Display optimizer progress inline."""
    bar = progress_bar(gen / total, width=30, color=CYAN)
    print(f"\r  Gen {gen:3d}/{total} {bar} "
          f"Best: {GREEN}{best:.4f}{RESET} Avg: {YELLOW}{avg:.4f}{RESET}",
          end="", flush=True)
    if gen == total:
        print()


def wait_for_key(prompt: str = "Press Enter to continue..."):
    """Wait for user to press Enter."""
    input(f"\n  {DIM}{prompt}{RESET}")
