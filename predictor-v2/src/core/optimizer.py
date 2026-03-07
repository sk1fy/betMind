"""Genetic Algorithm optimizer for engine parameters."""

import random
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple

from .data_types import EngineParameters, HistoricalMatch
from .engine import PredictionEngine


@dataclass
class GeneticConfig:
    population_size: int = 100
    generations: int = 150
    elite_size: int = 20
    tournament_size: int = 5
    mutation_rate: float = 0.2
    mutation_std: float = 0.1
    crossover_alpha: float = 0.5  # BLX-alpha


class GeneticOptimizer:
    """Optimize engine parameters using a Genetic Algorithm."""

    def __init__(self, config: Optional[GeneticConfig] = None):
        self.config = config or GeneticConfig()
        self.param_keys = list(EngineParameters.BOUNDS.keys())
        self.bounds = [EngineParameters.BOUNDS[k] for k in self.param_keys]
        self.n_params = len(self.param_keys)
        self.population: np.ndarray = np.array([])
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []

    def _init_population(self) -> np.ndarray:
        """Initialize random population within bounds."""
        pop = np.zeros((self.config.population_size, self.n_params))
        for i in range(self.n_params):
            lo, hi = self.bounds[i]
            pop[:, i] = np.random.uniform(lo, hi, self.config.population_size)
        return pop

    def evaluate_fitness(
        self,
        individual: np.ndarray,
        historical_data: List[HistoricalMatch],
    ) -> float:
        """Evaluate fitness of an individual on historical data.

        Fitness = accuracy (correct winner predictions) + calibration bonus.
        """
        params = EngineParameters.from_array(individual.tolist(), self.param_keys)
        engine = PredictionEngine(params)

        correct = 0
        total = len(historical_data)
        prob_errors = []

        for match in historical_data:
            from .data_types import TeamData, MapStats

            t1 = TeamData(
                name=match.team1,
                ranking=match.team1_ranking,
                form_score=match.team1_form,
                odds=match.team1_odds,
                map_stats={
                    match.map_name: MapStats(
                        map_name=match.map_name,
                        wins=int(match.team1_map_winrate * 10),
                        losses=int((1 - match.team1_map_winrate) * 10),
                        pistol_wins=int(match.team1_pistol_wr * 4),
                        pistol_total=4,
                    )
                },
            )
            t2 = TeamData(
                name=match.team2,
                ranking=match.team2_ranking,
                form_score=match.team2_form,
                odds=match.team2_odds,
                map_stats={
                    match.map_name: MapStats(
                        map_name=match.map_name,
                        wins=int(match.team2_map_winrate * 10),
                        losses=int((1 - match.team2_map_winrate) * 10),
                        pistol_wins=int(match.team2_pistol_wr * 4),
                        pistol_total=4,
                    )
                },
            )

            pred = engine.predict_map(t1, t2, match.map_name, match.picked_by,
                                      num_simulations=100)

            # Check if prediction is correct
            predicted_winner = match.team1 if pred.team1_win_prob > 0.5 else match.team2
            if predicted_winner == match.actual_winner:
                correct += 1

            # Calibration: how close was the probability to the actual outcome
            actual_t1_won = 1.0 if match.actual_winner == match.team1 else 0.0
            prob_error = (pred.team1_win_prob - actual_t1_won) ** 2
            prob_errors.append(prob_error)

        accuracy = correct / total if total > 0 else 0.0
        brier_score = 1.0 - (sum(prob_errors) / total if total > 0 else 1.0)

        # Fitness: weighted combination of accuracy and calibration
        fitness = accuracy * 0.7 + brier_score * 0.3

        return fitness

    def tournament_selection(self, fitness: np.ndarray) -> int:
        """Select individual via tournament selection."""
        candidates = np.random.choice(
            len(fitness), size=self.config.tournament_size, replace=False
        )
        best_idx = candidates[np.argmax(fitness[candidates])]
        return best_idx

    def blx_alpha_crossover(
        self, parent1: np.ndarray, parent2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """BLX-alpha crossover."""
        alpha = self.config.crossover_alpha
        child1 = np.zeros(self.n_params)
        child2 = np.zeros(self.n_params)

        for i in range(self.n_params):
            lo = min(parent1[i], parent2[i])
            hi = max(parent1[i], parent2[i])
            d = hi - lo
            new_lo = lo - alpha * d
            new_hi = hi + alpha * d

            # Clamp to bounds
            new_lo = max(new_lo, self.bounds[i][0])
            new_hi = min(new_hi, self.bounds[i][1])

            child1[i] = np.random.uniform(new_lo, new_hi)
            child2[i] = np.random.uniform(new_lo, new_hi)

        return child1, child2

    def gaussian_mutation(self, individual: np.ndarray) -> np.ndarray:
        """Apply Gaussian mutation."""
        mutant = individual.copy()
        for i in range(self.n_params):
            if random.random() < self.config.mutation_rate:
                lo, hi = self.bounds[i]
                std = (hi - lo) * self.config.mutation_std
                mutant[i] += np.random.normal(0, std)
                mutant[i] = np.clip(mutant[i], lo, hi)
        return mutant

    def run(
        self,
        historical_data: List[HistoricalMatch],
        progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
    ) -> Dict:
        """Run full genetic optimization.

        Args:
            historical_data: List of historical matches for evaluation
            progress_callback: Optional callback(generation, total, best_fitness, avg_fitness)

        Returns:
            Dict with 'best_params', 'best_fitness', 'history'
        """
        self.population = self._init_population()
        self.best_fitness_history = []
        self.avg_fitness_history = []

        best_ever_fitness = -1.0
        best_ever_individual = None

        for gen in range(self.config.generations):
            # Evaluate fitness for all individuals
            fitness = np.array([
                self.evaluate_fitness(ind, historical_data)
                for ind in self.population
            ])

            best_idx = np.argmax(fitness)
            best_fitness = fitness[best_idx]
            avg_fitness = np.mean(fitness)

            self.best_fitness_history.append(best_fitness)
            self.avg_fitness_history.append(avg_fitness)

            if best_fitness > best_ever_fitness:
                best_ever_fitness = best_fitness
                best_ever_individual = self.population[best_idx].copy()

            if progress_callback:
                progress_callback(gen + 1, self.config.generations, best_fitness, avg_fitness)

            # Elitism: keep top N
            elite_indices = np.argsort(fitness)[-self.config.elite_size:]
            new_population = [self.population[i].copy() for i in elite_indices]

            # Fill the rest with offspring
            while len(new_population) < self.config.population_size:
                p1_idx = self.tournament_selection(fitness)
                p2_idx = self.tournament_selection(fitness)

                child1, child2 = self.blx_alpha_crossover(
                    self.population[p1_idx], self.population[p2_idx]
                )

                child1 = self.gaussian_mutation(child1)
                child2 = self.gaussian_mutation(child2)

                new_population.append(child1)
                if len(new_population) < self.config.population_size:
                    new_population.append(child2)

            self.population = np.array(new_population[:self.config.population_size])

        # Build result
        best_params = EngineParameters.from_array(
            best_ever_individual.tolist(), self.param_keys
        )

        return {
            "best_params": best_params,
            "best_fitness": best_ever_fitness,
            "best_fitness_history": self.best_fitness_history,
            "avg_fitness_history": self.avg_fitness_history,
        }
