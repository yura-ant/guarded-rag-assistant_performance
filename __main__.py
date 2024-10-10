# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
import os
import pathlib

import pulumi
import pulumi_datarobot as datarobot

from docsassist.deployments import grading_deployment_env_name, rag_deployment_env_name
from infra import (
    settings_app_infra,
    settings_grader,
    settings_keyword_guard,
    settings_main,
    settings_rag,
)
from infra.common.feature_flags import check_feature_flags
from infra.common.papermill import run_notebook
from infra.common.urls import get_deployment_url
from infra.components.custom_model_deployment import CustomModelDeployment
from infra.components.dr_credential import DRCredential
from infra.components.rag_custom_model import RAGCustomModel
from infra.settings_global_guardrails import global_guardrails
from infra.settings_llm_credential import credential, credential_args

check_feature_flags(pathlib.Path("infra/feature_flag_requirements.yaml"))

if "DATAROBOT_DEFAULT_USE_CASE" in os.environ:
    use_case_id = os.environ["DATAROBOT_DEFAULT_USE_CASE"]
    pulumi.info(f"Using existing usecase {use_case_id}")
    use_case = datarobot.UseCase.get(
        id=use_case_id,
        resource_name="use-case-pre-existing",
    )
else:
    use_case = datarobot.UseCase(**settings_main.use_case_args)

if settings_main.default_prediction_server_id is None:
    prediction_environment = datarobot.PredictionEnvironment(
        **settings_main.prediction_environment_args,
    )
else:
    prediction_environment = datarobot.PredictionEnvironment.get(
        "prediction-environment-pre-existing",
        settings_main.default_prediction_server_id,
    )


llm_credential = DRCredential(
    resource_name="llm-credential",
    credential=credential,
    credential_args=credential_args,
)

keyword_guard_deployment = CustomModelDeployment(
    resource_name="keyword-guard",
    custom_model_args=settings_keyword_guard.custom_model_args,
    registered_model_args=settings_keyword_guard.registered_model_args,
    prediction_environment=prediction_environment,
    deployment_args=settings_keyword_guard.deployment_args,
)

global_guard_deployments = [
    datarobot.Deployment(
        registered_model_version_id=datarobot.get_global_model(
            name=guard.registered_model_name,
        ).version_id,
        prediction_environment_id=prediction_environment.id,
        **guard.deployment_args.model_dump(),
    )
    for guard in global_guardrails
]

all_guard_deployments = [keyword_guard_deployment] + global_guard_deployments

all_guardrails_configs = [
    settings_keyword_guard.custom_model_guard_configuration_args
] + [guard.custom_model_guard_configuration_args for guard in global_guardrails]


guard_configurations = [
    datarobot.CustomModelGuardConfigurationArgs(
        deployment_id=deployment.id,
        **guard_config_args.model_dump(mode="json", exclude_none=True),
    )
    for deployment, guard_config_args in zip(
        all_guard_deployments,
        all_guardrails_configs,
    )
]

if settings_main.core.rag_type == settings_main.RAGType.DR:
    rag_custom_model = RAGCustomModel(
        resource_name="rag-prep",
        use_case=use_case,
        dataset_args=settings_rag.dataset_args,
        playground_args=settings_rag.playground_args,
        vector_database_args=settings_rag.vector_database_args,
        llm_blueprint_args=settings_rag.llm_blueprint_args,
        runtime_parameter_values=llm_credential.runtime_parameter_values,
        guard_configurations=guard_configurations,
        custom_model_args=settings_rag.custom_model_args,
    )
elif settings_main.core.rag_type == settings_main.RAGType.DIY:
    if not all(
        [path.exists() for path in settings_rag.diy_rag_nb_output.model_dump().values()]
    ):
        pulumi.info("Executing doc chunking + vdb building notebook...")
        run_notebook(settings_rag.diy_rag_nb)
    else:
        pulumi.info(
            f"Using existing doc chunking + vdb outputs in '{settings_rag.diy_rag_deployment_path}'"
        )

    rag_custom_model = datarobot.CustomModel(  # type: ignore[assignment]
        files=settings_rag.get_diy_rag_files(
            runtime_parameter_values=llm_credential.runtime_parameter_values,
        ),
        runtime_parameter_values=llm_credential.runtime_parameter_values,
        guard_configurations=guard_configurations,
        **settings_rag.custom_model_args.model_dump(mode="json", exclude_none=True),
    )
else:
    raise NotImplementedError(f"Unknown RAG type: {settings_main.core.rag_type}")

rag_deployment = CustomModelDeployment(
    resource_name="rag",
    custom_model_version_id=rag_custom_model.version_id,
    registered_model_args=settings_rag.registered_model_args,
    prediction_environment=prediction_environment,
    deployment_args=settings_rag.deployment_args,
)

grading_deployment = CustomModelDeployment(
    resource_name="grading",
    custom_model_args=settings_grader.custom_model_args,
    registered_model_args=settings_grader.registered_model_args,
    prediction_environment=prediction_environment,
    deployment_args=settings_grader.deployment_args,
)

app_runtime_parameters = [
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=rag_deployment_env_name, type="deployment", value=rag_deployment.id
    ),
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=grading_deployment_env_name, type="deployment", value=grading_deployment.id
    ),
]

if settings_main.core.application_type == settings_main.ApplicationType.DIY:
    application_source = datarobot.ApplicationSource(
        runtime_parameter_values=app_runtime_parameters,
        **settings_app_infra.app_source_args,
    )
    qa_application = datarobot.CustomApplication(
        resource_name=settings_app_infra.app_resource_name,
        name=settings_app_infra.app_name,
        source_version_id=application_source.version_id,
    )
elif settings_main.core.application_type == settings_main.ApplicationType.DR:
    qa_application = datarobot.QaApplication(  # type: ignore[assignment]
        resource_name=settings_app_infra.app_resource_name,
        name=settings_app_infra.app_name,
        deployment_id=rag_deployment.deployment_id,
    )
else:
    raise NotImplementedError(
        f"Unknown application type: {settings_main.core.application_type}"
    )

qa_application.id.apply(settings_app_infra.ensure_app_settings)


pulumi.export(grading_deployment_env_name, grading_deployment.id)
pulumi.export(rag_deployment_env_name, rag_deployment.id)
for deployment, config in zip(global_guard_deployments, global_guardrails):
    pulumi.export(
        config.deployment_args.resource_name + "-url",
        deployment.id.apply(get_deployment_url),
    )
pulumi.export(
    settings_grader.deployment_args.resource_name + "-url",
    grading_deployment.id.apply(get_deployment_url),
)
pulumi.export(
    settings_rag.deployment_args.resource_name + "-url",
    rag_deployment.id.apply(get_deployment_url),
)
pulumi.export(
    settings_app_infra.app_resource_name + "-url",
    qa_application.application_url,
)
