# WARN: remember to destroy this stack!

from textwrap import dedent

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaScaleFromZeroStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        scale_from_zero_log_group = logs.LogGroup(
            self,
            "ScaleFromZeroLogGroup",
            log_group_name="/aws/lambda/scale_from_zero",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        scale_from_zero = lambda_.Function(
            self,
            "ScaleFromZeroLambda",
            function_name="scale_from_zero",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(300),
            log_group=scale_from_zero_log_group,
            # Sleep long so one invocation is enough to provoke the policy.
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(240)
                    """
                ).strip(),
            ),
        )

        # auto scaling can't target $LATEST, so we need an alias
        scale_from_zero_alias = lambda_.Alias(
            self,
            "ScaleFromZeroAlias",
            alias_name="live",
            version=scale_from_zero.current_version,
        )

        scale_from_zero_target = scale_from_zero_alias.add_auto_scaling(
            min_capacity=0,
            max_capacity=2,
        )
        scale_from_zero_target.scale_on_utilization(utilization_target=0.5)

        scale_from_one_log_group = logs.LogGroup(
            self,
            "ScaleFromOneLogGroup",
            log_group_name="/aws/lambda/scale_from_one",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        scale_from_one = lambda_.Function(
            self,
            "ScaleFromOneLambda",
            function_name="scale_from_one",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(300),
            log_group=scale_from_one_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(240)
                    """
                ).strip(),
            ),
        )

        scale_from_one_alias = lambda_.Alias(
            self,
            "ScaleFromOneAlias",
            alias_name="live",
            version=scale_from_one.current_version,
        )

        scale_from_one_target = scale_from_one_alias.add_auto_scaling(
            min_capacity=1,  # WARN: remember to tear down the stack!
            max_capacity=2,
        )
        scale_from_one_target.scale_on_utilization(utilization_target=0.5)
