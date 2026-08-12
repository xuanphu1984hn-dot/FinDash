"""
capm.py
--------
Các hàm phân tích danh mục đầu tư: CAPM, APT đơn giản (multi-factor regression),
và các chỉ số danh mục cơ bản (return, volatility, Sharpe ratio, Efficient Frontier).
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Tính daily return (%) từ DataFrame giá đóng cửa."""
    return prices.pct_change().dropna()


def capm_single_stock(stock_returns: pd.Series, market_returns: pd.Series,
                       risk_free_rate: float, freq: int = 252):
    """
    Hồi quy CAPM: R_stock - Rf = alpha + beta * (R_market - Rf)
    Trả về dict gồm beta, alpha, expected_return (annualized).
    """
    df = pd.concat([stock_returns, market_returns], axis=1).dropna()
    df.columns = ["stock", "market"]

    rf_daily = risk_free_rate / freq
    y = df["stock"] - rf_daily
    x = df["market"] - rf_daily
    x = sm.add_constant(x)

    model = sm.OLS(y, x).fit()
    alpha, beta = model.params.iloc[0], model.params.iloc[1]

    market_mean_return_annual = df["market"].mean() * freq
    expected_return = risk_free_rate + beta * (market_mean_return_annual - risk_free_rate)

    return {
        "beta": beta,
        "alpha_daily": alpha,
        "alpha_annual": alpha * freq,
        "expected_return": expected_return,
        "r_squared": model.rsquared,
    }


def capm_portfolio(tickers_returns: pd.DataFrame, market_returns: pd.Series,
                    risk_free_rate: float, freq: int = 252) -> pd.DataFrame:
    """Chạy CAPM cho từng mã trong danh mục, trả về bảng tổng hợp."""
    rows = []
    for col in tickers_returns.columns:
        res = capm_single_stock(tickers_returns[col], market_returns, risk_free_rate, freq)
        res["ticker"] = col
        rows.append(res)
    df = pd.DataFrame(rows).set_index("ticker")
    return df[["beta", "alpha_annual", "expected_return", "r_squared"]]


def apt_multi_factor(stock_returns: pd.Series, factor_returns: pd.DataFrame):
    """
    Hồi quy APT đa nhân tố: R_stock = a + b1*F1 + b2*F2 + ... + e
    factor_returns: DataFrame mỗi cột là 1 factor (vd: market, oil, rates...)
    Trả về hệ số hồi quy của từng factor + R-squared.
    """
    df = pd.concat([stock_returns, factor_returns], axis=1).dropna()
    y = df.iloc[:, 0]
    x = sm.add_constant(df.iloc[:, 1:])

    model = sm.OLS(y, x).fit()
    return {
        "params": model.params,
        "pvalues": model.pvalues,
        "r_squared": model.rsquared,
    }


def portfolio_performance(weights: np.ndarray, mean_returns: pd.Series,
                           cov_matrix: pd.DataFrame, freq: int = 252):
    """Trả về (expected_return, volatility) hàng năm cho 1 bộ trọng số."""
    port_return = np.sum(mean_returns * weights) * freq
    port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * freq, weights)))
    return port_return, port_vol


def random_portfolios(mean_returns, cov_matrix, num_portfolios=5000,
                       risk_free_rate=0.04, freq=252, seed=42):
    """
    Sinh ngẫu nhiên nhiều bộ trọng số danh mục để dựng Efficient Frontier.
    Trả về DataFrame: return, volatility, sharpe, weights...
    """
    rng = np.random.default_rng(seed)
    n_assets = len(mean_returns)
    results = []

    for _ in range(num_portfolios):
        weights = rng.random(n_assets)
        weights /= np.sum(weights)

        ret, vol = portfolio_performance(weights, mean_returns, cov_matrix, freq)
        sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0

        results.append({
            "return": ret,
            "volatility": vol,
            "sharpe": sharpe,
            "weights": weights,
        })

    return pd.DataFrame(results)
