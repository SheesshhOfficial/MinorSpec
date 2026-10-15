"""
Multi-Objective Evolutionary Optimization Engine: NSGA-II Core.
Simultaneously optimizes Sharpe Ratio (maximize) and Maximum Drawdown (minimize).
"""
from typing import List, Tuple, Dict, Optional
import numpy as np
import random
from src.config import (
    GENE_BOUNDS,
    POPULATION_SIZE,
    NUM_GENERATIONS,
    CROSSOVER_PROB,
    MUTATION_PROB,
    ETA_CROSSOVER,
    ETA_MUTATION,
)
from src.backtest_engine import run_vectorized_simulation_fast


class Individual:
    """
    Candidate trading strategy chromosome with multi-objective fitness evaluation.
    """
    def __init__(self, genes: np.ndarray):
        self.genes = np.array(genes, dtype=np.float64)
        # Objectives: [Sharpe (maximize), -MaxDrawdown (maximize, so smaller DD is better)]
        self.fitness: Tuple[float, float] = (-999.0, -999.0)
        self.metrics: Dict[str, float] = {}
        self.rank: int = 0
        self.crowding_distance: float = 0.0

    @classmethod
    def create_random(cls, bounds: List[Tuple[float, float]] = GENE_BOUNDS) -> "Individual":
        genes = [random.uniform(low, high) for (low, high) in bounds]
        return cls(np.array(genes, dtype=np.float64))


def dominates(ind_a: Individual, ind_b: Individual) -> bool:
    """
    Pareto dominance check: A dominates B if A is at least as good in all objectives
    and strictly better in at least one objective.
    Both objectives in self.fitness are to be maximized.
    """
    better_or_equal = (ind_a.fitness[0] >= ind_b.fitness[0]) and (ind_a.fitness[1] >= ind_b.fitness[1])
    strictly_better = (ind_a.fitness[0] > ind_b.fitness[0]) or (ind_a.fitness[1] > ind_b.fitness[1])
    return better_or_equal and strictly_better


def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    """
    Sorts population into Pareto fronts F_1, F_2, ... using Deb's fast non-dominated sorting.
    """
    fronts: List[List[Individual]] = [[]]
    S: Dict[int, List[int]] = {i: [] for i in range(len(population))}
    n: Dict[int, int] = {i: 0 for i in range(len(population))}

    for p_idx, p in enumerate(population):
        for q_idx, q in enumerate(population):
            if dominates(p, q):
                S[p_idx].append(q_idx)
            elif dominates(q, p):
                n[p_idx] += 1

        if n[p_idx] == 0:
            p.rank = 1
            fronts[0].append(p)

    current_rank = 1
    while len(fronts[current_rank - 1]) > 0:
        next_front: List[Individual] = []
        for p in fronts[current_rank - 1]:
            p_idx = population.index(p)
            for q_idx in S[p_idx]:
                n[q_idx] -= 1
                if n[q_idx] == 0:
                    q = population[q_idx]
                    q.rank = current_rank + 1
                    next_front.append(q)
        current_rank += 1
        fronts.append(next_front)

    if len(fronts[-1]) == 0:
        fronts.pop()

    return fronts


def calculate_crowding_distance(front: List[Individual]) -> None:
    """
    Assigns crowding distance to individuals in a Pareto front to preserve population diversity.
    """
    l = len(front)
    if l == 0:
        return
    for ind in front:
        ind.crowding_distance = 0.0

    num_objectives = 2
    for m in range(num_objectives):
        front.sort(key=lambda ind: ind.fitness[m])
        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")

        obj_min = front[0].fitness[m]
        obj_max = front[-1].fitness[m]
        norm = obj_max - obj_min

        if norm == 0.0:
            continue

        for i in range(1, l - 1):
            if front[i].crowding_distance != float("inf"):
                front[i].crowding_distance += (front[i + 1].fitness[m] - front[i - 1].fitness[m]) / norm


def crowded_comparison_operator(ind_a: Individual, ind_b: Individual) -> int:
    """
    Crowded tournament operator: Prefer lower rank (better front);
    if same rank, prefer larger crowding distance (less crowded region).
    Returns -1 if a is better, 1 if b is better, 0 if equal.
    """
    if ind_a.rank < ind_b.rank:
        return -1
    elif ind_a.rank > ind_b.rank:
        return 1
    else:
        if ind_a.crowding_distance > ind_b.crowding_distance:
            return -1
        elif ind_a.crowding_distance < ind_b.crowding_distance:
            return 1
        return 0


def tournament_selection(population: List[Individual], k: int = 2) -> Individual:
    """
    Binary tournament selection using crowded comparison.
    """
    candidates = random.sample(population, k)
    best = candidates[0]
    for other in candidates[1:]:
        if crowded_comparison_operator(other, best) == -1:
            best = other
    return best


