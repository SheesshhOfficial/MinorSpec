"""
Unit Tests for NSGA-II Multi-Objective Evolutionary Engine.
"""
import numpy as np
from src.evolutionary_core import (
    Individual,
    dominates,
    fast_non_dominated_sort,
    simulated_binary_crossover,
    polynomial_mutation,
)
from src.config import GENE_BOUNDS


def test_pareto_dominance():
    # Individual A: Sharpe 2.0, Drawdown 0.10 (fitness: 2.0, -0.10)
    ind_a = Individual(np.ones(7))
    ind_a.fitness = (2.0, -0.10)

    # Individual B: Sharpe 1.5, Drawdown 0.20 (fitness: 1.5, -0.20)
    ind_b = Individual(np.ones(7))
    ind_b.fitness = (1.5, -0.20)

    # Individual C: Sharpe 2.5, Drawdown 0.25 (fitness: 2.5, -0.25) -> Non-dominated with A!
    ind_c = Individual(np.ones(7))
    ind_c.fitness = (2.5, -0.25)

    assert dominates(ind_a, ind_b), "A should dominate B"
    assert not dominates(ind_b, ind_a), "B should not dominate A"
    assert not dominates(ind_a, ind_c), "A should not dominate C"
    assert not dominates(ind_c, ind_a), "C should not dominate A"


def test_fast_non_dominated_sort():
    ind1 = Individual(np.ones(7))
    ind1.fitness = (3.0, -0.05)  # Best: Rank 1

    ind2 = Individual(np.ones(7))
    ind2.fitness = (2.0, -0.10)  # Dominated by ind1: Rank 2

    ind3 = Individual(np.ones(7))
    ind3.fitness = (1.0, -0.20)  # Dominated by ind2: Rank 3

    population = [ind1, ind2, ind3]
    fronts = fast_non_dominated_sort(population)

    assert len(fronts) == 3
    assert fronts[0][0] == ind1
    assert fronts[1][0] == ind2
    assert fronts[2][0] == ind3


def test_genetic_operators_preserve_bounds():
    p1 = Individual.create_random(GENE_BOUNDS)
    p2 = Individual.create_random(GENE_BOUNDS)

    c1, c2 = simulated_binary_crossover(p1, p2, GENE_BOUNDS)
    m1 = polynomial_mutation(c1, GENE_BOUNDS)

    for i, (low, high) in enumerate(GENE_BOUNDS):
        assert low <= m1.genes[i] <= high, f"Gene {i} ({m1.genes[i]}) exceeded bounds [{low}, {high}]"


if __name__ == "__main__":
    test_pareto_dominance()
    test_fast_non_dominated_sort()
    test_genetic_operators_preserve_bounds()
    print("All evolutionary engine tests passed successfully!")
