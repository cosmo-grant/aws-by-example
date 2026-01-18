from textwrap import dedent

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaWhoWhatWhereStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        who_what_where_log_group = logs.LogGroup(
            self,
            "who_what_where_log_group",
            log_group_name="/aws/lambda/who_what_where",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        lambda_.Function(
            self,
            "who_what_where_lambda",
            function_name="who_what_where",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=who_what_where_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    import os
                    import subprocess
                    import time
                    from pathlib import Path

                    def handler(event, context):
                        print(f"{Path.home()=}")
                        print(f"{Path.cwd()=}")
                        print(f"{list(Path(".").glob("*"))=}")
                        print(f"{list(Path("/").glob("*"))=}")

                        try:
                            with open("foobar", "w") as f:
                                f.write("hi")
                        except Exception as err:
                            print(f"Exception writing to a file: {err}")

                        try:
                            subprocess.run("echo this is running via a shell", shell=True, check=True)
                        except subprocess.CalledProcessError as err:
                            print(f"Exception running subprocess via shell: {err}")
                        else:
                            print(f"{os.environ.get("SHELL")=}")
                            subprocess.run(["/bin/sh", "--version"], check=True)

                        print(f"{time.tzname=}")
                    """
                )
            ),
        )
