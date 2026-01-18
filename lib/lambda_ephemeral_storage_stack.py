from textwrap import dedent

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaEphemeralStorage(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ephemeral_storage_log_group = logs.LogGroup(
            self,
            "ephemeral_storage_log_group",
            log_group_name="/aws/lambda/ephemeral_storage",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "ephemeral_storage_lambda",
            function_name="ephemeral_storage",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=ephemeral_storage_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    from pathlib import Path

                    def handler(event, context):
                        p = Path("/tmp/foobar")
                        if p.exists():
                            response = f"{p} already exists, so doing nothing"
                        else:
                            with open(p, "w") as f:
                                pass
                            response = f"{p} did not exist, so created it"

                        return response
                    """
                )
            ),
        )
