import json

import streamlit as st
import anthropic

from data.data_utils import get_summary


SYSTEM_PROMPT = """Bạn là trợ lý phân tích tài chính trong một dashboard đầu tư.
Nhiệm vụ của bạn là trả lời câu hỏi của người dùng dựa trên dữ liệu được cung cấp
trong phần "Context" bên dưới (giá cổ phiếu, chỉ số CAPM, kết quả Monte Carlo, v.v.)

Quy tắc:
- Chỉ dùng dữ liệu trong Context và kiến thức tài chính tổng quát để trả lời.
- Nếu không có đủ dữ liệu để trả lời chính xác, hãy nói rõ điều đó thay vì bịa số liệu.
- Trả lời ngắn gọn, dễ hiểu, có thể dùng bullet point cho danh sách.
- Đây không phải là lời khuyên đầu tư có tính pháp lý; nếu người dùng hỏi "nên mua/bán không",
  hãy trình bày các yếu tố định lượng liên quan (return kỳ vọng, rủi ro, beta...) để họ tự quyết định,
  và nhắc rằng đây không phải lời khuyên tài chính chính thức.
"""


def build_context(ticker: str) -> str:
    """Gom toàn bộ dữ liệu đang có trong session (summary, CAPM, Monte Carlo) làm context."""
    context = {}

    if ticker and ticker != "-":
        try:
            summary_df = get_summary(ticker)
            context["current_ticker"] = ticker
            context["summary"] = dict(zip(summary_df["attribute"], summary_df["value"].astype(str)))
        except Exception:
            pass

    if "portfolio_context" in st.session_state:
        context["portfolio_analysis"] = st.session_state["portfolio_context"]

    if "montecarlo_context" in st.session_state:
        context["monte_carlo"] = st.session_state["montecarlo_context"]

    return json.dumps(context, ensure_ascii=False, default=str, indent=2)


def render(ticker: str):
    st.title("Chatbot hỗ trợ")
    st.caption("Hỏi về mã cổ phiếu đang chọn, danh mục đầu tư, hoặc kết quả mô phỏng Monte Carlo.")

    api_key = st.secrets.get("ANTHROPIC_API_KEY", None) or st.text_input(
        "Nhập Anthropic API Key", type="password"
    )
    if not api_key:
        st.info("Nhập API key (hoặc cấu hình trong .streamlit/secrets.toml) để dùng chatbot.")
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Đặt câu hỏi về cổ phiếu / danh mục đầu tư...")
    if not question:
        return

    st.session_state.chat_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    context_str = build_context(ticker)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context (dữ liệu hiện tại trên dashboard):\n{context_str}\n\n"
                               f"Câu hỏi: {question}",
                }
            ],
        )
        answer = response.content[0].text
    except Exception as e:
        answer = f"Đã xảy ra lỗi khi gọi API: {e}"

    st.session_state.chat_messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
