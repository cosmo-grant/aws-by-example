#!/usr/bin/env python3

import os

import aws_cdk as cdk

from lib.lambda_responses_and_logs_stack import LambdaResponsesAndLogsStack
from lib.lambda_retries_stack import LambdaRetriesStack
from lib.sns_publish_permissions_stack import SnsPublishPermissionsStack

app = cdk.App()
env = cdk.Environment(account=os.environ["ACCOUNT_ID"], region=os.environ["REGION"])

LambdaRetriesStack(
    app,
    "LambdaRetriesStack",
    env=env,
)

SnsPublishPermissionsStack(
    app,
    "SnsPublishPermissionsStack",
    env=env,
)

LambdaResponsesAndLogsStack(
    app,
    "LambdaResponsesAndLogsStack",
    env=env,
)

app.synth()
