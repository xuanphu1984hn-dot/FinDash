import streamlit as st

from data.data_utils import (
    get_valuation_measures,
    get_financial_highlights,
    get_financial_statement,
    get_analysis,
)


def render_statistics(ticker: str):
    st.title("Statistics")
    if ticker == "-":
        return
    st.write(f"**{ticker}**")

    c1, c2 = st.columns(2)

    highlights = get_financial_highlights(ticker)

    with c1:
        st.header("Valuation Measures")
        st.table(get_valuation_measures(ticker).set_index("Attribute"))

        st.header("Financial Highlights")
        for group in ["Fiscal Year", "Profitability", "Management Effectiveness",
                      "Income Statement", "Balance Sheet", "Cash Flow Statement"]:
            st.subheader(group)
            st.table(highlights[group].set_index("Attribute"))

    with c2:
        st.header("Trading Information")
        for group in ["Stock Price History", "Share Statistics", "Dividends & Splits"]:
            st.subheader(group)
            st.table(highlights[group].set_index("Attribute"))


def render_financials(ticker: str):
    st.title("Financials")
    if ticker == "-":
        return
    st.write(f"**{ticker}**")

    statement = st.selectbox("Show", ["Income Statement", "Balance Sheet", "Cash Flow"])
    period = st.selectbox("Period", ["Yearly", "Quarterly"])

    data = get_financial_statement(ticker, statement, period)
    if data.empty:
        st.warning("Không có dữ liệu cho lựa chọn này.")
    else:
        st.dataframe(data, use_container_width=True)


def render_analysis(ticker: str):
    st.title("Analysis")
    st.caption("Currency in USD")
    if ticker == "-":
        return
    st.write(f"**{ticker}**")

    analysis = get_analysis(ticker)
    for name, df in analysis.items():
        st.subheader(name)
        if df is None or (hasattr(df, "empty") and df.empty):
            st.write("Không có dữ liệu.")
        else:
            st.dataframe(df, use_container_width=True)
