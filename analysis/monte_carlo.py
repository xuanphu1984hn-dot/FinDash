"""
monte_carlo.py
---------------
Monte Carlo Simulation cho 1 cổ phiếu (giữ logic gốc từ findash_app.py)
và mở rộng cho cả danh mục đầu tư (multi-asset, có tương quan giữa các mã).
"""

import numpy as np
import pandas as pd


def monte_carlo_single_stock(close_prices: pd.Series, time_horizon: int,
                              simulations: int, seed: int | None = None) -> pd.DataFrame:
    """
    Mô phỏng giá cổ phiếu tương lai bằng random walk dựa trên daily volatility lịch sử.
    Giữ nguyên logic gốc của findash_app.py (tab6), chỉ tối ưu vòng lặp bằng numpy.
    """
    rng = np.random.default_rng(seed)

    daily_return = close_prices.pct_change().dropna()
    daily_volatility = daily_return.std()
    last_price = close_prices.iloc[-1]

    # shape: (time_horizon, simulations)
    random_returns = rng.normal(0, daily_volatility, size=(time_horizon, simulations))

    price_paths = np.zeros((time_horizon, simulations))
    price_paths[0] = last_price * (1 + random_returns[0])
    for t in range(1, time_horizon):
        price_paths[t] = price_paths[t - 1] * (1 + random_returns[t])

    return pd.DataFrame(price_paths)


def compute_var(ending_prices: np.ndarray, current_price: float, confidence: float = 0.95):
    """Tính Value at Risk (VaR) ở mức tin cậy cho trước."""
    percentile = (1 - confidence) * 100
    future_price_ci = np.percentile(ending_prices, percentile)
    var = current_price - future_price_ci
    return var, future_price_ci


def monte_carlo_portfolio(prices: pd.DataFrame, weights: np.ndarray,
                           time_horizon: int, simulations: int,
                           initial_value: float = 10000, seed: int | None = None):
    """
    Monte Carlo cho cả danh mục, có tính đến tương quan giữa các mã
    bằng phân rã Cholesky trên ma trận hiệp phương sai.

    prices: DataFrame giá đóng cửa, mỗi cột 1 mã
    weights: mảng trọng số tương ứng từng cột (tổng = 1)
    Trả về mảng shape (time_horizon, simulations) = giá trị danh mục mỗi ngày mô phỏng.
    """
    rng = np.random.default_rng(seed)

    returns = prices.pct_change().dropna()
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values
    n_assets = len(mean_returns)

    L = np.linalg.cholesky(cov_matrix)

    portfolio_values = np.zeros((time_horizon, simulations))

    for s in range(simulations):
        asset_prices = np.ones(n_assets)  # bắt đầu từ base = 1 (tính theo % thay đổi)
        values = []
        for t in range(time_horizon):
            z = rng.normal(size=n_assets)
            correlated_shock = mean_returns + L @ z
            asset_prices *= (1 + correlated_shock)
            port_value = initial_value * np.sum(weights * asset_prices)
            values.append(port_value)
        portfolio_values[:, s] = values

    return portfolio_values
