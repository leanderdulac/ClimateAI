import logging
import time

import numpy as np

from services.bayesian_bootstrap_service import bayesian_bootstrap_service
from services.extreme_value_service import extreme_value_service
from services.spatial_statistics_service import spatial_statistics_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def benchmark_spatial():
    logger.info("--- Benchmarking Spatial Statistics ---")
    # Generate random coordinates
    n_points = 2000
    coords = np.random.uniform(-90, 90, size=(n_points, 2))
    coords = [tuple(c) for c in coords]
    values = np.random.random(n_points).tolist()

    start_time = time.time()
    # This calls the optimized _haversine_distances internally
    spatial_statistics_service.calculate_spatial_correlation(
        coords, values, max_distance=1000
    )
    end_time = time.time()

    logger.info(
        f"Spatial Correlation (N={n_points}): {end_time - start_time:.4f} seconds"
    )


def benchmark_kde():
    logger.info("--- Benchmarking KDE ---")
    n_points = 5000
    coords = np.random.uniform(-90, 90, size=(n_points, 2))
    coords = [tuple(c) for c in coords]
    values = np.random.random(n_points).tolist()

    start_time = time.time()
    spatial_statistics_service.calculate_kernel_density_estimation(coords, values)
    end_time = time.time()
    logger.info(f"KDE (N={n_points}): {end_time - start_time:.4f} seconds")


def benchmark_bootstrap():
    logger.info("--- Benchmarking Bayesian Bootstrap ---")
    n_scenarios = 100000
    data = np.random.lognormal(0, 1, 100).tolist()
    base_premium = 1000.0
    exposure = 100000.0

    start_time = time.time()
    bayesian_bootstrap_service.bayesian_bootstrap_premium(
        data, base_premium, exposure, n_scenarios=n_scenarios
    )
    end_time = time.time()

    logger.info(
        f"Monte Carlo Simulation (N={n_scenarios}): {end_time - start_time:.4f} seconds"
    )


def verify_extreme_value():
    logger.info("--- Verifying Extreme Value CI ---")
    # Generate GEV data
    from scipy.stats import genextreme

    data = genextreme.rvs(c=-0.1, loc=100, scale=20, size=100).tolist()

    try:
        result = extreme_value_service.fit_gev_distribution(data)
        logger.info(f"GEV Fit Success. CI: {result.confidence_interval}")
        logger.info(
            f"Params: loc={result.location:.2f}, scale={result.scale:.2f}, shape={result.shape:.2f}"
        )
    except Exception as e:
        logger.error(f"GEV Fit Failed: {e}")


if __name__ == "__main__":
    benchmark_spatial()
    benchmark_kde()
    benchmark_bootstrap()
    verify_extreme_value()
