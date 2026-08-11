"""
data_utils.py
--------------
Tất cả các hàm lấy dữ liệu tài chính, thay thế cho thư viện yahoo_fin
(đã ngừng hoạt động vì Yahoo Finance đổi cấu trúc trang).
Chỉ dùng yfinance, có cache để tránh gọi lại API quá nhiều lần.
"""

from datetime import datetime, date

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np


# ----------------------------------------------------------------------
# Helpers xử lý dữ liệu thiếu / None từ yfinance
# ----------------------------------------------------------------------

def fmt_value(value, kind: str = "auto"):
    """
    Định dạng giá trị lấy từ yfinance .info cho dễ đọc, xử lý an toàn khi None/NaN.
    kind: 'auto' | 'pct' | 'large' | 'date' | 'raw'
    """
    if value is None:
        return "N/A"
    if isinstance(value, float) and np.isnan(value):
        return "N/A"

    try:
        if kind == "pct":
            return f"{value:.2%}"

        if kind == "date":
            # yfinance thường trả về unix timestamp cho các trường ngày
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value).strftime("%Y-%m-%d")
            return str(value)

        if kind == "large":
            abs_v = abs(value)
            sign = "-" if value < 0 else ""
            if abs_v >= 1e12:
                return f"{sign}{abs_v/1e12:.2f}T"
            if abs_v >= 1e9:
                return f"{sign}{abs_v/1e9:.2f}B"
            if abs_v >= 1e6:
                return f"{sign}{abs_v/1e6:.2f}M"
            return f"{value:,.2f}"

        if kind == "raw" or kind == "auto":
            if isinstance(value, (int, float)):
                return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
            return str(value)

    except Exception:
        return str(value)

    return str(value)


def is_valid_ticker_info(info: dict) -> bool:
    """
    Kiểm tra info trả về từ yfinance có hợp lệ không (mã sai/delisted thường trả về
    dict gần như rỗng, chỉ có vài field mặc định).
    """
    if not info:
        return False
    # yfinance trả về dict rỗng hoặc chỉ có vài field mặc định khi ticker không tồn tại
    key_signals = ["previousClose", "regularMarketPrice", "currentPrice", "open", "symbol"]
    return any(info.get(k) is not None for k in key_signals)


# ----------------------------------------------------------------------
# Danh sách mã cổ phiếu
# ----------------------------------------------------------------------

