import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Lambda Scale From Zero

    You can auto-scale provisioned concurrency via a scaling policy,
    say "scale out to at most 100, trying to keep provisioned concurrency utilization at 50%".
    That way, you have enough warm environments for the current load (the in-use 50%),
    and are ready for spikes (the spare 50%),
    without being wasteful (it scales in too),
    or risking breaking the bank (max 100).

    Lambda achieves this by emitting a `ProvisionedConcurrencyUtilization` metric, and scaling provisioned concurrency to keep the metric near the target.

    `ProvisionedConcurrencyUtilization` is defined as

    >The percentage of provisioned concurrency in use (i.e. the value of
    >`ProvisionedConcurrentExecutions` divided by the total amount of provisioned concurrency allocated).

    where `ProvisionedConcurrentExecutions` is

    >The number of execution environment instances that are actively processing an invocation on provisioned concurrency.

    But what if the denominator — allocated provisioned concurrency — is 0?
    Will the metric be emitted?
    Will Lambda scale provisioned concurrency?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stack

    Two lambdas, `scale_from_zero` and `scale_from_one`, with "live" aliases, which sleep for a while.

    Both have auto-scaling policies designed to keep utilization at 50% with max capacity 2.
    But `scale_from_zero` has `min_capacity=0` and `scale_from_one` has `min_capacity=1`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Results
    """)
    return


@app.cell
def _():
    import datetime
    import time
    import boto3

    lambda_ = boto3.client("lambda")
    cloudwatch = boto3.client("cloudwatch")
    appscaling = boto3.client("application-autoscaling")
    return appscaling, cloudwatch, datetime, lambda_, time


@app.cell
def _(lambda_):
    def get_provisioned_concurrency(function_name):
        try:
            return lambda_.get_provisioned_concurrency_config(FunctionName=function_name, Qualifier="live")
        except lambda_.exceptions.ProvisionedConcurrencyConfigNotFoundException:
            return "<no provisioned concurrency>"
    return (get_provisioned_concurrency,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's check provisioned concurrency _before_ provoking auto-scaling.
    """)
    return


@app.cell
def _(get_provisioned_concurrency):
    get_provisioned_concurrency("scale_from_zero")
    return


@app.cell
def _(get_provisioned_concurrency):
    get_provisioned_concurrency("scale_from_one")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now let's provoke the scaling policies.

    The docs are a bit cagey about what it takes to provoke a policy.
    [1] has the clearest statement I could find:

    >Both of the Application Auto Scaling alarms use the average statistic by default.
    >Functions that experience quick bursts of traffic may not trigger these alarms.
    >For example, suppose your Lambda function executes quickly (i.e. 20-100 ms) and your traffic comes in quick bursts.
    >In this case, the number of requests exceeds the allocated provisioned concurrency during the burst.
    >However, Application Auto Scaling requires the burst load to sustain for at least 3 minutes in order to provision additional environments.
    >Additionally, both CloudWatch alarms require 3 data points that hit the target average to activate the auto scaling policy.

    "_At least_ 3 minutes"?

    To be on the safe side, our lambdas sleep for _4_ minutes.
    So one invocation should be enough to provoke scaling, if it can be provoked.

    Let's go.
    """)
    return


@app.cell
def _(datetime, lambda_, time):
    start_time = datetime.datetime.now(datetime.UTC)

    # Provisioned concurrency attaches to aliases, not function versions.
    # Hit the "live" alias so the invocations use the alias's provisioned concurrency.
    lambda_.invoke(FunctionName="scale_from_zero", Qualifier="live", InvocationType="Event")
    lambda_.invoke(FunctionName="scale_from_one", Qualifier="live", InvocationType="Event")

    # Wait for the executions to complete plus a bit extra to allow Lambda time to scale out.
    time.sleep(360)
    return (start_time,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we'll fetch provisioned concurrency again.
    """)
    return


@app.cell
def _(get_provisioned_concurrency):
    get_provisioned_concurrency("scale_from_zero")
    return


@app.cell
def _(get_provisioned_concurrency):
    get_provisioned_concurrency("scale_from_one")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Lambda **did not** `scale_from_zero` (the policy had no effect), but (sanity check) **did** `scale_from_one`.

    **Target-tracking on provisioned concurrency utilization gets stuck when no provisioned concurrency.**

    Let's dig deeper into the mechanism.
    """)
    return


@app.cell
def _(cloudwatch, datetime, start_time):
    def get_utilization(function_name):
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="ProvisionedConcurrencyUtilization",
            Dimensions=[
                {"Name": "FunctionName", "Value": function_name},
                {"Name": "Resource", "Value": f"{function_name}:live"},
            ],
            StartTime=start_time,
            EndTime=datetime.datetime.now(datetime.UTC),
            Period=60,
            Statistics=["Maximum"],  # The docs say "View this metric using MAX".
        )
        return sorted(
            ((datapoint["Maximum"], datapoint["Timestamp"]) for datapoint in response["Datapoints"]),
            key=lambda dp: dp[1],
        )
    return (get_utilization,)


@app.cell
def _(get_utilization):
    get_utilization("scale_from_zero")
    return


@app.cell
def _(get_utilization):
    get_utilization("scale_from_one")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **When there is no provisioned concurrency, CloudWatch doesn't emit the `ProvisionedConcurrencyUtilization` metric.**

    Application Auto Scaling implements target-tracking via two alarms:
    an `AlarmHigh` that triggers scale-out
    and an `AlarmLow` that triggers scale-in.
    How do they treat missing data?
    """)
    return


@app.cell
def _(appscaling, cloudwatch):
    def get_scaling_alarms(function_name):
        # The scaling policy, not Lambda, owns the alarms.
        policies = appscaling.describe_scaling_policies(
            ServiceNamespace="lambda",
            ResourceId=f"function:{function_name}:live",
        )["ScalingPolicies"]
        alarm_names = [alarm["AlarmName"] for policy in policies for alarm in policy["Alarms"]]
        alarms = cloudwatch.describe_alarms(AlarmNames=alarm_names)["MetricAlarms"]
        return [
            {
                "name": alarm["AlarmName"],
                "state": alarm["StateValue"],
                "treat_missing_data": alarm.get("TreatMissingData"),
            }
            for alarm in alarms
        ]
    return (get_scaling_alarms,)


@app.cell
def _(get_scaling_alarms):
    get_scaling_alarms("scale_from_zero")
    return


@app.cell
def _(get_scaling_alarms):
    get_scaling_alarms("scale_from_one")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `"treat_missing_data": None`, so the alarms fall back on the default setting `missing` [3], so **no metric emitted doesn't trigger the alarm.**
    That's the mechanism.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And after all that I spotted this note [3]:

    >If you use Application Auto Scaling to manage your function's provisioned concurrency,
    >ensure that you configure an initial provisioned concurrency value first.
    >If your function doesn't have an initial provisioned concurrency value,
    >Application Auto Scaling may not handle function scaling properly.

    Still, it's good to verify directly and understand the mechanism.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## References

    [1] https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html

    [2] https://docs.aws.amazon.com/lambda/latest/dg/monitoring-concurrency.html

    [3] https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
