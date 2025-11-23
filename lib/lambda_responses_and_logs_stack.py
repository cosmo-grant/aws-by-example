from textwrap import dedent

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaResponsesAndLogsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        slow_init_log_group = logs.LogGroup(
            self,
            "slow_init_log_group",
            log_group_name="/aws/lambda/slow_init",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "slow_init_lambda",
            function_name="slow_init",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=slow_init_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    from time import sleep

                    sleep(4)

                    def handler(event, context):
                        return "hi there"
                    """
                )
            ),
        )

        init_exception_log_group = logs.LogGroup(
            self,
            "init_exception_log_group",
            log_group_name="/aws/lambda/init_exception",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "init_exception_lambda",
            function_name="init_exception",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=init_exception_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    raise Exception("uh oh")

                    def handler(event, context):
                        pass
                    """
                )
            ),
        )

        handler_exception_log_group = logs.LogGroup(
            self,
            "handler_exception_log_group",
            log_group_name="/aws/lambda/handler_exception",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "handler_exception_lambda",
            function_name="handler_exception",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=handler_exception_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    def handler(event, context):
                        raise Exception("uh oh")
                    """
                )
            ),
        )

        init_times_out_log_group = logs.LogGroup(
            self,
            "init_times_out_log_group",
            log_group_name="/aws/lambda/init_times_out",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "init_times_out_lambda",
            function_name="init_times_out",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=init_times_out_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    from time import sleep

                    sleep(11)

                    def handler(event, context):
                        pass
                    """
                )
            ),
        )

        handler_times_out_log_group = logs.LogGroup(
            self,
            "handler_times_out_log_group",
            log_group_name="/aws/lambda/handler_times_out",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "handler_times_out_lambda",
            function_name="handler_times_out",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(3),
            log_group=handler_times_out_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    from time import sleep

                    def handler(event, context):
                        sleep(4)
                    """
                )
            ),
        )

        handler_returns_unserializable_log_group = logs.LogGroup(
            self,
            "handler_returns_unserializable_log_group",
            log_group_name="/aws/lambda/handler_returns_unserializable",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "handler_returns_unserializable_lambda",
            function_name="handler_returns_unserializable",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            timeout=Duration.seconds(3),
            log_group=handler_returns_unserializable_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    def handler(event, context):
                        return set()
                    """
                )
            ),
        )

        init_plus_handler_exceeds_timeout_log_group = logs.LogGroup(
            self,
            "init_plus_handler_exceeds_timeout_log_group",
            log_group_name="/aws/lambda/init_plus_handler_exceeds_timeout",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "init_plus_handler_exceeds_timeout_lambda",
            function_name="init_plus_handler_exceeds_timeout",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=init_plus_handler_exceeds_timeout_log_group,
            timeout=Duration.seconds(3),
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    from time import sleep

                    sleep(2)

                    def handler(event, context):
                        sleep(2)
                    """
                )
            ),
        )