def simulated_binary_crossover(
    parent1: Individual,
    parent2: Individual,
    bounds: List[Tuple[float, float]] = GENE_BOUNDS,
    eta_c: float = ETA_CROSSOVER,
) -> Tuple[Individual, Individual]:
    """
    Simulated Binary Crossover (SBX) for real-valued chromosomes.
    """
    g1 = parent1.genes.copy()
    g2 = parent2.genes.copy()

    if random.random() < CROSSOVER_PROB:
        for i in range(len(bounds)):
            if random.random() <= 0.5:
                y1 = min(g1[i], g2[i])
                y2 = max(g1[i], g2[i])
                low, high = bounds[i]

                if abs(y2 - y1) > 1e-10:
                    rand = random.random()
                    beta = 1.0 + (2.0 * (y1 - low) / (y2 - y1))
                    alpha = 2.0 - beta ** (-(eta_c + 1.0))
                    if rand <= (1.0 / alpha):
                        beta_q = (rand * alpha) ** (1.0 / (eta_c + 1.0))
                    else:
                        beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta_c + 1.0))
                    c1 = 0.5 * ((y1 + y2) - beta_q * (y2 - y1))

                    beta = 1.0 + (2.0 * (high - y2) / (y2 - y1))
                    alpha = 2.0 - beta ** (-(eta_c + 1.0))
                    if rand <= (1.0 / alpha):
                        beta_q = (rand * alpha) ** (1.0 / (eta_c + 1.0))
                    else:
                        beta_q = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta_c + 1.0))
                    c2 = 0.5 * ((y1 + y2) + beta_q * (y2 - y1))

                    g1[i] = np.clip(c1, low, high)
                    g2[i] = np.clip(c2, low, high)

    return Individual(g1), Individual(g2)


def polynomial_mutation(
    ind: Individual,
    bounds: List[Tuple[float, float]] = GENE_BOUNDS,
    eta_m: float = ETA_MUTATION,
) -> Individual:
    """
    Polynomial mutation for real-coded evolutionary parameters.
    """
    genes = ind.genes.copy()
    for i in range(len(bounds)):
        if random.random() < (1.0 / len(bounds)):
            y = genes[i]
            low, high = bounds[i]
            delta1 = (y - low) / (high - low + 1e-10)
            delta2 = (high - y) / (high - low + 1e-10)
            rand = random.random()
            mut_pow = 1.0 / (eta_m + 1.0)

            if rand <= 0.5:
                xy = 1.0 - delta1
                val = 2.0 * rand + (1.0 - 2.0 * rand) * (xy ** (eta_m + 1.0))
                delta_q = val ** mut_pow - 1.0
            else:
                xy = 1.0 - delta2
                val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (xy ** (eta_m + 1.0))
                delta_q = 1.0 - val ** mut_pow

            y = y + delta_q * (high - low)
            genes[i] = np.clip(y, low, high)

    return Individual(genes)


