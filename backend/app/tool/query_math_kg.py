"""T6: QueryMathKG — Query the math modeling knowledge graph.

Provides a curated knowledge base of common mathematical modeling
algorithms, techniques, and their applicability.

PRD §2.7: Input: `topic: str` → Output: `{algorithms, pros_cons, examples}`
"""

from __future__ import annotations

import json

from loguru import logger

# Built-in knowledge base (expandable)
_KNOWLEDGE_BASE = {
    "linear_programming": {
        "algorithms": ["Simplex Method", "Interior Point Method", "Branch and Bound"],
        "applicable_types": ["optimization", "resource allocation", "scheduling"],
        "pros": ["Global optimum guaranteed", "Fast for large-scale problems", "Well-studied"],
        "cons": ["Only linear relationships", "No integer constraints (LP)"],
        "tools": ["scipy.optimize.linprog", "PuLP", "Gurobi", "CPLEX"],
        "examples": ["Diet problem", "Transportation problem", "Production planning"],
    },
    "nonlinear_optimization": {
        "algorithms": ["Gradient Descent", "Newton's Method", "Genetic Algorithm", "Simulated Annealing"],
        "applicable_types": ["optimization", "curve fitting"],
        "pros": ["Handle nonlinear relationships", "Flexible objective functions"],
        "cons": ["May converge to local optima", "Computationally expensive"],
        "tools": ["scipy.optimize.minimize", "DEAP", "PyGAD"],
        "examples": ["Portfolio optimization", "Parameter estimation"],
    },
    "time_series": {
        "algorithms": ["ARIMA", "SARIMA", "Prophet", "LSTM", "Exponential Smoothing"],
        "applicable_types": ["prediction", "forecasting"],
        "pros": ["Capture temporal patterns", "Well-established methods"],
        "cons": ["Require sufficient historical data", "Sensitive to outliers"],
        "tools": ["statsmodels", "prophet", "pytorch", "sklearn"],
        "examples": ["Stock prediction", "Weather forecasting", "Demand prediction"],
    },
    "graph_theory": {
        "algorithms": ["Dijkstra", "Floyd-Warshall", "MST (Kruskal/Prim)", "Max Flow", "PageRank"],
        "applicable_types": ["network analysis", "routing", "optimization"],
        "pros": ["Natural for network problems", "Efficient algorithms"],
        "cons": ["Graph construction can be complex", "Scalability issues"],
        "tools": ["networkx", "igraph", "graph-tool"],
        "examples": ["Shortest path", "Network flow", "Community detection"],
    },
    "machine_learning": {
        "algorithms": ["Random Forest", "SVM", "XGBoost", "Neural Networks", "K-Means"],
        "applicable_types": ["prediction", "classification", "clustering"],
        "pros": ["Handle complex patterns", "Feature learning"],
        "cons": ["Need training data", "Black box models", "Overfitting risk"],
        "tools": ["scikit-learn", "xgboost", "pytorch", "tensorflow"],
        "examples": ["Credit scoring", "Image classification", "Customer segmentation"],
    },
    "differential_equations": {
        "algorithms": ["Euler Method", "Runge-Kutta", "Finite Element", "Finite Difference"],
        "applicable_types": ["simulation", "dynamic systems"],
        "pros": ["Model continuous processes", "Physics-based"],
        "cons": ["Stiff systems need special treatment", "Boundary conditions"],
        "tools": ["scipy.integrate", "FEniCS", "COMSOL"],
        "examples": ["Epidemic modeling (SIR)", "Heat transfer", "Population dynamics"],
    },
    "multi_criteria_decision": {
        "algorithms": ["AHP", "TOPSIS", "ELECTRE", "PROMETHEE", "Grey Relational Analysis"],
        "applicable_types": ["evaluation", "ranking", "decision making"],
        "pros": ["Handle multiple objectives", "Systematic comparison"],
        "cons": ["Subjective weight assignment", "Rank reversal possible"],
        "tools": ["pyahp", "scikit-criteria", "custom implementation"],
        "examples": ["Site selection", "Supplier evaluation", "Risk assessment"],
    },
    "monte_carlo": {
        "algorithms": ["Monte Carlo Simulation", "MCMC", "Importance Sampling", "Bootstrap"],
        "applicable_types": ["simulation", "uncertainty analysis", "prediction"],
        "pros": ["Handle uncertainty", "No closed-form solution needed"],
        "cons": ["Computationally expensive", "Convergence speed"],
        "tools": ["numpy.random", "scipy.stats", "pymc3"],
        "examples": ["Risk analysis", "Option pricing", "Reliability estimation"],
    },
}


def query_math_kg(topic: str) -> str:
    """Query the math modeling knowledge graph for algorithms and techniques.

    Given a topic or problem type, returns relevant algorithms,
    their pros and cons, applicable tools, and example problems.
    This helps in selecting the appropriate modeling approach.

    Args:
        topic: The math modeling topic to query (e.g., "optimization",
               "time_series", "graph_theory", "machine_learning").

    Returns:
        A JSON object with algorithms, pros/cons, tools, and examples.
    """
    logger.info(f"📚 Querying MathKG: '{topic}'")

    topic_lower = topic.lower().replace(" ", "_").replace("-", "_")

    # Direct match
    if topic_lower in _KNOWLEDGE_BASE:
        return json.dumps(
            {topic_lower: _KNOWLEDGE_BASE[topic_lower]},
            ensure_ascii=False,
            indent=2,
        )

    # Fuzzy match: search in keywords
    matches = {}
    for key, info in _KNOWLEDGE_BASE.items():
        searchable = (
            key + " "
            + " ".join(info["algorithms"])
            + " "
            + " ".join(info["applicable_types"])
        ).lower()

        if topic_lower in searchable or any(
            word in searchable for word in topic_lower.split("_")
        ):
            matches[key] = info

    if matches:
        return json.dumps(matches, ensure_ascii=False, indent=2)

    # No match — return all topics
    all_topics = list(_KNOWLEDGE_BASE.keys())
    return json.dumps(
        {
            "message": f"No exact match for '{topic}'",
            "available_topics": all_topics,
            "suggestion": "Try one of the available topics or describe your problem type.",
        },
        ensure_ascii=False,
        indent=2,
    )
