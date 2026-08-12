from datetime import datetime, timedelta

import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from data.data_utils import get_chart_data, resample_ohlcv


def render(ticker: str):
    st.title("Chart")

    if ticker == "-":
        return

    st.write(f"**{ticker}**")
    st.caption("Set duration to '-' to select a custom date range")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        start_date = st.date_input("Start date", datetime.today().date() - timedelta(days=180))
    with c2:
        end_date = st.date_input("End date", datetime.today().date())
    with c3:
        duration = st.selectbox("Duration", ["-", "1mo", "3mo", "6mo", "ytd", "1y", "3y", "5y", "max"])
    with c4:
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"])
    with c5:
        sampling = st.selectbox("Sampling", ["Ngày", "Tuần", "Tháng"])
    with c6:
        plot_type = st.selectbox("Plot", ["Line", "Candle"])

    data = get_chart_data(ticker, start_date, end_date, duration, interval)
    if data.empty:
        st.warning("Không lấy được dữ liệu cho khoảng thời gian đã chọn.")
        return

    freq_map = {"Ngày": "D", "Tuần": "W", "Tháng": "ME"}
    resampled = resample_ohlcv(data[["Date", "Open", "High", "Low", "Close", "Volume"]], freq_map[sampling])
    # merge lại SMA cho phần close line (dùng SMA gốc theo ngày, không resample)
    resampled = resampled.merge(data[["Date", "SMA"]], on="Date", how="left")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if plot_type == "Line":
        fig.add_trace(
            go.Scatter(x=resampled["Date"], y=resampled["Close"], mode="lines", name="Close"),
            secondary_y=False,
        )
    else:
        fig.add_trace(
            go.Candlestick(
                x=resampled["Date"], open=resampled["Open"], high=resampled["High"],
                low=resampled["Low"], close=resampled["Close"], name="Candle",
            ),
            secondary_y=False,
        )

    fig.add_trace(
        go.Scatter(x=resampled["Date"], y=resampled["SMA"], mode="lines", name="50-day SMA"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(x=resampled["Date"], y=resampled["Volume"], name="Volume", opacity=0.4),
        secondary_y=True,
    )

    fig.update_yaxes(range=[0, resampled["Volume"].max() * 3], showticklabels=False, secondary_y=True)
    fig.update_layout(height=600, legend=dict(orientation="h"))

    st.plotly_chart(fig, use_container_width=True)
