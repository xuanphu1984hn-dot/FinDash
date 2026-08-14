import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from data.data_utils import get_multi_close_prices, get_risk_free_rate
from analysis.capm import compute_returns, capm_portfolio, random_portfolios, apt_multi_factor
from analysis.monte_carlo import monte_carlo_portfolio, compute_var

FACTOR_OPTIONS = {
    "Thị trường (S&P 500 - ^GSPC)": "^GSPC",
    "Lãi suất trái phiếu 10 năm (^TNX)": "^TNX",
    "Giá dầu (CL=F)": "CL=F",
    "Giá vàng (GC=F)": "GC=F",
    "Chỉ số USD (DX-Y.NYB)": "DX-Y.NYB",
}


def render(default_tickers=("AAPL", "MSFT", "AMZN")):
    st.title("Phân tích Danh mục Đầu tư")

    selected = st.multiselect(
        "Chọn các mã trong danh mục",
        options=["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT",
                 "IBM", "KO", "PEP", "XOM", "DIS"],
        default=list(default_tickers),
    )
    market_ticker = st.text_input("Chỉ số thị trường tham chiếu (benchmark)", value="^GSPC")

    if len(selected) < 2:
        st.info("Chọn ít nhất 2 mã để phân tích danh mục.")
        return

    period = st.selectbox("Khoảng dữ liệu lịch sử", ["1y", "2y", "3y", "5y"], index=2)

    with st.spinner("Đang tải dữ liệu giá..."):
        prices = get_multi_close_prices(selected, period=period)
        market_prices = get_multi_close_prices([market_ticker], period=period)
        rf = get_risk_free_rate()

    if prices.empty:
        st.error("Không lấy được dữ liệu giá cho các mã đã chọn.")
        return

    returns = compute_returns(prices)
    market_returns = compute_returns(market_prices).iloc[:, 0]

    st.caption(f"Lãi suất phi rủi ro (risk-free rate) ước tính hiện tại: **{rf:.2%}**/năm")

    # ------------------------------------------------------------------
    # CAPM
    # ------------------------------------------------------------------
    st.header("1. CAPM (Capital Asset Pricing Model)")
    capm_table = capm_portfolio(returns, market_returns, rf)
    st.dataframe(
        capm_table.style.format({
            "beta": "{:.2f}", "alpha_annual": "{:.2%}",
            "expected_return": "{:.2%}", "r_squared": "{:.2f}",
        }),
        use_container_width=True,
    )

    # Security Market Line (SML)
    market_mean_return = market_returns.mean() * 252
    beta_range = np.linspace(0, capm_table["beta"].max() * 1.2, 50)
    sml_returns = rf + beta_range * (market_mean_return - rf)

    fig_sml = go.Figure()
    fig_sml.add_trace(go.Scatter(x=beta_range, y=sml_returns, mode="lines", name="Security Market Line"))
    fig_sml.add_trace(go.Scatter(
        x=capm_table["beta"], y=capm_table["expected_return"],
        mode="markers+text", text=capm_table.index, textposition="top center",
        name="Cổ phiếu trong danh mục",
    ))
    fig_sml.update_layout(xaxis_title="Beta", yaxis_title="Expected Return (annual)", height=450)
    st.plotly_chart(fig_sml, use_container_width=True)

    # ------------------------------------------------------------------
    # Ma trận tương quan / hiệp phương sai
    # ------------------------------------------------------------------
    st.header("2. Ma trận Tương quan giữa các mã")
    corr = returns.corr()
    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    st.plotly_chart(fig_corr, use_container_width=True)

    # ------------------------------------------------------------------
    # Efficient Frontier (Monte Carlo random weights)
    # ------------------------------------------------------------------
    st.header("3. Efficient Frontier (Monte Carlo)")
    n_portfolios = st.slider("Số lượng danh mục mô phỏng", 500, 10000, 3000, step=500)

    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    with st.spinner("Đang mô phỏng các danh mục ngẫu nhiên..."):
        sim = random_portfolios(mean_returns, cov_matrix, num_portfolios=n_portfolios, risk_free_rate=rf)

    best_sharpe = sim.loc[sim["sharpe"].idxmax()]
    min_vol = sim.loc[sim["volatility"].idxmin()]

    fig_ef = go.Figure()
    fig_ef.add_trace(go.Scatter(
        x=sim["volatility"], y=sim["return"], mode="markers",
        marker=dict(color=sim["sharpe"], colorscale="Viridis", showscale=True, size=5,
                    colorbar=dict(title="Sharpe")),
        name="Danh mục mô phỏng",
    ))
    fig_ef.add_trace(go.Scatter(
        x=[best_sharpe["volatility"]], y=[best_sharpe["return"]],
        mode="markers", marker=dict(color="red", size=14, symbol="star"),
        name="Sharpe cao nhất",
    ))
    fig_ef.add_trace(go.Scatter(
        x=[min_vol["volatility"]], y=[min_vol["return"]],
        mode="markers", marker=dict(color="blue", size=14, symbol="star"),
        name="Rủi ro thấp nhất",
    ))
    fig_ef.update_layout(xaxis_title="Volatility (rủi ro, hàng năm)",
                          yaxis_title="Expected Return (hàng năm)", height=500)
    st.plotly_chart(fig_ef, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Danh mục Sharpe cao nhất")
        st.write(f"Return: **{best_sharpe['return']:.2%}**, Volatility: **{best_sharpe['volatility']:.2%}**, "
                 f"Sharpe: **{best_sharpe['sharpe']:.2f}**")
        st.dataframe(pd.Series(best_sharpe["weights"], index=selected, name="weight")
                     .to_frame().style.format("{:.2%}"))
    with c2:
        st.subheader("Danh mục rủi ro thấp nhất")
        st.write(f"Return: **{min_vol['return']:.2%}**, Volatility: **{min_vol['volatility']:.2%}**, "
                 f"Sharpe: **{min_vol['sharpe']:.2f}**")
        st.dataframe(pd.Series(min_vol["weights"], index=selected, name="weight")
                     .to_frame().style.format("{:.2%}"))

    # ------------------------------------------------------------------
    # Trend giá danh mục
    # ------------------------------------------------------------------
    st.header("4. Xu hướng giá (Your Portfolio's Trend)")
    normalized = prices / prices.iloc[0] * 100
    fig_trend = px.line(normalized, labels={"value": "Giá (chuẩn hoá, base=100)", "Date": "Ngày"})
    st.plotly_chart(fig_trend, use_container_width=True)

    # ------------------------------------------------------------------
    # APT (Arbitrage Pricing Theory) - hồi quy đa nhân tố
    # ------------------------------------------------------------------
    st.header("5. APT (Arbitrage Pricing Theory)")
    st.caption(
        "Mô hình đa nhân tố: giải thích lợi suất mỗi cổ phiếu bằng nhiều yếu tố vĩ mô "
        "thay vì chỉ 1 yếu tố thị trường như CAPM."
    )

    factor_labels = st.multiselect(
        "Chọn các nhân tố (factor) đưa vào mô hình",
        options=list(FACTOR_OPTIONS.keys()),
        default=["Thị trường (S&P 500 - ^GSPC)", "Lãi suất trái phiếu 10 năm (^TNX)", "Giá dầu (CL=F)"],
    )

    if len(factor_labels) < 1:
        st.info("Chọn ít nhất 1 nhân tố để chạy APT.")
    else:
        factor_tickers = [FACTOR_OPTIONS[label] for label in factor_labels]

        with st.spinner("Đang tải dữ liệu các nhân tố..."):
            factor_prices = get_multi_close_prices(factor_tickers, period=period)

        if factor_prices.empty:
            st.error("Không lấy được dữ liệu cho các nhân tố đã chọn.")
        else:
            factor_returns = compute_returns(factor_prices)
            factor_returns.columns = factor_labels  # đặt lại tên cột dễ đọc

            coef_rows = []
            r2_rows = {}
            for tkr in selected:
                try:
                    apt_result = apt_multi_factor(returns[tkr], factor_returns)
                    row = apt_result["params"].to_dict()
                    row["ticker"] = tkr
                    coef_rows.append(row)
                    r2_rows[tkr] = apt_result["r_squared"]
                except Exception as e:
                    st.warning(f"Không chạy được APT cho {tkr}: {e}")

            if coef_rows:
                apt_df = pd.DataFrame(coef_rows).set_index("ticker")
                apt_df["R-squared"] = pd.Series(r2_rows)
                rename_map = {"const": "Alpha (const)"}
                apt_df = apt_df.rename(columns=rename_map)

                st.write("**Hệ số hồi quy (độ nhạy của mỗi mã với từng nhân tố):**")
                st.dataframe(apt_df.style.format("{:.4f}"), use_container_width=True)
                st.caption(
                    "Hệ số càng lớn (trị tuyệt đối) nghĩa là cổ phiếu càng nhạy với nhân tố đó. "
                    "R-squared cho biết mô hình giải thích được bao nhiêu % biến động lợi suất."
                )

    # ------------------------------------------------------------------
    # Monte Carlo Simulation cho cả danh mục
    # ------------------------------------------------------------------
    st.header("6. Monte Carlo Simulation cho Danh mục")
    st.caption(
        "Mô phỏng giá trị danh mục trong tương lai, có tính đến tương quan giữa các mã "
        "(khác với Monte Carlo ở tab riêng, chỉ mô phỏng cho 1 mã)."
    )

    weight_scheme = st.selectbox(
        "Chọn cách phân bổ trọng số danh mục",
        ["Trọng số bằng nhau (Equal Weight)", "Sharpe cao nhất (từ Efficient Frontier)",
         "Rủi ro thấp nhất (từ Efficient Frontier)"],
    )

    if weight_scheme == "Trọng số bằng nhau (Equal Weight)":
        mc_weights = np.repeat(1 / len(selected), len(selected))
    elif weight_scheme == "Sharpe cao nhất (từ Efficient Frontier)":
        mc_weights = best_sharpe["weights"]
    else:
        mc_weights = min_vol["weights"]

    st.write("Trọng số sử dụng:")
    st.dataframe(pd.Series(mc_weights, index=selected, name="weight").to_frame().style.format("{:.2%}"))

    c1, c2, c3 = st.columns(3)
    with c1:
        mc_simulations = st.selectbox("Số lần mô phỏng (n)", [200, 500, 1000], key="mc_port_sim")
    with c2:
        mc_horizon = st.selectbox("Số ngày mô phỏng (t)", [30, 60, 90], key="mc_port_horizon")
    with c3:
        initial_value = st.number_input("Giá trị danh mục ban đầu (USD)", min_value=1000,
                                         value=10000, step=1000)

    with st.spinner("Đang chạy mô phỏng Monte Carlo cho danh mục..."):
        port_paths = monte_carlo_portfolio(
            prices, mc_weights, mc_horizon, mc_simulations, initial_value=initial_value
        )

    fig_mc = go.Figure()
    for i in range(port_paths.shape[1]):
        fig_mc.add_trace(go.Scatter(
            y=port_paths[:, i], mode="lines", line=dict(width=0.6), opacity=0.5, showlegend=False,
        ))
    fig_mc.add_hline(y=initial_value, line_color="red",
                      annotation_text=f"Giá trị ban đầu: {initial_value:,.0f}")
    fig_mc.update_layout(
        title=f"Monte Carlo simulation - Giá trị danh mục trong {mc_horizon} ngày tới",
        xaxis_title="Ngày", yaxis_title="Giá trị danh mục (USD)", height=550,
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    ending_values = port_paths[-1]
    var_port, value_5th = compute_var(ending_values, initial_value, confidence=0.95)

    fig_hist_port = go.Figure()
    fig_hist_port.add_trace(go.Histogram(x=ending_values, nbinsx=50))
    fig_hist_port.add_vline(x=value_5th, line_dash="dash", line_color="red",
                             annotation_text=f"5th percentile: {value_5th:,.0f}")
    fig_hist_port.update_layout(title="Phân phối giá trị danh mục ở cuối kỳ",
                                 xaxis_title="Giá trị (USD)", yaxis_title="Tần suất", height=450)
    st.plotly_chart(fig_hist_port, use_container_width=True)

    st.write(f"**VaR danh mục tại độ tin cậy 95%: {var_port:,.2f} USD** "
             f"(tức là có 5% khả năng danh mục mất hơn số tiền này trong {mc_horizon} ngày tới)")

    # lưu vào session_state để chatbot có thể dùng làm context
    st.session_state["portfolio_context"] = {
        "tickers": selected,
        "capm": capm_table.to_dict(),
        "best_sharpe_weights": dict(zip(selected, best_sharpe["weights"])),
        "best_sharpe_return": best_sharpe["return"],
        "best_sharpe_vol": best_sharpe["volatility"],
        "monte_carlo_portfolio": {
            "weight_scheme": weight_scheme,
            "initial_value": initial_value,
            "time_horizon": mc_horizon,
            "var_95": float(var_port),
        },
    }