@st.cache_data(ttl=86400)  # cache 1 ngày
def get_sp500_tickers():
    """Lấy danh sách mã S&P 500 từ Wikipedia (thay cho si.tickers_sp500())."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = sorted(df["Symbol"].str.replace(".", "-", regex=False).tolist())
        return tickers
    except Exception:
        # fallback nếu không lấy được (mất mạng, Wikipedia đổi cấu trúc, ...)
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"]


# Một danh sách mẫu cho cổ phiếu Việt Nam (Yahoo Finance hỗ trợ hạn chế mã VN,
# nên đây chỉ là các mã niêm yết ở nước ngoài / ADR hoặc index liên quan).
# Nếu muốn dữ liệu VN chính xác, khuyến nghị dùng thêm thư viện `vnstock`.
VN_RELATED_TICKERS = ["VNM", "^VNINDEX"]  # placeholder, tuỳ chỉnh theo nhu cầu

# ----------------------------------------------------------------------
# NEW: Danh sách mã phổ biến ngoài cổ phiếu Mỹ (crypto & trái phiếu)
# ----------------------------------------------------------------------
# Bổ sung để đáp ứng đúng yêu cầu đề bài: "Một cổ phiếu (trái phiếu, bitcoin, etc.)".
# Dùng dict {ticker: tên hiển thị} để dropdown thân thiện hơn, nhưng giá trị THỰC
# (key) vẫn là mã ticker hợp lệ mà yfinance hiểu được — mọi hàm phía trên (get_summary,
# get_chart_data, get_stock_history...) không cần sửa gì, vì chúng chỉ nhận vào 1
# chuỗi ticker và gọi yfinance giống hệt cách gọi với "AAPL".
#
# - BTC-USD, ETH-USD, SOL-USD: giá Bitcoin/Ethereum/Solana theo USD (dữ liệu đầy đủ,
#   có giá/khối lượng/lịch sử, nhưng sẽ hiện "N/A" ở các chỉ số kiểu công ty như
#   PE Ratio, EPS — vì tiền mã hoá không có các chỉ số đó. Đây là hành vi ĐÚNG,
#   không phải lỗi, nhờ cơ chế fmt_value() đã xử lý sẵn ở trên.)
# - TLT/IEF/BND: các ETF trái phiếu chính phủ Mỹ (20+ năm / 7-10 năm / tổng hợp),
#   dùng để đại diện cho "trái phiếu" vì đây là tài sản giao dịch thật có đầy đủ
#   giá/volume — khác với ^TNX (chỉ là chỉ số lợi suất, không phải tài sản để mua bán).
POPULAR_EXTRA_TICKERS = {
    "BTC-USD": "Bitcoin (BTC-USD)",
    "ETH-USD": "Ethereum (ETH-USD)",
    "SOL-USD": "Solana (SOL-USD)",
    "TLT": "US Treasury 20+Y Bond ETF (TLT)",
    "IEF": "US Treasury 7-10Y Bond ETF (IEF)",
    "BND": "US Total Bond Market ETF (BND)",
}


# ----------------------------------------------------------------------
# Summary (Tab 1)
# ----------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_summary(ticker: str) -> pd.DataFrame:
    """Thay thế si.get_quote_table(). Trả về DataFrame 2 cột attribute/value.
    Các giá trị thiếu (None) được hiển thị là 'N/A' thay vì làm vỡ giao diện."""
    stock = yf.Ticker(ticker)
    info = stock.info

    if not is_valid_ticker_info(info):
        return pd.DataFrame(
            [["Trạng thái", "Không tìm thấy dữ liệu cho mã này (có thể sai mã hoặc đã hủy niêm yết)"]],
            columns=["attribute", "value"],
        )

    day_low, day_high = info.get("dayLow"), info.get("dayHigh")
    wk_low, wk_high = info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")

    fields = {
        "Previous Close": fmt_value(info.get("previousClose")),
        "Open": fmt_value(info.get("open")),
        "Bid": fmt_value(info.get("bid")),
        "Ask": fmt_value(info.get("ask")),
        "Day's Range": f"{fmt_value(day_low)} - {fmt_value(day_high)}",
        "52 Week Range": f"{fmt_value(wk_low)} - {fmt_value(wk_high)}",
        "Volume": fmt_value(info.get("volume")),
        "Avg. Volume": fmt_value(info.get("averageVolume")),
        "Market Cap": fmt_value(info.get("marketCap"), kind="large"),
        "Beta (5Y Monthly)": fmt_value(info.get("beta")),
        "PE Ratio (TTM)": fmt_value(info.get("trailingPE")),
        "EPS (TTM)": fmt_value(info.get("trailingEps")),
        "Earnings Date": fmt_value(info.get("earningsTimestampStart"), kind="date"),
        "Forward Dividend & Yield": fmt_value(info.get("dividendYield"), kind="pct"),
        "Ex-Dividend Date": fmt_value(info.get("exDividendDate"), kind="date"),
        "1y Target Est": fmt_value(info.get("targetMeanPrice")),
    }

    df = pd.DataFrame(list(fields.items()), columns=["attribute", "value"])
    return df


@st.cache_data(ttl=600)
def get_stock_history(ticker: str, period: str = "max", interval: str = "1d") -> pd.DataFrame:
    """Thay thế yf.download cũ, dùng interface Ticker.history ổn định hơn."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    df = df.reset_index()
    return df


# ----------------------------------------------------------------------
# Chart (Tab 2)
# ----------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_chart_data(ticker: str, start_date=None, end_date=None,
                    duration: str = "-", interval: str = "1d",
                    sma_window: int = 50) -> pd.DataFrame:
    """
    Lấy dữ liệu giá + volume, tính SMA.
    duration != '-' -> lấy theo period (1mo, 3mo, ...)
    duration == '-' -> lấy theo khoảng start_date/end_date
    """
    stock = yf.Ticker(ticker)

    # Lấy toàn bộ lịch sử để tính SMA chính xác (không bị cắt cụt ở đầu)
    full_hist = stock.history(period="max", interval="1d").reset_index()
    full_hist["SMA"] = full_hist["Close"].rolling(sma_window).mean()
    sma_only = full_hist[["Date", "SMA"]]

    if duration != "-":
        data = stock.history(period=duration, interval=interval).reset_index()
    else:
        data = stock.history(start=start_date, end=end_date, interval=interval).reset_index()

    # Chuẩn hoá tên cột ngày (interval intraday trả về "Datetime")
    date_col = "Date" if "Date" in data.columns else "Datetime"
    if date_col != "Date":
        data = data.rename(columns={date_col: "Date"})

    data = data.merge(sma_only, on="Date", how="left")
    return data


