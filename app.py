import streamlit as st

from data.data_utils import get_sp500_tickers, POPULAR_EXTRA_TICKERS
from tabs import tab_summary, tab_chart, tab_statistics


st.set_page_config(page_title="FinDash", layout="wide")


def format_ticker(t):
    """Hiện tên thân thiện cho crypto/trái phiếu trong dropdown (vd 'Bitcoin (BTC-USD)'),
    còn các mã cổ phiếu bình thường vẫn hiện đúng mã (vd 'AAPL')."""
    return POPULAR_EXTRA_TICKERS.get(t, t)


def main():
    st.sidebar.title("FinDash")
    ticker_list = ["-"] + list(POPULAR_EXTRA_TICKERS.keys()) + get_sp500_tickers()
    ticker = st.sidebar.selectbox("Select a ticker", ticker_list, format_func=format_ticker)

    select_tab = st.sidebar.radio(
        "Select tab",
        ["Summary", "Chart", "Statistics", "Financials", "Analysis"],
    )

    if select_tab == "Summary":
        tab_summary.render(ticker)
    elif select_tab == "Chart":
        tab_chart.render(ticker)
    elif select_tab == "Statistics":
        tab_statistics.render_statistics(ticker)
    elif select_tab == "Financials":
        tab_statistics.render_financials(ticker)
    elif select_tab == "Analysis":
        tab_statistics.render_analysis(ticker)


if __name__ == "__main__":
    main()