# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

---

## Cách chạy project

```bash
# 1. Tạo và kích hoạt môi trường ảo (chỉ cần tạo 1 lần)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat (CMD) hoặc venv\Scripts\Activate.ps1 (PowerShell)

# 2. Cài các thư viện cần thiết
pip install -r requirements.txt

# 3. (Tuỳ chọn) Cấu hình API key cho Chatbot
# Mở file .streamlit/secrets.toml, điền ANTHROPIC_API_KEY = "sk-ant-..."
# Nếu bỏ qua bước này, tab Chatbot vẫn dùng được — sẽ hiện ô nhập API key trực tiếp trên giao diện.

# 4. Chạy ứng dụng
streamlit run app.py
```

Sau khi chạy, trình duyệt sẽ tự mở `http://localhost:8501`. Những lần chạy sau chỉ cần lặp lại bước 1 (activate) và bước 4 — không cần tạo lại venv hay cài lại thư viện.

---

## Cấu trúc project

```
findash_project/
├── app.py                      # entry point, điều hướng sidebar -> tab
├── data/
│   └── data_utils.py           # toàn bộ hàm lấy & định dạng dữ liệu (yfinance)
├── analysis/
│   ├── capm.py                 # CAPM, APT, Efficient Frontier
│   └── monte_carlo.py          # Monte Carlo cho 1 mã và cả danh mục
└── tabs/
    ├── tab_summary.py          # [1] Summary
    ├── tab_chart.py            # [2] Chart
    ├── tab_statistics.py       # [3] Statistics / Financials / Analysis
    ├── tab_portfolio.py        # [4] Portfolio: CAPM/APT + Efficient Frontier + Monte Carlo danh mục
    ├── tab_montecarlo.py       # [5] Monte Carlo Simulation (1 mã)
    └── tab_chatbot.py          # Chatbot hỗ trợ (Anthropic API)
```

---

## Luồng chính (`app.py`)

`app.py` là entry point (`streamlit run app.py`). Sidebar cho chọn:

- **Ticker**: danh sách ghép từ `POPULAR_EXTRA_TICKERS` (crypto: BTC/ETH/SOL,
  ETF trái phiếu: TLT/IEF/BND — để đáp ứng yêu cầu "cổ phiếu/trái phiếu/bitcoin")
  và `get_sp500_tickers()`. Dropdown hiện tên thân thiện (vd "Bitcoin (BTC-USD)")
  nhưng giá trị trả về vẫn là ticker chuẩn (vd "BTC-USD"), nên mọi hàm xử lý dữ
  liệu phía sau dùng chung logic mà không cần phân biệt loại tài sản.
- **Tab**: Summary, Chart, Statistics, Financials, Analysis (3 tab sau dùng chung
  module `tab_statistics.py`), Portfolio Analysis (CAPM/APT), Monte Carlo
  Simulation, Chatbot.

---

## `data/data_utils.py` — lớp lấy dữ liệu

Toàn bộ truy vấn `yfinance` tập trung ở đây, có cache (`st.cache_data`, 600s hoặc
86400s cho danh sách S&P 500) để giảm số lần gọi API.

- **`fmt_value` / `is_valid_ticker_info`**: chuẩn hoá hiển thị (None/NaN → "N/A",
  format phần trăm / số lớn K-M-B-T / ngày từ timestamp) và phát hiện ticker
  không hợp lệ (sai mã, đã hủy niêm yết).
- **`get_sp500_tickers`**: scrape danh sách từ Wikipedia, có fallback nếu lỗi mạng.
- **`POPULAR_EXTRA_TICKERS`**: mở rộng ngoài cổ phiếu Mỹ (crypto, ETF trái phiếu).
- **Summary/Chart**: `get_summary`, `get_stock_history`, `get_chart_data` (tính
  thêm SMA từ full lịch sử để không bị cụt đầu), `resample_ohlcv` (đổi tần suất
  ngày/tuần/tháng).
- **Statistics/Financials/Analysis**: `get_valuation_measures`,
  `get_financial_highlights` (nhiều nhóm: Profitability, Balance Sheet,
  Dividends...), `get_financial_statement` (income/balance sheet/cash flow,
  yearly/quarterly), `get_analysis` (earnings estimate, revisions,
  recommendations — mỗi field có try/except riêng để 1 field lỗi không làm vỡ cả trang).
- **Portfolio helpers**: `get_multi_close_prices` (giá nhiều mã cùng lúc),
  `get_risk_free_rate` (xấp xỉ từ lợi suất trái phiếu Mỹ 10 năm `^TNX`, fallback 4%).

---

## `analysis/capm.py` — CAPM, APT, Efficient Frontier

- `compute_returns`: daily return từ giá đóng cửa.
- `capm_single_stock` / `capm_portfolio`: hồi quy CAPM bằng `statsmodels.OLS`,
  trả về beta, alpha, expected return, R².
