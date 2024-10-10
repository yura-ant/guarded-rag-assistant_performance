# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

# mypy: ignore-errors

import subprocess
import logging

logger = logging.getLogger(__name__)


def get_custom_app_id():
    custom_app_url = subprocess.check_output(
        ["pulumi", "stack", "output", "qa-app-url", "--non-interactive"],
        text=True,
    ).strip()
    return custom_app_url.split("/")[-2]


def test_app_running(pulumi_up, dr_client):
    custom_app_id = get_custom_app_id()
    msg = f"Custom application ID: {custom_app_id}"
    logger.info(msg)

    url = f"customApplications/{custom_app_id}/"
    app_response = dr_client.get(url, timeout=30)
    app_status = app_response.json()["status"]

    assert app_status in ["running", "paused"]
