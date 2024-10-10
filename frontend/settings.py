# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    render_grading_model_scores: bool = Field(
        description="Whether to show scores from the grading model"
    )
    page_title: str = Field(description="The title of the app webpage")


app_settings = AppSettings(
    render_grading_model_scores=True,
    page_title="DocsAssist",
)
