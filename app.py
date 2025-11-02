#!/usr/bin/env python3

import os

import aws_cdk as cdk

from lib.lambda_retries_stack import LambdaRetriesStack

app = cdk.App()

LambdaRetriesStack(
    app,
    "LambdaRetriesStack",
    env=cdk.Environment(account=os.environ["ACCOUNT_ID"], region=os.environ["REGION"]),
)

app.synth()
