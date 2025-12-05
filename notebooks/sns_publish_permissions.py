import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # SNS Publish Permissions
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    When Bad Thing happens, aws puts an event onto our event bus.
    We have an eventbridge rule to publish the event to an sns topic so that we get emailed.
    But no email arrived.
    How come?

    The rule's metrics show a failed invocation.
    So the event was emitted and matched the rule,
    but the rule failed to publish to the topic.

    We have a cloudwatch alarm which publishes to that topic too.
    We _do_ get emails when the alarm goes off.
    So the alarm is working as expected but not the rule.

    We set up the alarm and the rule via cdk.
    We import the topic, created elsewhere, into the stack via the `from_topic_arn` method.
    We configure the rule to publish to the topic via the `Rule` construct's `add_target` method.
    We configure the alarm to publish to the topic via the `Alarm` construct's `add_alarm_action` method.
    Similar, yet the alarm works and the rule doesn't.

    Maybe a permissions issue?
    Does it matter that the topic was imported, not created?
    What are the default permissions?
    How do the cdk methods modify them?

    I'll investigate using a simple stack.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Stack
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid(
        """
    graph LR
        Z1:::hidden -->|invoking| A[noop λ]
        A -->|triggers| B[alarm]
        B -->|publishes to| C[pre-existing topic]
        C -->|invokes| D[target λ]

        Z2:::hidden -->|putting| E[event] 
        E -->|matches| F[rule]
        F -->|publishes to| G[topic]
        G -->|invokes| H[target λ]

        B -->|publishes to| G
        F -->|publishes to| C

    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Investigation
    """)
    return


@app.cell
def _():
    from datetime import datetime, timezone

    import boto3

    lambda_ = boto3.client("lambda")
    events = boto3.client("events")
    return boto3, datetime, events, lambda_, timezone


@app.cell
def _(datetime, events, lambda_, timezone):
    start_time = datetime.now(timezone.utc)
    invoke_response = lambda_.invoke(FunctionName="noop")
    put_events_response = events.put_events(
        Entries=[
            {
                "Source": "my_source",
                "DetailType": "my_detail_type",
                "Detail": "{}",
            },
        ]
    )
    return invoke_response, put_events_response, start_time


@app.cell
def _(start_time):
    start_time
    return


@app.cell
def _(invoke_response):
    assert invoke_response["StatusCode"] == 200
    return


@app.cell
def _(put_events_response):
    assert put_events_response["FailedEntryCount"] == 0
    return


@app.cell
def _(mo):
    mo.md(r"""
    Which topics did the alarm and rule successfully publish to?
    We'll wait a bit then check the target lambdas.
    """)
    return


@app.cell
def _():
    import time

    time.sleep(4 * 60)
    return


@app.cell
def _(boto3):
    cloudwatch = boto3.client("cloudwatch")
    return (cloudwatch,)


@app.cell
def _(cloudwatch, datetime, start_time, timezone):
    cloudwatch.get_metric_statistics(
        MetricName="Invocations",
        Namespace="AWS/Lambda",
        Dimensions=[{"Name": "FunctionName", "Value": "pre_existing_topic_target"}],
        StartTime=start_time,
        EndTime=datetime.now(timezone.utc),
        Statistics=["Sum"],
        Period=60,
    )["Datapoints"]
    return


@app.cell
def _(cloudwatch, datetime, start_time, timezone):
    cloudwatch.get_metric_statistics(
        MetricName="Invocations",
        Namespace="AWS/Lambda",
        Dimensions=[{"Name": "FunctionName", "Value": "topic_target"}],
        StartTime=start_time,
        EndTime=datetime.now(timezone.utc),
        Statistics=["Sum"],
        Period=60,
    )["Datapoints"]
    return


@app.cell
def _(mo):
    mo.md(r"""
    For the pre-existing topic and for the new topic, one publish succeeded and the other failed. Which?
    """)
    return


@app.cell
def _(cloudwatch, datetime, start_time, timezone):
    cloudwatch.describe_alarm_history(
        StartDate=start_time,
        EndDate=datetime.now(timezone.utc),
        AlarmName="noop_lambda_invocation_alarm",
    )["AlarmHistoryItems"]
    return


