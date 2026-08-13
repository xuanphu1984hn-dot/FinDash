import numpy as np
import streamlit as st
import plotly.graph_objects as go

from data.data_utils import get_stock_history
from analysis.monte_carlo import monte_carlo_single_stock, compute_var


def render(ticker: str):
    st.title("Monte Carlo Simulation")

    if ticker == "-":
        return
    st.write(f"**{ticker}**")

    c1, c2 = st.columns(2)
    with c1:
        simulations = st.selectbox("Number of Simulations (n)", [200, 500, 1000, 2000])
    with c2:
        time_horizon = st.selectbox("Time Horizon (t, days)", [30, 60, 90])

    hist = get_stock_history(ticker, period="3mo")
    if hist.empty:
        st.warning("Không lấy được dữ liệu giá gần đây.")
        return

    close_price = hist["Close"]
    current_price = close_price.iloc[-1]

    sim = monte_carlo_single_stock(close_price, time_horizon, simulations)

    fig = go.Figure()
    for col in sim.columns:
        fig.add_trace(go.Scatter(y=sim[col], mode="lines", line=dict(width=0.6), showlegend=False,
                                  opacity=0.5))
    fig.add_hline(y=current_price, line_color="red",
                  annotation_text=f"Giá hiện tại: {current_price:.2f}")
    fig.update_layout(title=f"Monte Carlo simulation for {ticker} stock price in next {time_horizon} days",
                       xaxis_title="Day", yaxis_title="Price", height=550)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Value at Risk (VaR)")
    ending_prices = sim.iloc[-1].values
    var, price_5th = compute_var(ending_prices, current_price, confidence=0.95)

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=ending_prices, nbinsx=50, name="Ending Price"))
    fig_hist.add_vline(x=price_5th, line_dash="dash", line_color="red",
                        annotation_text=f"5th percentile: {price_5th:.2f}")
    fig_hist.update_layout(title="Distribution of the Ending Price",
                            xaxis_title="Price", yaxis_title="Frequency", height=450)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.write(f"**VaR tại độ tin cậy 95%: {var:.2f} USD**")

    # lưu context cho chatbot
    st.session_state["montecarlo_context"] = {
        "ticker": ticker, "time_horizon": time_horizon, "simulations": simulations,
        "current_price": float(current_price), "var_95": float(var),
    }