class NSGA2Optimizer:
    """
    NSGA-II Controller for Multi-Objective Evolutionary Strategy Discovery.
    """
    def __init__(
        self,
        open_prices: np.ndarray,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        p_up: np.ndarray,
        atr: np.ndarray,
        regime_vol: np.ndarray,
        pop_size: int = POPULATION_SIZE,
        num_generations: int = NUM_GENERATIONS,
        bounds: List[Tuple[float, float]] = GENE_BOUNDS,
        seed: Optional[int] = None,
        volume: Optional[np.ndarray] = None,
        prefix_p_up: float = -1.0,
        prefix_atr: float = -1.0,
        prefix_regime_vol: int = -1,
    ):
        self.open_prices = open_prices
        self.close = close
        self.high = high
        self.low = low
        self.p_up = p_up
        self.atr = atr
        self.regime_vol = regime_vol
        self.pop_size = pop_size
        self.num_generations = num_generations
        self.bounds = bounds
        self.seed = seed
        self.volume = volume
        self.prefix_p_up = prefix_p_up
        self.prefix_atr = prefix_atr
        self.prefix_regime_vol = prefix_regime_vol
        self.population: List[Individual] = []
        self.generation_history: List[Dict] = []

    def evaluate_individual(self, ind: Individual) -> None:
        """
        Evaluates individual using the Numba fast simulator with penalty for GA selection.
        Objective 1: Maximize Sharpe Ratio
        Objective 2: Minimize Max Drawdown (represented as -MaxDD to maximize)
        """
        sharpe, max_dd, total_ret, trades, turnover = run_vectorized_simulation_fast(
            self.open_prices, self.close, self.high, self.low, self.p_up, self.atr, self.regime_vol,
            ind.genes, apply_penalty=True, volume=self.volume,
            prefix_p_up=self.prefix_p_up, prefix_atr=self.prefix_atr, prefix_regime_vol=self.prefix_regime_vol,
        )
        # Objectives are to be maximized:
        # obj0 = Sharpe Ratio (penalized for GA fitness)
        # obj1 = -MaxDrawdown (penalized for GA fitness)
        ind.fitness = (float(sharpe), float(-max_dd))
        ind.metrics = {
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_dd),
            "total_return": float(total_ret),
            "trades": int(trades),
            "turnover": float(turnover),
        }

    def run(self, progress_callback=None) -> List[Individual]:
        """
        Executes full NSGA-II evolutionary loop.
        Returns the non-dominated Pareto Front (Rank 1 individuals).
        """
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        # Step 1: Initialize random population
        self.population = [Individual.create_random(self.bounds) for _ in range(self.pop_size)]
        for ind in self.population:
            self.evaluate_individual(ind)

        # Initial ranking
        fronts = fast_non_dominated_sort(self.population)
        for front in fronts:
            calculate_crowding_distance(front)

        # Step 2: Generational loop
        for gen in range(1, self.num_generations + 1):
            # Create offspring population Q_t of size N
            offspring: List[Individual] = []
            while len(offspring) < self.pop_size:
                p1 = tournament_selection(self.population)
                p2 = tournament_selection(self.population)
                c1, c2 = simulated_binary_crossover(p1, p2, self.bounds)
                c1 = polynomial_mutation(c1, self.bounds)
                c2 = polynomial_mutation(c2, self.bounds)
                self.evaluate_individual(c1)
                self.evaluate_individual(c2)
                offspring.extend([c1, c2])

            # Trim to pop_size
            offspring = offspring[:self.pop_size]

            # Combine Parent + Offspring: R_t = P_t U Q_t (size 2N)
            combined = self.population + offspring
            fronts = fast_non_dominated_sort(combined)

            new_population: List[Individual] = []
            front_idx = 0

            # Fill new population until pop_size
            while front_idx < len(fronts) and (len(new_population) + len(fronts[front_idx])) <= self.pop_size:
                calculate_crowding_distance(fronts[front_idx])
                new_population.extend(fronts[front_idx])
                front_idx += 1

            # If new_population not full, fill remaining slots from current front sorted by crowding distance
            if len(new_population) < self.pop_size and front_idx < len(fronts):
                last_front = fronts[front_idx]
                calculate_crowding_distance(last_front)
                last_front.sort(key=lambda ind: ind.crowding_distance, reverse=True)
                needed = self.pop_size - len(new_population)
                new_population.extend(last_front[:needed])

            self.population = new_population

            # Log generation metrics
            pareto_front = [ind for ind in self.population if ind.rank == 1]
            best_sharpe = max(ind.metrics["sharpe_ratio"] for ind in pareto_front)
            min_dd = min(ind.metrics["max_drawdown"] for ind in pareto_front)

            gen_stat = {
                "generation": gen,
                "pareto_size": len(pareto_front),
                "best_sharpe": best_sharpe,
                "min_drawdown": min_dd,
            }
            self.generation_history.append(gen_stat)

            if progress_callback:
                progress_callback(gen, self.num_generations, gen_stat)
            elif gen % 5 == 0 or gen == self.num_generations:
                print(f"[NSGA-II] Gen {gen:02d}/{self.num_generations} | Pareto Front Size: {len(pareto_front):02d} | Max Sharpe: {best_sharpe:.2f} | Min Drawdown: {min_dd*100:.2f}%")

        # Return final Pareto Front
        final_fronts = fast_non_dominated_sort(self.population)
        calculate_crowding_distance(final_fronts[0])
        return final_fronts[0]


if __name__ == "__main__":
    from src.data_loader import fetch_and_cache_ticker
    from src.feature_pipeline import prepare_feature_dataset
    from src.predictor import MarketPredictor

    df = fetch_and_cache_ticker("SPY")
    proc_df, feats = prepare_feature_dataset(df, "SPY", save_processed=False)
    predictor = MarketPredictor("SPY", feats)
    predictor.train(proc_df)
    p_up = predictor.predict_proba(proc_df)

    close = proc_df["Close"].to_numpy(dtype=np.float64)
    high = proc_df["High"].to_numpy(dtype=np.float64)
    low = proc_df["Low"].to_numpy(dtype=np.float64)
    atr = proc_df["atr_14"].to_numpy(dtype=np.float64)
    reg_vol = proc_df["regime_high_vol"].to_numpy(dtype=np.int32)

    optimizer = NSGA2Optimizer(close, high, low, p_up, atr, reg_vol, pop_size=40, num_generations=15)
    pareto_solutions = optimizer.run()

    print(f"\nEvolution complete! Discovered {len(pareto_solutions)} non-dominated Pareto solutions:")
    for i, sol in enumerate(pareto_solutions[:5]):
        print(f" Solution {i+1}: Sharpe={sol.metrics['sharpe_ratio']:.2f}, MaxDD={sol.metrics['max_drawdown']*100:.2f}%, Return={sol.metrics['total_return']*100:.2f}%, Trades={sol.metrics['trades']}")
