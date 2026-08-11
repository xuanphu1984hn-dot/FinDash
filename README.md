# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

> Project đang trong quá trình xây dựng. Commit này mới có lớp lấy dữ liệu
> (`data/`), các phần `analysis/` (CAPM, APT, Monte Carlo) và `tabs/` (giao diện)
> sẽ được bổ sung ở các commit tiếp theo.

---

## Cấu trúc project (hiện tại)

```
findash_project/
├── requirements.txt
└── data/
    └── data_utils.py           # toàn bộ hàm lấy & định dạng dữ liệu (yfinance)
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
  Dropdown hiện tên thân thiện (vd "Bitcoin (BTC-USD)") nhưng giá trị trả về vẫn
  là ticker chuẩn yfinance, nên các hàm bên dưới không cần phân biệt loại tài sản.
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

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A" thay vì làm vỡ
  giao diện (`fmt_value()` + `is_valid_ticker_info()`).
- Nếu muốn hỗ trợ cổ phiếu Việt Nam (HOSE/HNX), Yahoo Finance hỗ trợ rất hạn chế —
  nên cân nhắc bổ sung `vnstock` làm nguồn dữ liệu thứ hai (xem `VN_RELATED_TICKERS`,
  hiện chỉ là placeholder).