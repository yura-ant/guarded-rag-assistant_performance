# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import pulumi_datarobot as datarobot
from pydantic import BaseModel

from .common.globals import (
    GlobalGuardrailTemplateName,
    GlobalRegisteredModelName,
)
from .common.schema import (
    Condition,
    CustomModelGuardConfigurationArgs,
    DeploymentArgs,
    GuardConditionComparator,
    Intervention,
    ModerationAction,
    Stage,
)
from .settings_main import default_prediction_server_id


class GlobalGuardrail(BaseModel):
    name: str
    deployment_args: DeploymentArgs
    registered_model_name: GlobalRegisteredModelName
    custom_model_guard_configuration_args: CustomModelGuardConfigurationArgs


toxicity = GlobalGuardrail(
    name="toxicity-guard",
    deployment_args=DeploymentArgs(
        resource_name="toxicity-guard-deployment",
        label="Toxicity Guard Deployment",
        predictions_settings=None
        if default_prediction_server_id
        else datarobot.DeploymentPredictionsSettingsArgs(
            min_computes=0, max_computes=1, real_time=True
        ),
    ),
    registered_model_name=GlobalRegisteredModelName.TOXICITY,
    custom_model_guard_configuration_args=CustomModelGuardConfigurationArgs(
        name="Toxicity Guard Configuration",
        template_name=GlobalGuardrailTemplateName.TOXICITY,
        stages=[Stage.PROMPT],
        intervention=Intervention(
            action=ModerationAction.BLOCK,
            condition=Condition(
                comparand=0.7,
                comparator=GuardConditionComparator.GREATER_THAN,
            ).model_dump_json(),
            message="I have detected that your question contains toxic language. Please rephrase your question.",
        ),
    ),
)

prompt_injection = GlobalGuardrail(
    name="prompt-injection-guard",
    deployment_args=DeploymentArgs(
        resource_name="prompt-injection-guard-deployment",
        label="Prompt Injection Guard Deployment",
        predictions_settings=None
        if default_prediction_server_id
        else datarobot.DeploymentPredictionsSettingsArgs(
            min_computes=0, max_computes=1, real_time=True
        ),
    ),
    registered_model_name=GlobalRegisteredModelName.PROMPT_INJECTION,
    custom_model_guard_configuration_args=CustomModelGuardConfigurationArgs(
        name="Prompt Injection Guard Configuration",
        template_name=GlobalGuardrailTemplateName.PROMPT_INJECTION,
        stages=[Stage.PROMPT],
        intervention=Intervention(
            action=ModerationAction.BLOCK,
            condition=Condition(
                comparand=0.7,
                comparator=GuardConditionComparator.GREATER_THAN,
            ).model_dump_json(),
            message="I have detected that your question contains a prompt injection. Please rephrase your question.",
        ),
    ),
)


global_guardrails = [toxicity, prompt_injection]
