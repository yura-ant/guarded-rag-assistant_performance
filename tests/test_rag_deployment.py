# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

# mypy: ignore-errors

import datetime as dt
import uuid
from docsassist.deployments import RAGDeployment
from docsassist.schema import PROMPT_COLUMN_NAME
import datarobot as dr
import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def rag_deployment_id():
    return RAGDeployment().id


def generate_association_id():
    return f"{uuid.uuid4().hex}_{dt.datetime.now()}"


def extract_references(rag_response_dict):
    if "references" in rag_response_dict:
        return rag_response_dict["references"]

    references = []
    for column in sorted(rag_response_dict.keys()):
        if "CITATION_CONTENT" in column:
            doc = {"page_content": rag_response_dict[column], "metadata": {}}
            source = rag_response_dict[column.replace("CONTENT", "SOURCE")]
            if column.replace("CONTENT", "PAGE") in rag_response_dict:
                page = rag_response_dict[column.replace("CONTENT", "PAGE")]
                doc["metadata"]["source"] = f"{source}, page {page}"
            else:
                doc["metadata"]["source"] = source
            references.append(doc)
    return references


def test_rag_deployment_prediction(pulumi_up, make_prediction, rag_deployment_id):
    prompt_feature_name = PROMPT_COLUMN_NAME
    msg = f"RAG Deployment ID: {rag_deployment_id}"
    logger.info(msg)

    rag_input = [
        {
            prompt_feature_name: "tell me about DataRobot",
            "association_id": generate_association_id(),
        }
    ]
    rag_response_dict = make_prediction(rag_input, rag_deployment_id)

    rag_deployment = dr.Deployment.get(rag_deployment_id)
    rag_response = {
        "answer": rag_response_dict[
            f"{rag_deployment.model['target_name']}_PREDICTION"
        ],
        "references": extract_references(rag_response_dict),
    }
    if "usage" in rag_response_dict:
        rag_response["usage"] = rag_response_dict["usage"]

    assert len(rag_response["answer"]) > 0 and len(rag_response["references"]) > 0
