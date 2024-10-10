# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from pathlib import Path

from infra.common.globals import GlobalRuntimeEnvironment
from infra.common.schema import ApplicationSourceArgs
from infra.settings_main import project_name

import datarobot as dr


def ensure_app_settings(app_id: str) -> None:
    dr.client.get_client().patch(
        f"customApplications/{app_id}/",
        json={"allowAutoStopping": True},
    )


_application_path = Path("frontend/")

app_source_args = ApplicationSourceArgs(
    resource_name="qa-app-source",
    base_environment_id=GlobalRuntimeEnvironment.PYTHON_39_STREAMLIT.value.id,
    name=f"QA Application Source [{project_name}]",
    files=[
        (str(f), str(f.relative_to(_application_path)))
        for f in _application_path.glob("**/*")
        if f.is_file()
    ]
    + [
        ("docsassist/__init__.py", "docsassist/__init__.py"),
        ("docsassist/deployments.py", "docsassist/deployments.py"),
        ("docsassist/predict.py", "docsassist/predict.py"),
        ("docsassist/schema.py", "docsassist/schema.py"),
    ],
).model_dump(mode="json", exclude_none=True)

app_resource_name: str = "qa-app"
app_name: str = f"QA Application [{project_name}]"
