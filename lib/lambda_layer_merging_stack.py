from pathlib import Path
from textwrap import dedent

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct


class LambdaLayerMergingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        layer_merging_log_group = logs.LogGroup(
            self,
            "layer_merging_log_group",
            log_group_name="/aws/lambda/layer_merging",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        requests_2_30_layer = lambda_.LayerVersion(
            self,
            "requests_2_30_layer",
            code=lambda_.Code.from_asset(str(Path(__file__).parent / "resources" / "layers" / "requests-2-30")),
            description="A layer containing requests 2.30 and a sentinel file.",
        )
        requests_2_31_layer = lambda_.LayerVersion(
            self,
            "requests_2_31_layer",
            code=lambda_.Code.from_asset(str(Path(__file__).parent / "resources" / "layers" / "requests-2-31")),
            description="A layer containing requests 2.31 and a sentinel file.",
        )
        lambda_.Function(
            self,
            "layer_merging_lambda",
            function_name="layer_merging",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            layers=[requests_2_31_layer, requests_2_30_layer],  # order is for making a point
            log_group=layer_merging_log_group,
            code=lambda_.Code.from_inline(
                dedent(
                    """\
                    import os
                    import subprocess
                    import sys

                    import requests


                    def handler(event, context):
                        print(f"{os.environ.get("PYTHONPATH")=}")  # used to add dirs to module search path
                        print(f"{sys.path=}")  # module search path

                        # layers are extracted into /opt
                        p1 = subprocess.run(["ls", "/opt"], text=True, capture_output=True, check=True)
                        print("/opt listing:\\n", p1.stdout.split())
                        p2 = subprocess.run(["ls", "/opt/python"], text=True, capture_output=True, check=True)
                        print("/opt/python listing:\\n", p2.stdout.split())

                        print("imported requests version:", requests.__version__)
                    """
                )
            ),
        )