def resample_ohlcv(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """
    Resample dữ liệu OHLCV theo tần suất mong muốn.
    freq: 'D' (ngày), 'W' (tuần), 'M' (tháng)
    """
    df = df.set_index("Date")
    agg = {
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }
    out = df.resample(freq).agg(agg).dropna(how="all").reset_index()
    return out


# ----------------------------------------------------------------------
# Statistics / Financials (Tab 3, 4)
# ----------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation_measures(ticker: str) -> pd.DataFrame:
    """Thay thế si.get_stats_valuation()."""
    info = yf.Ticker(ticker).info

    if not is_valid_ticker_info(info):
        return pd.DataFrame([["Trạng thái", "Không có dữ liệu"]], columns=["Attribute", "Value"])

    fields = {
        "Market Cap": fmt_value(info.get("marketCap"), kind="large"),
        "Enterprise Value": fmt_value(info.get("enterpriseValue"), kind="large"),
        "Trailing P/E": fmt_value(info.get("trailingPE")),
        "Forward P/E": fmt_value(info.get("forwardPE")),
        "PEG Ratio": fmt_value(info.get("pegRatio")),
        "Price/Sales (TTM)": fmt_value(info.get("priceToSalesTrailing12Months")),
        "Price/Book (mrq)": fmt_value(info.get("priceToBook")),
        "Enterprise Value/Revenue": fmt_value(info.get("enterpriseToRevenue")),
        "Enterprise Value/EBITDA": fmt_value(info.get("enterpriseToEbitda")),
    }
    df = pd.DataFrame(list(fields.items()), columns=["Attribute", "Value"])
    return df


@st.cache_data(ttl=600)
def get_financial_highlights(ticker: str) -> dict:
    """Thay thế si.get_stats() -- trả dict gồm nhiều DataFrame nhỏ theo nhóm.
    Mọi giá trị thiếu (None) hiển thị 'N/A' thay vì làm vỡ giao diện."""
    info = yf.Ticker(ticker).info
    invalid = not is_valid_ticker_info(info)

    groups_raw = {
        "Fiscal Year": {
            "Fiscal Year Ends": (info.get("lastFiscalYearEnd"), "date"),
            "Most Recent Quarter": (info.get("mostRecentQuarter"), "date"),
        },
        "Profitability": {
            "Profit Margin": (info.get("profitMargins"), "pct"),
            "Operating Margin (ttm)": (info.get("operatingMargins"), "pct"),
        },
        "Management Effectiveness": {
            "Return on Assets (ttm)": (info.get("returnOnAssets"), "pct"),
            "Return on Equity (ttm)": (info.get("returnOnEquity"), "pct"),
        },
        "Income Statement": {
            "Revenue (ttm)": (info.get("totalRevenue"), "large"),
            "Revenue Per Share (ttm)": (info.get("revenuePerShare"), "raw"),
            "Quarterly Revenue Growth (yoy)": (info.get("revenueGrowth"), "pct"),
            "Gross Profit (ttm)": (info.get("grossProfits"), "large"),
            "EBITDA": (info.get("ebitda"), "large"),
            "Net Income Avi to Common (ttm)": (info.get("netIncomeToCommon"), "large"),
            "Diluted EPS (ttm)": (info.get("trailingEps"), "raw"),
            "Quarterly Earnings Growth (yoy)": (info.get("earningsGrowth"), "pct"),
        },
        "Balance Sheet": {
            "Total Cash (mrq)": (info.get("totalCash"), "large"),
            "Total Cash Per Share (mrq)": (info.get("totalCashPerShare"), "raw"),
            "Total Debt (mrq)": (info.get("totalDebt"), "large"),
            "Total Debt/Equity (mrq)": (info.get("debtToEquity"), "raw"),
            "Current Ratio (mrq)": (info.get("currentRatio"), "raw"),
            "Book Value Per Share (mrq)": (info.get("bookValue"), "raw"),
        },
        "Cash Flow Statement": {
            "Operating Cash Flow (ttm)": (info.get("operatingCashflow"), "large"),
            "Levered Free Cash Flow (ttm)": (info.get("freeCashflow"), "large"),
        },
        "Stock Price History": {
            "Beta (5Y Monthly)": (info.get("beta"), "raw"),
            "52 Week Change": (info.get("52WeekChange"), "pct"),
            "S&P500 52-Week Change": (info.get("SandP52WeekChange"), "pct"),
            "52 Week High": (info.get("fiftyTwoWeekHigh"), "raw"),
            "52 Week Low": (info.get("fiftyTwoWeekLow"), "raw"),
            "50-Day Moving Average": (info.get("fiftyDayAverage"), "raw"),
            "200-Day Moving Average": (info.get("twoHundredDayAverage"), "raw"),
        },
        "Share Statistics": {
            "Avg Vol (3 month)": (info.get("averageVolume"), "raw"),
            "Avg Vol (10 day)": (info.get("averageVolume10days"), "raw"),
            "Shares Outstanding": (info.get("sharesOutstanding"), "large"),
            "Float": (info.get("floatShares"), "large"),
            "% Held by Insiders": (info.get("heldPercentInsiders"), "pct"),
            "% Held by Institutions": (info.get("heldPercentInstitutions"), "pct"),
            "Shares Short": (info.get("sharesShort"), "large"),
        },
        "Dividends & Splits": {
            "Forward Annual Dividend Rate": (info.get("dividendRate"), "raw"),
            "Forward Annual Dividend Yield": (info.get("dividendYield"), "pct"),
            "Trailing Annual Dividend Rate": (info.get("trailingAnnualDividendRate"), "raw"),
            "5 Year Average Dividend Yield": (info.get("fiveYearAvgDividendYield"), "pct"),
            "Payout Ratio": (info.get("payoutRatio"), "pct"),
            "Last Split Factor": (info.get("lastSplitFactor"), "raw"),
        },
    }

    result = {}
    for group_name, fields in groups_raw.items():
        if invalid:
            rows = [(k, "N/A") for k in fields]
        else:
            rows = [(k, fmt_value(v, kind=kind)) for k, (v, kind) in fields.items()]
        result[group_name] = pd.DataFrame(rows, columns=["Attribute", "Value"])
    return result


@st.cache_data(ttl=600)
def get_financial_statement(ticker: str, statement: str, period: str) -> pd.DataFrame:
    """
    statement: 'Income Statement' | 'Balance Sheet' | 'Cash Flow'
    period: 'Yearly' | 'Quarterly'
    Thay thế si.get_income_statement / get_balance_sheet / get_cash_flow
    """
    stock = yf.Ticker(ticker)

    mapping = {
        ("Income Statement", "Yearly"): stock.financials,
        ("Income Statement", "Quarterly"): stock.quarterly_financials,
        ("Balance Sheet", "Yearly"): stock.balance_sheet,
        ("Balance Sheet", "Quarterly"): stock.quarterly_balance_sheet,
        ("Cash Flow", "Yearly"): stock.cashflow,
        ("Cash Flow", "Quarterly"): stock.quarterly_cashflow,
    }
    df = mapping.get((statement, period), pd.DataFrame())
    return df


@st.cache_data(ttl=600)
def get_analysis(ticker: str) -> dict:
    """
    Thay thế si.get_analysts_info(). Dùng các thuộc tính mới của yfinance
    thay vì scrape HTML (ổn định hơn nhiều).
    """
    stock = yf.Ticker(ticker)
    result = {}

    try:
        result["Earnings Estimate"] = stock.earnings_estimate
    except Exception:
        result["Earnings Estimate"] = pd.DataFrame()

    try:
        result["Revenue Estimate"] = stock.revenue_estimate
    except Exception:
        result["Revenue Estimate"] = pd.DataFrame()

    try:
        result["Earnings History"] = stock.earnings_history
    except Exception:
        result["Earnings History"] = pd.DataFrame()

    try:
        result["EPS Trend"] = stock.eps_trend
    except Exception:
        result["EPS Trend"] = pd.DataFrame()

    try:
        result["EPS Revisions"] = stock.eps_revisions
    except Exception:
        result["EPS Revisions"] = pd.DataFrame()

    try:
        result["Growth Estimates"] = stock.growth_estimates
    except Exception:
        result["Growth Estimates"] = pd.DataFrame()

    try:
        result["Recommendations"] = stock.recommendations
    except Exception:
        result["Recommendations"] = pd.DataFrame()

    return result


# ----------------------------------------------------------------------
# Portfolio helpers (Tab 4 - CAPM/APT + Monte Carlo)
# ----------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_multi_close_prices(tickers: list, period: str = "5y") -> pd.DataFrame:
    """Lấy giá đóng cửa của nhiều mã, trả về DataFrame với mỗi cột là 1 mã."""
    data = yf.download(tickers, period=period)["Close"]
    if isinstance(data, pd.Series):  # trường hợp chỉ 1 ticker
        data = data.to_frame(name=tickers[0])
    return data.dropna(how="all")


@st.cache_data(ttl=600)
def get_risk_free_rate() -> float:
    """
    Lấy lãi suất phi rủi ro xấp xỉ từ lợi suất trái phiếu Mỹ 10 năm (^TNX).
    Trả về dạng thập phân (vd 0.04 = 4%/năm). Có fallback nếu lỗi mạng.
    """
    try:
        tnx = yf.Ticker("^TNX").history(period="5d")
        return float(tnx["Close"].iloc[-1]) / 100
    except Exception:
        return 0.04  # fallback 4%