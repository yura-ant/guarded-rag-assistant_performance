# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import get_args
from docsassist.schema import Grade

CLASS_LABELS = list(get_args(Grade))


# dummy load model function to overwrite the default
def load_model(code_dir):
    return ""


# equal prediction on each class
def score(data, model, **kwargs):
    equal_weight = 1.0 / len(CLASS_LABELS)
    for col in CLASS_LABELS:
        data[col] = equal_weight
    return data[CLASS_LABELS]
