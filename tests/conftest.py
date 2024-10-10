# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

# mypy: ignore-errors

import os
import subprocess
import time

import datarobot as dr
import uuid
import pandas as pd
import pytest
import logging
from dotenv import dotenv_values
from datarobot_predict.deployment import predict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--pulumi_up",
        action="store_true",
        default=False,
        help="Run pulumi up before conducting test. Otherwise use existing stack.",
    )


@pytest.fixture(params=["dr-dr", "dr-diy", "diy-dr", "diy-diy"], scope="session")
def mode(request, pytestconfig):
    if pytestconfig.getoption("pulumi_up") is False:
        from infra.settings_main import core

        app_type = core.application_type
        rag_type = core.rag_type
        rag, app = request.param.split("-")
        if rag != rag_type or app != app_type:
            pytest.skip(f"Skipping {request.param} test")
    return request.param


@pytest.fixture(scope="session")
def app_mode(mode):
    rag_mode, app_mode = mode.split("-")
    return app_mode


@pytest.fixture(scope="session")
def rag_mode(mode):
    rag_mode, app_mode = mode.split("-")
    return rag_mode


@pytest.fixture(scope="session")
def stack_name(app_mode, rag_mode):
    short_uuid = str(uuid.uuid4())[:5]
    return f"test-stack-{rag_mode}-{app_mode}-{short_uuid}"


@pytest.fixture(scope="session")
def session_env_vars(request, stack_name, rag_mode, app_mode):
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    env_vars = dotenv_values(env_file)
    session_vars = {
        "MAIN_RAG_TYPE": rag_mode,
        "MAIN_APPLICATION_TYPE": app_mode,
        "PROJECT_NAME": stack_name,
    }
    env_vars.update(session_vars)
    os.environ.update(env_vars)
    return session_vars


@pytest.fixture(scope="session")
def pulumi_up(stack_name, session_env_vars, pytestconfig):
    def run_command(command):
        proc = subprocess.run(command, check=False, text=True, capture_output=True)
        cmd = " ".join(command)
        if proc.returncode:
            msg = f"'{cmd}' exited {proc.returncode}"
            logger.warning(msg)
            msg = f"'{cmd}' STDOUT:\n{proc.stdout}"
            logger.warning(msg)
            msg = f"'{cmd}' STDERR:\n{proc.stderr}"
            logger.warning(msg)
        return proc

    if pytestconfig.getoption("pulumi_up"):
        logger.info(f"Running {stack_name} with {session_env_vars}")
        run_command(["pulumi", "stack", "init", stack_name, "--non-interactive"])
        proc = run_command(["pulumi", "up", "-y", "--non-interactive"])
        stack = subprocess.check_output(["pulumi", "stack", "output"], text=True)
        try:
            if proc.returncode:
                raise RuntimeError(f"`pulumi up` failed for {stack_name}")
            os.environ["PULUMI_STACK_CONTEXT"] = stack_name
            yield
        finally:
            run_command(["pulumi", "down", "-y", "--non-interactive"])
            run_command(
                ["pulumi", "stack", "rm", stack_name, "-y", "--non-interactive"]
            )
    else:
        stack = subprocess.check_output(
            ["pulumi", "stack"],
            text=True,
        ).split("\n")[0]
        logger.info(stack)
        yield


@pytest.fixture
def dr_client(session_env_vars):
    return dr.Client()


def predict_with_retry(
    deployment, data_frame, max_wait_seconds=300, retry_interval_seconds=5
):
    start_time = time.time()
    while True:
        try:
            prediction = predict(deployment, data_frame=data_frame)
            return prediction
        except dr.errors.ServerError as e:
            if "Inference server is starting" in str(e):
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_seconds:
                    raise TimeoutError(
                        f"Server did not start within {max_wait_seconds} seconds"
                    )
                logger.info(
                    f"Server is starting. Retrying in {retry_interval_seconds} seconds..."
                )
                time.sleep(retry_interval_seconds)
            else:
                # If it's a different ServerError, re-raise it
                raise


@pytest.fixture
def make_prediction(dr_client):
    def predict_function(input_json, deployment_id):
        deployment = dr.Deployment.get(deployment_id)
        predict_df = pd.DataFrame(input_json)
        while True:
            try:
                prediction = predict_with_retry(
                    deployment, data_frame=predict_df
                ).dataframe
                break
            except dr.errors.ServerError as e:
                if "Inference server is starting" in str(e):
                    continue

        return prediction.to_dict(orient="records")[0]

    return predict_function
