import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:9000")


def post_api(path: str, **kwargs) -> requests.Response | None:
    try:
        return requests.post(f"{API_URL}{path}", **kwargs)
    except requests.RequestException as exc:
        st.error(f"无法连接业务 API：{exc}")
        return None


def error_detail(response: requests.Response) -> str:
    try:
        return response.json().get("detail", response.text)
    except (requests.JSONDecodeError, AttributeError):
        return response.text


st.set_page_config(page_title="本地图片助手", page_icon="image", layout="centered")
st.title("本地图片问答与 OCR")
uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png", "webp"])
question = st.text_input("问题", value="请描述图片中的主要内容。")
col1, col2 = st.columns(2)
if uploaded:
    st.image(uploaded, width="stretch")
    if col1.button("图片问答", type="primary"):
        with st.spinner("模型处理中..."):
            response = post_api(
                "/v1/image/qa",
                files={"image": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                data={"question": question},
                timeout=150,
            )
        if response is not None and response.ok:
            st.session_state.setdefault("messages", []).append((question, response.json()["answer"]))
        elif response is not None:
            st.error(error_detail(response))
    if col2.button("提取文字"):
        with st.spinner("OCR 处理中..."):
            response = post_api(
                "/v1/ocr",
                files={"image": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                timeout=60,
            )
        if response is not None and response.ok:
            st.text_area("OCR 结果", response.json()["text"], height=220)
        elif response is not None:
            st.error(error_detail(response))

st.divider()
st.subheader("文档知识库问答（RAG）")
rag_question = st.text_input("请输入关于本地文档的问题", value="项目中使用了哪些技术？")
rag_top_k = st.slider("检索片段数量", min_value=1, max_value=5, value=3)
if st.button("查询知识库", type="primary"):
    with st.spinner("正在检索文档并生成回答..."):
        response = post_api(
            "/v1/rag/query",
            data={"question": rag_question, "top_k": str(rag_top_k)},
            timeout=180,
        )
    if response is not None and response.ok:
        result = response.json()
        st.markdown("**回答**")
        st.write(result["answer"])
        sources = result.get("sources", [])
        if sources:
            st.markdown("**检索来源**")
            for source in sources:
                st.caption(f"{source['source']} | {source['chunk_id']} | 相似度 {source['score']}")
        else:
            st.info("没有检索到相关文档片段。")
    elif response is not None:
        st.error(error_detail(response))

for item_question, answer in st.session_state.get("messages", []):
    with st.chat_message("user"):
        st.write(item_question)
    with st.chat_message("assistant"):
        st.write(answer)