@app.cell
def _(mo):
    mo.md(r"""
    Cloudwatch published ok to the pre-existing topic but failed to publish to the new topic because

    > CloudWatch Alarms is not authorized to perform: SNS:Publish on resource:arn:aws:sns:eu-west-2:872115063659:my_topic

    That means eventbridge published ok to the new topic but not to the pre-existing topic.

    What are the topic permissions?
    """)
    return


@app.cell
def _(boto3):
    import json
    from os import environ

    sns = boto3.client("sns")
    return environ, json, sns


@app.cell
def _(environ, json, sns):
    _ = sns.get_topic_attributes(TopicArn=f"arn:aws:sns:{environ['REGION']}:{environ['ACCOUNT_ID']}:pre_existing_topic")
    json.loads(_["Attributes"]["Policy"])
    return


@app.cell
def _(mo):
    mo.md(r"""
    Based on the `Id`, this must be a topic's default access policy.

    And it must be that cloudwatch satisfies the `AWS:SourceOwner` condition and eventbridge doesn't.
    """)
    return


@app.cell
def _(environ, json, sns):
    _ = sns.get_topic_attributes(TopicArn=f"arn:aws:sns:{environ['REGION']}:{environ['ACCOUNT_ID']}:my_topic")
    json.loads(_["Attributes"]["Policy"])
    return


@app.cell
def _(mo):
    mo.md(r"""
    Ok, that's clear: eventbridge has permission to publish to the new topic and cloudwatch does not.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    How come these permissions?
    Here's what I think has happened.

    I created the new topic in the stack,
    and added subscriptions via `add_target` and `add_alarm_action`.
    `add_target` modifies the access policy, permitting eventbridge.
    But `add_alarm_action` does not:
    you have to give cloudwatch permission yourself.
    That's the **first surprise**.

    The **second surprise** is that `add_target` doesn't add permissions
    on top of the default `AWS:SourceOwner` policy.
    Instead, it replaces the default policy.
    The docs make this clear for `add_to_resource_policy`:

    > If this topic was created in this stack (`new Topic`), a topic policy will be automatically created upon the first call to `addToResourcePolicy`.

    and I suppose it's implicit that the same applies to other permissions-changing methods,
    such as `add_target`.

    I created the pre-existing topic in another stack, with all defaults.
    It has the default policy based on `AWS:SourceOwner`.
    I imported the topic into the stack via `from_topic_arn`,
    then added subscriptions via `add_target` and `add_alarm_action`.
    Because the topic was imported,
    neither method changed the access policy.
    But — **third surprise** — cloudwatch passes the policy and events doesn't.

    A **fourth surprise**.
    It makes sense that the cdk methods didn't change the pre-existing topic's policy.
    It would be confusing if stacks could modify resources they didn't create.
    Except sometimes they do!
    For example, in our stack we _were_ able to add the target lambda subscription to the pre-existing topic.
    So cdk _doesn't_ strictly observe the "stacks can't modify resources they didn't create" rule.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## References

    [1] https://docs.aws.amazon.com/sns/latest/dg/sns-access-policy-use-cases.html#sns-allow-specified-service-to-publish-to-topic

    Confirms that cloudwatch supports `AWS:SourceOwner` and eventbridge does not.

    Warns that

    > `aws:SourceOwner` is deprecated and new services can integrate with Amazon SNS
    > only through `aws:SourceArn` and `aws:SourceAccount`.
    > Amazon SNS still maintains backward compatibility for existing services
    > that are currently supporting `aws:SourceOwner`.

    "Maintains backward compatibility" seems to go as far as using `aws:SourceOwner` in the default policy.

    [2] https://github.com/awsdocs/iam-user-guide/issues/111

    AWS say they're not going to document `SourceOwner` because deprecated.
    Ok, but then, as one of the comments says, why keep using it in the default policy?

    [3] https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html#aws_cdk.aws_sns.Topic.add_to_resource_policy
    """)
    return


if __name__ == "__main__":
    app.run()
