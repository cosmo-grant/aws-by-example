from textwrap import dedent

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaRetriesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # the duplicate constructs (async* and sync*) are so i can compare sync and async invocations
        # in parallel without them interfering with each other
        # the async and sync prefixes just indicate how i will call them, nothing about the construct itself

        # a log group is created automatically for a lambda
        # but that log group is not configurable (e.g. you should not set its removal policy)
        # so the docs recommend creating your own and passing it to your lambda
        async_handler_raises_exception_log_group = logs.LogGroup(
            self,
            "AsyncHandlerRaisesExceptionLogGroup",
            log_group_name="/aws/lambda/async_handler_raises_exception",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,  # as a precaution to save $, in case i forget to destroy the stack
        )

        lambda_.Function(
            self,
            "AsyncHandlerRaisesExceptionLambda",
            function_name="async_handler_raises_exception",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=async_handler_raises_exception_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    def handler(event, context):
                        raise Exception
                    """
                ).strip(),
            ),
        )

        sync_handler_raises_exception_log_group = logs.LogGroup(
            self,
            "SyncHandlerRaisesExceptionLogGroup",
            log_group_name="/aws/lambda/sync_handler_raises_exception",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,  # as a precaution to save $, in case i forget to destroy the stack
        )

        lambda_.Function(
            self,
            "SyncHandlerRaisesExceptionLambda",
            function_name="sync_handler_raises_exception",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=sync_handler_raises_exception_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    def handler(event, context):
                        raise Exception
                    """
                ).strip(),
            ),
        )

        async_invocation_times_out_log_group = logs.LogGroup(
            self,
            "AsyncInvocationTimesOutLogGroup",
            log_group_name="/aws/lambda/async_invocation_times_out",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "AsyncInvocationTimesOutLambda",
            function_name="async_invocation_times_out",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(1),
            handler="index.handler",
            log_group=async_invocation_times_out_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(2)
                    """
                ).strip(),
            ),
        )

        sync_invocation_times_out_log_group = logs.LogGroup(
            self,
            "SyncInvocationTimesOutLogGroup",
            log_group_name="/aws/lambda/sync_invocation_times_out",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "SyncInvocationTimesOutLambda",
            function_name="sync_invocation_times_out",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(1),
            handler="index.handler",
            log_group=sync_invocation_times_out_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(2)
                    """
                ).strip(),
            ),
        )

        async_throttled_log_group = logs.LogGroup(
            self,
            "AsyncThrottledLogGroup",
            log_group_name="/aws/lambda/async_throttled",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        # we'll arrange throttling after deploying
        # the long sleep is explained in the notebook
        lambda_.Function(
            self,
            "AsyncThrottledLambda",
            function_name="async_throttled",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(61),
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(60)
                    """
                ).strip(),
            ),
            log_group=async_throttled_log_group,
        )

        sync_throttled_log_group = logs.LogGroup(
            self,
            "SyncThrottledLogGroup",
            log_group_name="/aws/lambda/sync_throttled",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        # we'll arrange throttling after deploying
        # the long sleep is explained in the notebook
        lambda_.Function(
            self,
            "SyncThrottledLambda",
            function_name="sync_throttled",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(11),
            code=lambda_.Code.from_inline(
                dedent(
                    """
                    from time import sleep

                    def handler(event, context):
                        sleep(10)
                    """
                ).strip(),
            ),
            log_group=sync_throttled_log_group,
        )