- `apt_multi_factor`: hồi quy đa nhân tố (APT) — 1 mã theo nhiều factor tuỳ chọn
  (thị trường, lãi suất, dầu, vàng, USD index).
- `portfolio_performance`: return/volatility hàng năm cho 1 bộ trọng số.
- `random_portfolios`: sinh ngẫu nhiên nhiều bộ trọng số để dựng Efficient Frontier.

## `analysis/monte_carlo.py` — mô phỏng Monte Carlo

- `monte_carlo_single_stock`: random walk giá 1 mã dựa trên daily volatility
  lịch sử (vector hoá bằng numpy).
- `compute_var`: Value at Risk theo percentile.
- `monte_carlo_portfolio`: mô phỏng cả danh mục, giữ tương quan giữa các mã bằng
  phân rã Cholesky trên ma trận hiệp phương sai.

> Công thức chi tiết và giải thích toán học xem trong file báo cáo
> `FinDash_Bao_Cao_Cong_Thuc.docx` đi kèm.

---

## `tabs/` — các trang giao diện

| File | Nội dung |
|---|---|
| `tab_summary.py` | Bảng thông tin nhanh (`get_summary`) + biểu đồ giá area chart có range selector (1M/3M/6M/YTD/1Y/3Y/5Y/MAX) |
| `tab_chart.py` | Biểu đồ Line/Candlestick + SMA + Volume, chọn khoảng ngày hoặc period cố định, resample theo ngày/tuần/tháng |
| `tab_statistics.py` | 3 hàm render riêng: `render_statistics` (Valuation + Financial Highlights), `render_financials` (Income/Balance/Cash Flow theo năm/quý), `render_analysis` (earnings estimate, EPS trend, recommendations...) |
| `tab_portfolio.py` | Trang tổng hợp: CAPM + Security Market Line, ma trận tương quan, Efficient Frontier (Monte Carlo random weights), xu hướng giá chuẩn hoá, APT đa nhân tố, Monte Carlo cho cả danh mục + VaR |
| `tab_montecarlo.py` | Monte Carlo cho 1 mã + histogram phân phối giá cuối kỳ + VaR |
| `tab_chatbot.py` | Chatbot dùng Anthropic API (`claude-sonnet-4-6`), context được build từ `get_summary` + dữ liệu đã tính ở các tab khác (xem bên dưới) |

### Chi tiết `tab_portfolio.py`

Trang nặng nhất, gồm 6 phần theo thứ tự:
1. **CAPM** — bảng beta/alpha/expected return cho từng mã + biểu đồ Security Market Line.
2. **Ma trận tương quan** giữa các mã (heatmap).
3. **Efficient Frontier** — mô phỏng nhiều danh mục ngẫu nhiên, đánh dấu danh mục
   Sharpe cao nhất và rủi ro thấp nhất.
4. **Xu hướng giá** danh mục đã chuẩn hoá (base = 100).
5. **APT** — chọn nhân tố tuỳ ý (`FACTOR_OPTIONS`: thị trường, lãi suất, dầu, vàng,
   USD index), hồi quy riêng cho từng mã, hiển thị bảng hệ số + R².
6. **Monte Carlo danh mục** — chọn cách phân bổ trọng số (Equal Weight / Sharpe
   cao nhất / rủi ro thấp nhất từ bước 3), mô phỏng giá trị danh mục tương lai,
   tính VaR 95%.

### Cơ chế chia sẻ context cho Chatbot

`tab_portfolio.py` và `tab_montecarlo.py` sau khi chạy xong sẽ lưu kết quả vào
`st.session_state["portfolio_context"]` và `st.session_state["montecarlo_context"]`.
`tab_chatbot.py` (hàm `build_context`) gom các state này cùng `get_summary(ticker)`
thành 1 khối JSON, đưa vào system prompt để chatbot trả lời dựa trên đúng dữ liệu
đang hiển thị trên dashboard tại thời điểm hỏi — không tự bịa số liệu.

---

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A" thay vì làm vỡ
  giao diện (`fmt_value()` + `is_valid_ticker_info()`).
- Nếu muốn hỗ trợ cổ phiếu Việt Nam (HOSE/HNX), Yahoo Finance hỗ trợ rất hạn chế —
  nên cân nhắc bổ sung `vnstock` làm nguồn dữ liệu thứ hai (xem `VN_RELATED_TICKERS`
  trong `data_utils.py`, hiện chỉ là placeholder).
- Monte Carlo có 2 phiên bản độc lập: 1 mã (`tab_montecarlo.py`) và cả danh mục
  có tương quan (`tab_portfolio.py`, phần 6) — không dùng chung code vì logic
  sinh shock ngẫu nhiên khác nhau (đơn biến vs. đa biến qua Cholesky).