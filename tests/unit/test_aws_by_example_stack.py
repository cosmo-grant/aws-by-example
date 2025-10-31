import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_by_example.aws_by_example_stack import AwsByExampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_by_example/aws_by_example_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsByExampleStack(app, "aws-by-example")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
