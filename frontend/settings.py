# Copyright 2024 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    render_grading_model_scores: bool = Field(
        description="Whether to show scores from the grading model"
    )
    page_title: str = Field(description="The title of the app webpage")


app_settings = AppSettings(
    render_grading_model_scores=True,
    page_title="Guarded RAG Assistant",
)
