import streamlit as st
import plotly.express as px

from data.data_utils import get_summary, get_stock_history


def render(ticker: str):
    st.title("Summary")
    st.write("Select ticker on the left to begin")

    if ticker == "-":
        return

    st.write(f"**{ticker}**")

    summary = get_summary(ticker)
    summary["value"] = summary["value"].astype(str)

    c1, c2 = st.columns(2)
    mid = len(summary) // 2
    with c1:
        st.dataframe(summary.iloc[:mid].set_index("attribute"), use_container_width=True)
    with c2:
        st.dataframe(summary.iloc[mid:].set_index("attribute"), use_container_width=True)

    chart_data = get_stock_history(ticker, period="max")
    if chart_data.empty:
        st.warning("Không lấy được dữ liệu giá cho mã này.")
        return

    fig = px.area(chart_data, x="Date", y="Close")
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label="MAX", step="all"),
            ])
        )
    )
    st.plotly_chart(fig, use_container_width=True)
