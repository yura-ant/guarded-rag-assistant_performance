# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import base64
import logging
import os
import sys
from typing import get_args

import datarobot as dr
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)

from settings import app_settings

sys.path.append("../")
from docsassist.schema import (
    Grade,
    GraderOutput,
    RAGOutput,
)
from docsassist import predict


logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


DATAROBOT_ENDPOINT = os.getenv("DATAROBOT_ENDPOINT")
DATAROBOT_API_KEY = os.getenv("DATAROBOT_API_TOKEN")

st.set_page_config(
    page_title=app_settings.page_title, page_icon="./datarobot_favicon.png"
)

with open("./style.css") as f:
    css = f.read()

with open("./DataRobot.svg") as f:
    svg = f.read()

st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

dr.Client(endpoint=DATAROBOT_ENDPOINT, token=DATAROBOT_API_KEY)  # type: ignore[attr-defined]


if "messages" not in st.session_state:
    st.session_state.messages = []

if "response" not in st.session_state:
    st.session_state.response = {}

if "confidence" not in st.session_state:
    st.session_state.confidence = {}


def render_svg(svg: str) -> None:
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)


def render_message(
    container: DeltaGenerator, message: str, is_user: bool = False
) -> None:
    message_role = "user" if is_user else "ai"
    container.markdown(
        f"""
    <div class="chat-message {message_role}-message">
        <div class="message-content">
            <span class="message-label"><b>{'User' if is_user else 'Assistant'}:</b></span>
            <span class="message-text">{message}</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_conversation_history(container: DeltaGenerator) -> None:
    container.subheader("Conversation History")
    for message in st.session_state.messages[:-1]:  # Exclude the latest message
        render_message(container, message["content"], message["role"] == "user")
    st.markdown("---")


def render_answer_and_citations(
    container: DeltaGenerator, response: RAGOutput, grade_output: GraderOutput
) -> None:
    render_message(container, response.completion, is_user=False)

    if app_settings.render_grading_model_scores:
        st.header(f"**Response Grade**: {grade_output.grade}")
        st.markdown("**Confidence Scores:**")
        scores = ", ".join(
            f"{k}: {v:.1%}" for k, v in grade_output.class_scores.items()
        )
        st.markdown(scores)

    with st.expander("Show Citations"):
        for i, doc in enumerate(response.references):
            st.markdown(f"**Reference {i+1}:**")
            st.markdown(f"**Source:** {doc.metadata.source}")
            st.markdown("**Content:**")
            for text in doc.page_content.split("\\n"):
                if text.strip():
                    st.markdown(text)
            st.markdown("---")


def main() -> None:
    render_svg(svg)
    st.title(app_settings.page_title)

    chat_container = st.container()

    if st.session_state.messages:
        render_conversation_history(chat_container)
    answer_and_citations_placeholder = chat_container.container()
    if "prompt_sent" not in st.session_state:
        st.session_state.prompt_sent = False
    prompt = chat_container.chat_input(
        placeholder="Your message",
        key=None,
        max_chars=None,
        disabled=False,
        on_submit=None,
        args=None,
        kwargs=None,
    )

    if prompt and prompt.strip():
        st.session_state.prompt_sent = True

        with st.spinner("Getting AI response..."):
            response, association_id = predict.get_rag_completion(
                question=prompt,
                messages=st.session_state.messages,
            )
        st.session_state.response = response
        st.session_state.association_id = association_id
        st.session_state.messages.extend(
            [
                ChatCompletionUserMessageParam(content=prompt, role="user"),
                ChatCompletionAssistantMessageParam(
                    content=response.completion, role="assistant"
                ),
            ]
        )
        with st.spinner("Predicting grade..."):
            grade_output = predict.predict_grade(response, association_id)
        st.session_state.confidence = grade_output
        # display the grade
        st.write(f"Grade: {grade_output.class_scores}")

        st.rerun()

    if st.session_state.prompt_sent:
        render_answer_and_citations(
            answer_and_citations_placeholder,
            st.session_state.response,
            st.session_state.confidence,
        )

        st.subheader("**How would you rate this response?**")
        cols = st.columns(5)
        grades = get_args(Grade)

        for col, grade_to_submit in zip(cols, grades):
            if col.button(label=grade_to_submit, key=f"button_{grade_to_submit}"):
                predict.submit_grade(
                    grade_to_submit,
                    st.session_state.association_id,
                )
                st.success("Thank you for your rating!")

        st.write(
            """
        **Correct**: the response sufficiently answers the question.
        **Incorrect**: the response "hallucinates" or is the wrong answer to the question.
        **Incomplete**: the response does not fully answer the question.
        **Digress**: the response includes irrelevant information or is not concise.
        **No Answer**: the response claims it cannot or will not answer the question.
        """
        )


if __name__ == "__main__":
    main()
