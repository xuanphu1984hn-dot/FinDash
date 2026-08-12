# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

> Project đang trong quá trình xây dựng. Commit này bổ sung lớp `analysis/`
> (công thức CAPM/APT và Monte Carlo). Phần `tabs/` (giao diện Streamlit) sẽ
> được bổ sung ở các commit tiếp theo.

---

## Cấu trúc project (hiện tại)

```
findash_project/
├── requirements.txt
├── data/
│   └── data_utils.py           # toàn bộ hàm lấy & định dạng dữ liệu (yfinance)
└── analysis/
    ├── capm.py                 # CAPM, APT, Efficient Frontier
    └── monte_carlo.py          # Monte Carlo cho 1 mã và cả danh mục
```

---

## `data/data_utils.py` — lớp lấy dữ liệu

Toàn bộ truy vấn `yfinance` tập trung ở đây, có cache (`st.cache_data`, 600s hoặc
86400s cho danh sách S&P 500) để giảm số lần gọi API.

- **`fmt_value` / `is_valid_ticker_info`**: chuẩn hoá hiển thị (None/NaN → "N/A",
  format phần trăm / số lớn K-M-B-T / ngày từ timestamp) và phát hiện ticker
  không hợp lệ (sai mã, đã hủy niêm yết).
- **`get_sp500_tickers`**: scrape danh sách từ Wikipedia, có fallback nếu lỗi mạng.
- **`POPULAR_EXTRA_TICKERS`**: mở rộng ngoài cổ phiếu Mỹ — crypto (BTC/ETH/SOL),
  ETF trái phiếu (TLT/IEF/BND) — để đáp ứng yêu cầu "cổ phiếu/trái phiếu/bitcoin".
- **Summary/Chart**: `get_summary`, `get_stock_history`, `get_chart_data`,
  `resample_ohlcv`.
- **Statistics/Financials/Analysis**: `get_valuation_measures`,
  `get_financial_highlights`, `get_financial_statement`, `get_analysis`.
- **Portfolio helpers**: `get_multi_close_prices`, `get_risk_free_rate`
  (xấp xỉ từ lợi suất trái phiếu Mỹ 10 năm `^TNX`, fallback 4%).

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
> `FinDash_Bao_Cao_Cong_Thuc.docx` (sẽ đính kèm ở commit cuối).

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A" thay vì làm vỡ
  giao diện (`fmt_value()` + `is_valid_ticker_info()`).
- Nếu muốn hỗ trợ cổ phiếu Việt Nam (HOSE/HNX), Yahoo Finance hỗ trợ rất hạn chế —
  nên cân nhắc bổ sung `vnstock` làm nguồn dữ liệu thứ hai.
- Monte Carlo có 2 phiên bản độc lập: 1 mã và cả danh mục có tương quan — không
  dùng chung code vì logic sinh shock ngẫu nhiên khác nhau (đơn biến vs. đa biến
  qua Cholesky).