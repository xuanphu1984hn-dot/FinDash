# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

> Project đang trong quá trình xây dựng. Commit này thêm `app.py` (entry point)
> và 3 tab đầu tiên cho phân tích 1 mã (Summary/Chart/Statistics). Portfolio
> Analysis, Monte Carlo và Chatbot sẽ được bổ sung ở các commit tiếp theo.

---

## Cấu trúc project (hiện tại)

```
findash_project/
├── app.py                      # entry point, chạy: streamlit run app.py
├── requirements.txt
├── data/
│   └── data_utils.py           # toàn bộ hàm lấy & định dạng dữ liệu (yfinance)
├── analysis/
│   ├── capm.py                 # CAPM, APT, Efficient Frontier
│   └── monte_carlo.py          # Monte Carlo cho 1 mã và cả danh mục
└── tabs/
    ├── tab_summary.py          # [1] Summary
    ├── tab_chart.py            # [2] Chart
    └── tab_statistics.py       # [3] Statistics / Financials / Analysis
```

---

## Luồng chính (`app.py`)

`app.py` là entry point (`streamlit run app.py`). Sidebar cho chọn:

- **Ticker**: danh sách ghép từ `POPULAR_EXTRA_TICKERS` (crypto: BTC/ETH/SOL,
  ETF trái phiếu: TLT/IEF/BND) và `get_sp500_tickers()`. Dropdown hiện tên thân
  thiện (vd "Bitcoin (BTC-USD)") nhưng giá trị trả về vẫn là ticker chuẩn (vd
  "BTC-USD"), nên mọi hàm xử lý dữ liệu phía sau dùng chung logic mà không cần
  phân biệt loại tài sản.
- **Tab**: Summary, Chart, Statistics, Financials, Analysis (3 tab sau dùng chung
  module `tab_statistics.py`).

---

## `data/data_utils.py` — lớp lấy dữ liệu

Xem chi tiết các hàm `fmt_value`, `get_sp500_tickers`, `POPULAR_EXTRA_TICKERS`,
`get_summary`, `get_chart_data`, `get_valuation_measures`, `get_financial_highlights`,
`get_financial_statement`, `get_analysis`... — tất cả có cache (`st.cache_data`)
và xử lý N/A an toàn.

## `analysis/capm.py` & `analysis/monte_carlo.py`

Đã có sẵn công thức CAPM, APT, Efficient Frontier, Monte Carlo — sẽ được gắn vào
giao diện ở các tab Portfolio/Monte Carlo (commit tiếp theo).

---

## `tabs/` — các trang giao diện (hiện tại)

| File | Nội dung |
|---|---|
| `tab_summary.py` | Bảng thông tin nhanh (`get_summary`) + biểu đồ giá area chart có range selector (1M/3M/6M/YTD/1Y/3Y/5Y/MAX) |
| `tab_chart.py` | Biểu đồ Line/Candlestick + SMA + Volume, chọn khoảng ngày hoặc period cố định, resample theo ngày/tuần/tháng |
| `tab_statistics.py` | 3 hàm render riêng: `render_statistics` (Valuation + Financial Highlights), `render_financials` (Income/Balance/Cash Flow theo năm/quý), `render_analysis` (earnings estimate, EPS trend, recommendations...) |

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A" thay vì làm vỡ
  giao diện (`fmt_value()` + `is_valid_ticker_info()`).
- Nếu muốn hỗ trợ cổ phiếu Việt Nam (HOSE/HNX), Yahoo Finance hỗ trợ rất hạn chế —
  nên cân nhắc bổ sung `vnstock` làm nguồn dữ liệu thứ hai.