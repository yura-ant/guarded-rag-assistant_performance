# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import contextlib
import importlib
import os
from pathlib import Path
import sys
from typing import get_args

import pytest
from streamlit.testing.v1 import AppTest


from docsassist.schema import Grade


@contextlib.contextmanager
def cd(new_dir: Path):
    """Changes the current working directory to the given path and restores the old directory on exit."""
    prev_dir = os.getcwd()

    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev_dir)


@pytest.fixture
def grades() -> list:
    return get_args(Grade)


@pytest.fixture
def application(app_mode: str, pulumi_up) -> AppTest:
    import docsassist.predict

    if app_mode == "dr":
        pytest.skip("Skipping DR frontend tests")
    with cd("frontend"):
        sys.path.append(".")
        importlib.reload(docsassist.predict)
        yield AppTest.from_file("app.py", default_timeout=30)


@pytest.fixture
def app_prompt():
    return "What is the capital of France?"


@pytest.fixture
def app_post_prompt(application: AppTest, app_prompt: str):
    at = application.run()
    at.chat_input[0].set_value(app_prompt).run(timeout=60)
    return at


def test_produces_a_response(app_post_prompt: AppTest, app_prompt: str):
    response = app_post_prompt.session_state.response
    conversation_history_markdown = [
        i.value
        for i in app_post_prompt.markdown
        if '<div class="message-content">' in i.value
    ]
    assert "paris" in response.completion.lower()
    assert "France" in conversation_history_markdown[0]
    assert "paris" in conversation_history_markdown[1].lower()
    assert len(conversation_history_markdown) == 2


def test_reports_citations(app_post_prompt: AppTest):
    references = app_post_prompt.session_state.response.references
    citation_markdown = [i.value for i in app_post_prompt.expander[0].markdown]
    for i in range(len(references)):
        assert f"**Reference {i+1}:**" in citation_markdown

    assert len(references) > 0


def test_reports_grade(app_post_prompt: AppTest, grades: list):
    grade = app_post_prompt.header[0].value
    assert grade.replace("**Response Grade**: ", "") in grades


def test_submit_feedback(app_post_prompt: AppTest, grades: list):
    at = app_post_prompt
    at.button(f"button_{grades[0]}").click().run(timeout=30)

    assert len(at.button) == len(grades)
    assert at.success[0].value == "Thank you for your rating!"
