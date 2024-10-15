# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

from enum import Enum
from typing import Type, Tuple, Optional
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from .common.globals import (
    GlobalPredictionEnvironmentPlatforms,
    GlobalRuntimeEnvironment,
)
from .common.schema import (
    PredictionEnvironmentArgs,
    UseCaseArgs,
)
from .common.stack import get_stack


class RAGType(str, Enum):
    DIY = "diy"
    DR = "dr"


class ApplicationType(str, Enum):
    DIY = "diy"
    DR = "dr"


class CoreSettings(BaseSettings):
    """Schema for core settings that can also be overridden by environment variables

    e.g. for running automated tests.
    """

    rag_documents: str = Field(
        description="Local path to zip file of pdf, txt, docx, md files to use with RAG",
    )
    rag_type: RAGType = Field(
        description="Whether to use DR RAG chunking, vectorization, retrieval, or user-provided (DIY)",
    )
    application_type: ApplicationType = Field(
        description="Whether to use the default DR QA frontend or a user-provided frontend (DIY)",
    )

    model_config = SettingsConfigDict(env_prefix="MAIN_", case_sensitive=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            init_settings,
        )


project_name = get_stack()

# Core settings are overridable by environment variables; env values take precedence
core = CoreSettings(
    rag_documents="assets/datarobot_english_documentation_docsassist.zip",
    rag_type=RAGType.DR,
    application_type=ApplicationType.DR,
)

runtime_environment_moderations = GlobalRuntimeEnvironment.PYTHON_311_MODERATIONS.value

default_prediction_server_id: Optional[str] = None

prediction_environment_args = PredictionEnvironmentArgs(
    resource_name=f"Guarded RAG Prediction Environment [{project_name}]",
    platform=GlobalPredictionEnvironmentPlatforms.DATAROBOT_SERVERLESS,
).model_dump(mode="json", exclude_none=True)

use_case_args = UseCaseArgs(
    resource_name=f"Guarded RAG Use Case [{project_name}]",
    description="Use case for Guarded RAG Assistant application",
).model_dump(exclude_none=True)
