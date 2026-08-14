# FinDash — Financial Dashboard with Chatbot

Dashboard phân tích tài chính (CAPM, APT, Efficient Frontier, Monte Carlo...) kèm
Chatbot hỗ trợ, xây dựng bằng Streamlit.

Toàn bộ dữ liệu lấy qua `yfinance` (không dùng `yahoo_fin` vì thư viện này đã ngừng
hoạt động do Yahoo Finance đổi cấu trúc trang).

> Project đang trong quá trình xây dựng. Commit này thêm tab Portfolio
> Analysis (CAPM/APT/Efficient Frontier/Monte Carlo danh mục) — phần nặng nhất
> của dashboard. Chatbot sẽ được bổ sung ở commit cuối.

---

## Cấu trúc project (hiện tại)

```
findash_project/
├── app.py
├── requirements.txt
├── data/
│   └── data_utils.py
├── analysis/
│   ├── capm.py
│   └── monte_carlo.py
└── tabs/
    ├── tab_summary.py
    ├── tab_chart.py
    ├── tab_statistics.py
    ├── tab_portfolio.py         # [4] Portfolio: CAPM/APT + Efficient Frontier + Monte Carlo danh mục
    └── tab_montecarlo.py        # [5] Monte Carlo Simulation (1 mã)
```

---

## Luồng chính (`app.py`)

Sidebar cho chọn ticker và tab: Summary, Chart, Statistics, Financials, Analysis,
**Portfolio Analysis (CAPM/APT)**, Monte Carlo Simulation.

---

## `tabs/tab_portfolio.py` — Portfolio Analysis (mới, trang nặng nhất)

Gồm 6 phần theo thứ tự, dùng `analysis/capm.py` và `analysis/monte_carlo.py`:

1. **CAPM** — chọn ≥2 mã + 1 benchmark, chạy `capm_portfolio` ra bảng
   beta/alpha/expected return/R², vẽ biểu đồ **Security Market Line**.
2. **Ma trận tương quan** giữa các mã (heatmap Plotly).
3. **Efficient Frontier** — `random_portfolios` mô phỏng nhiều danh mục ngẫu
   nhiên, đánh dấu danh mục Sharpe cao nhất và rủi ro thấp nhất.
4. **Xu hướng giá** danh mục đã chuẩn hoá (base = 100).
5. **APT** — chọn nhân tố tuỳ ý (`FACTOR_OPTIONS`: thị trường, lãi suất, dầu,
   vàng, USD index), hồi quy `apt_multi_factor` riêng cho từng mã, hiển thị
   bảng hệ số + R².
6. **Monte Carlo danh mục** — chọn cách phân bổ trọng số (Equal Weight / Sharpe
   cao nhất / rủi ro thấp nhất từ bước 3), chạy `monte_carlo_portfolio` (có
   tương quan qua Cholesky), tính VaR 95%.

Kết quả được lưu vào `st.session_state["portfolio_context"]` — sẽ được Chatbot
dùng làm context ở commit sau.

## `tabs/` — tổng hợp các trang giao diện (hiện tại)

| File | Nội dung |
|---|---|
| `tab_summary.py` | Bảng thông tin nhanh + biểu đồ giá area chart |
| `tab_chart.py` | Line/Candlestick + SMA + Volume, resample ngày/tuần/tháng |
| `tab_statistics.py` | Valuation/Financial Highlights, Income/Balance/Cash Flow, Analysis |
| `tab_portfolio.py` | CAPM + SML, ma trận tương quan, Efficient Frontier, xu hướng giá, APT, Monte Carlo danh mục + VaR |
| `tab_montecarlo.py` | Monte Carlo 1 mã + histogram phân phối giá cuối kỳ + VaR |

## Ghi chú kỹ thuật

- Các giá trị bị thiếu (`None`) từ `yfinance` luôn hiển thị "N/A".
- Monte Carlo có 2 phiên bản độc lập: 1 mã và cả danh mục có tương quan — không
  dùng chung code vì logic sinh shock ngẫu nhiên khác nhau (đơn biến vs. đa biến
  qua Cholesky).
- `random_portfolios` hiện chỉ sinh trọng số dương (long-only), không giới hạn
  tỷ trọng tối đa mỗi mã.