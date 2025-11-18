from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from constructs import Construct


class SnsPublishPermissionsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # this topic is created outside this stack
        pre_existing_topic = sns.Topic.from_topic_arn(
            self,
            "PreExistingTopic",
            f"arn:aws:sns:{Stack.of(self).region}:{Stack.of(self).account}:pre_existing_topic",
        )

        # the target lambdas' are merely sns targets: one for the pre-existing topic and one for the new topic
        # it's convenient to use a lambda for this (over, say, email) because we can easily check delivery
        # we set up the log group separately so we can configure the removal policy
        pre_existing_topic_target_lambda_log_group = logs.LogGroup(
            self,
            "PreExistingTopicTargetLambdaLogGroup",
            log_group_name="/aws/lambda/pre_existing_topic_target",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        pre_existing_topic_target_lambda = lambda_.Function(
            self,
            "PreExistingTopicTargetLambda",
            function_name="pre_existing_topic_target",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=pre_existing_topic_target_lambda_log_group,
            code=lambda_.Code.from_inline("def handler(event, context): pass"),
        )

        topic_target_lambda_log_group = logs.LogGroup(
            self,
            "TopicTargetLambdaLogGroup",
            log_group_name="/aws/lambda/topic_target",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        topic_target_lambda = lambda_.Function(
            self,
            "TopicTargetLambda",
            function_name="topic_target",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=topic_target_lambda_log_group,
            code=lambda_.Code.from_inline("def handler(event, context): pass"),
        )

        # this adds the subscription, and updates the target lambda's resource policy to allow the topic to invoke it
        # i'm surprised you can modify resources defined outside the stack
        pre_existing_topic.add_subscription(subscriptions.LambdaSubscription(pre_existing_topic_target_lambda))

        topic = sns.Topic(
            self,
            "MyTopic",
            topic_name="my_topic",
        )
        topic.apply_removal_policy(policy=RemovalPolicy.DESTROY)
        topic.add_subscription(subscriptions.LambdaSubscription(topic_target_lambda))

        # we will put a matching event to eventbridge manually
        rule = events.Rule(
            self,
            "MyRule",
            event_pattern=events.EventPattern(
                source=["my_source"],
            ),
            rule_name="my_rule",
        )
        rule.add_target(targets.SnsTopic(topic))  # DOES change the access policy
        rule.add_target(targets.SnsTopic(pre_existing_topic))  # DOES NOT change the access policy

        # we want to test if cloudwatch can publish to the sns topics
        # so create an alarm based on a noop lambda, and have the alarm try to publish to the topic
        noop_lambda_log_group = logs.LogGroup(
            self,
            "NoopLogGroup",
            log_group_name="/aws/lambda/noop",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_DAY,
        )

        noop_lambda = lambda_.Function(
            self,
            "NoopLambda",
            function_name="noop",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=noop_lambda_log_group,
            code=lambda_.Code.from_inline("def handler(event, context): pass"),
        )

        lambda_invocations_alarm = cloudwatch.Alarm(
            self,
            "NoopLambdaInvocationAlarm",
            alarm_name="noop_lambda_invocation_alarm",
            metric=noop_lambda.metric_invocations(period=Duration.minutes(1)),
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
        )

        lambda_invocations_alarm.add_alarm_action(cloudwatch_actions.SnsAction(topic))
        lambda_invocations_alarm.add_alarm_action(cloudwatch_actions.SnsAction(pre_existing_topic))
