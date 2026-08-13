# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

> Project đang trong quá trình xây dựng. Commit này thêm tab Monte Carlo
> Simulation cho 1 mã. Portfolio Analysis (CAPM/APT + Monte Carlo danh mục) và
> Chatbot sẽ được bổ sung ở các commit tiếp theo.

---

## Cấu trúc project (hiện tại)

```
findash_project/
├── app.py                      # entry point, chạy: streamlit run app.py
├── requirements.txt
├── data/
│   └── data_utils.py
├── analysis/
│   ├── capm.py
│   └── monte_carlo.py
└── tabs/
    ├── tab_summary.py          # [1] Summary
    ├── tab_chart.py            # [2] Chart
    ├── tab_statistics.py       # [3] Statistics / Financials / Analysis
    └── tab_montecarlo.py       # [5] Monte Carlo Simulation (1 mã)
```

---

## Luồng chính (`app.py`)

Sidebar cho chọn ticker (S&P 500 + crypto/ETF trái phiếu qua `POPULAR_EXTRA_TICKERS`)
và tab: Summary, Chart, Statistics, Financials, Analysis, **Monte Carlo Simulation**.

---

## `tabs/tab_montecarlo.py` — Monte Carlo cho 1 mã (mới)

Dùng `monte_carlo_single_stock` từ `analysis/monte_carlo.py`:

- Lấy giá 3 tháng gần nhất (`get_stock_history(ticker, period="3mo")`) để tính
  daily volatility.
- Cho chọn số lần mô phỏng (200/500/1000/2000) và số ngày mô phỏng (30/60/90).
- Vẽ toàn bộ các đường giá mô phỏng (Plotly), đánh dấu giá hiện tại.
- Tính **Value at Risk (VaR)** ở độ tin cậy 95% từ phân phối giá cuối kỳ
  (`compute_var`), kèm histogram phân phối.
- Lưu kết quả vào `st.session_state["montecarlo_context"]` — sẽ được Chatbot
  dùng làm context ở commit sau.

## `tabs/` — tổng hợp các trang giao diện (hiện tại)

| File | Nội dung |
|---|---|
| `tab_summary.py` | Bảng thông tin nhanh + biểu đồ giá area chart có range selector |
| `tab_chart.py` | Line/Candlestick + SMA + Volume, resample ngày/tuần/tháng |
| `tab_statistics.py` | Valuation/Financial Highlights, Income/Balance/Cash Flow, Analysis |
| `tab_montecarlo.py` | Monte Carlo 1 mã + histogram phân phối giá cuối kỳ + VaR |

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A".
- Monte Carlo 1 mã dùng volatility tính từ 3 tháng gần nhất; phiên bản cho cả
  danh mục (commit sau) sẽ khác — có tính tương quan qua phân rã Cholesky.