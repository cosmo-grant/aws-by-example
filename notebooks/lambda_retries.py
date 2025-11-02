import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Lambda Retries

    When a lambda function invocation fails, does the Lambda service retry?
    How often, and with what backoff?
    Does it depend on the invocation type (synchronous or asynchronous) or the failure reason (timeout, exception, throttling)?

    Let's find out.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Deploy stack

    `lib/lambda_retries_stack.py` describes the lambdas we'll deploy.

    Export `ACCOUNT_ID` and `REGION` environment variables for your account.

    Then:
    """)
    return


@app.cell
def _():
    import subprocess
    from pathlib import Path
    return Path, subprocess


@app.cell
def _(Path):
    repo_root = Path(__file__).parent.parent
    return (repo_root,)


@app.cell
def _(repo_root, subprocess):
    # deploy from repo root so cdk.json is found
    subprocess.run(
        ["cdk", "deploy", "--require-approval=never", "LambdaRetriesStack"],
        check=True,
        cwd=repo_root,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Set up boto3 clients

    We'll use boto3 to invoke and monitor the functions.

    But boto3 automatically retries for certain errors, such as `ThrottlingException`, by default [1].
    We don't want boto3 to retry: it would confuse things.
    (Was this function invoked twice because boto3 retried or because Lambda retried?)
    So let's disable.
    """)
    return


@app.cell
def _():
    import boto3
    import botocore
    return boto3, botocore


@app.cell
def _(boto3, botocore):
    config = botocore.config.Config(retries={"total_max_attempts": 1})
    logs = boto3.client("logs", config=config)
    lambda_ = boto3.client("lambda", config=config)
    cloudwatch = boto3.client("cloudwatch", config=config)
    return cloudwatch, lambda_, logs


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Throttle

    Two of the lambdas we've deployed are for checking retries given throttling.
    So throttle them.
    """)
    return


@app.cell
def _(lambda_):
    lambda_.put_function_concurrency(
        FunctionName="async_throttled",
        ReservedConcurrentExecutions=0,
    )
    return


@app.cell
def _(lambda_):
    lambda_.put_function_concurrency(
        FunctionName="sync_throttled",
        ReservedConcurrentExecutions=0,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Invoke the functions
    """)
    return


@app.cell
def _():
    import datetime
    return (datetime,)


@app.cell
def _():
    call_times = {}
    return (call_times,)


@app.cell
def _(call_times, datetime, lambda_):
    call_times["async_handler_raises_exception"] = datetime.datetime.now(datetime.UTC)
    lambda_.invoke(FunctionName="async_handler_raises_exception", InvocationType="Event")
    return


@app.cell
def _(call_times, datetime, lambda_):
    call_times["async_invocation_times_out"] = datetime.datetime.now(datetime.UTC)
    lambda_.invoke(FunctionName="async_invocation_times_out", InvocationType="Event")
    return


@app.cell
def _(call_times, datetime, lambda_):
    call_times["async_throttled"] = datetime.datetime.now(datetime.UTC)
    # async invocation so we don't get TooManyRequestsException
    lambda_.invoke(FunctionName="async_throttled", InvocationType="Event")
    return


@app.cell
def _(call_times, datetime, lambda_):
    call_times["sync_handler_raises_exception"] = datetime.datetime.now(datetime.UTC)
    lambda_.invoke(FunctionName="sync_handler_raises_exception", InvocationType="RequestResponse")
    return


@app.cell
def _(call_times, datetime, lambda_):
    call_times["sync_invocation_times_out"] = datetime.datetime.now(datetime.UTC)
    lambda_.invoke(FunctionName="sync_invocation_times_out", InvocationType="RequestResponse")
    return


@app.cell
def _(botocore, call_times, datetime, lambda_):
    call_times["sync_throttled"] = datetime.datetime.now(datetime.UTC)
    try:
        lambda_.invoke(FunctionName="sync_throttled", InvocationType="RequestResponse")
    except botocore.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "TooManyRequestsException":
            print("Sync invocation so got TooManyRequestsException")
        else:
            raise err
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Investigate retries

    What retries we find depends on how long we wait after invoking.
    So best to wait a few minutes before continuing.

    We'll `assert` some things about the results conditional on having waited long enough.

    We'll use the logs to find function invocations, since logs have high resolution timestamps.
    """)
    return


@app.cell
def _():
    from pprint import pprint
    return (pprint,)


@app.cell
def _(call_times, datetime, logs):
    def get_invocations_from_logs(function_name: str) -> list[float]:
        call_timestamp_in_ms = int(call_times[function_name].timestamp()) * 1000

        response = logs.filter_log_events(
            logGroupName=f"/aws/lambda/{function_name}",
            startTime=call_timestamp_in_ms,
        )

        invocations = [
            datetime.datetime.fromtimestamp(event["timestamp"] / 1000.0, tz=datetime.UTC)
            for event in response["events"]
            if event["message"].startswith("START")  # the first START will probably be a moment after the boto3 call, because of init time
        ]
        invocations = sorted(invocations)

        return invocations
    return (get_invocations_from_logs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### asynchronous, errors
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    First, a sanity check.
    """)
    return


@app.cell
def _(call_times, datetime, get_invocations_from_logs):
    call_time = call_times["async_handler_raises_exception"]
    print("call time:", call_time)

    first_invocation_time_from_logs = get_invocations_from_logs("async_handler_raises_exception")[0]
    print("first invocation time:", first_invocation_time_from_logs)

    assert call_time <= first_invocation_time_from_logs <= call_time + datetime.timedelta(seconds=3), "First invocation time not in expected range"
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So what's the retry behaviour for async invocations where the function errors?

    We can eyeball the retries directly.
    How many invocations you find depends on when you run the cell.
    """)
    return


@app.cell
def _(get_invocations_from_logs, pprint):
    pprint(get_invocations_from_logs("async_handler_raises_exception"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The docs [4] say the retry behaviour in this case is: try, about 1 minute wait, try, about 2 minute wait, try.

    So let's `assert` that.
    """)
    return


@app.cell
def _(call_times, datetime, get_invocations_from_logs):
    def assert_three_tries_with_approx_one_and_two_minute_waits(function_name: str) -> None:
        call_time = call_times[function_name]
        wiggle = 15
        if datetime.datetime.now(datetime.UTC) <= call_time + datetime.timedelta(minutes=3, seconds=wiggle):
            print("Too soon! Skipping asserts. Try re-running in a few minutes.")
            return

        print("boto3 call time:")
        print(f"\t{call_times[function_name]}")
        invocations = get_invocations_from_logs(function_name)
        print("function invocation times:")
        for invocation_time in invocations:
            print(f"\t{invocation_time}")

        assert len(invocations) == 3, f"Expected 3 invocations but found {len(invocations)}"
        first_invocation_time, second_invocation_time, third_invocation_time = invocations
        assert call_time - datetime.timedelta(seconds=wiggle) <= first_invocation_time <= call_time + datetime.timedelta(seconds=wiggle), "First invocation time outside expected range"
        assert call_time + datetime.timedelta(seconds=60 - wiggle) <= second_invocation_time <= call_time + datetime.timedelta(60 + wiggle), "Second invocation time outside expected range"
        assert call_time + datetime.timedelta(seconds=180 - wiggle) <= third_invocation_time <= call_time + datetime.timedelta(seconds=180 + wiggle), "Third invocation time outside expected range"
        print("\N{WHITE HEAVY CHECK MARK} Retries as expected.")
    return (assert_three_tries_with_approx_one_and_two_minute_waits,)


@app.cell
def _(assert_three_tries_with_approx_one_and_two_minute_waits):
    assert_three_tries_with_approx_one_and_two_minute_waits("async_handler_raises_exception")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### async, times out
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    The same docs say function time outs are treated the same as code errors.
    """)
    return


@app.cell
def _(assert_three_tries_with_approx_one_and_two_minute_waits):
    assert_three_tries_with_approx_one_and_two_minute_waits("async_invocation_times_out")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### async, throttled
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    We can't use logs in this case.
    """)
    return


@app.cell
def _(get_invocations_from_logs):
    assert get_invocations_from_logs("async_throttled") == []
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    That makes sense: it's throttled so no invocations so no logs.

    What about the `Throttles` metric?
    """)
    return


@app.cell
def _(call_times, cloudwatch, datetime):
    def get_metric_sum(function_name: str, metric_name: str) -> list[tuple]:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=call_times[function_name],
            EndTime=datetime.datetime.now(datetime.UTC),
            Period=60,  # lowest possible for non-custom metrics
            Statistics=["Sum"],
        )

        sum_and_timestamps = [(datapoint["Sum"], datapoint["Timestamp"]) for datapoint in response["Datapoints"]]
        sum_and_timestamps = sorted(sum_and_timestamps, key=lambda x: x[1])

        return sum_and_timestamps
    return (get_metric_sum,)


@app.cell
def _(get_metric_sum):
    assert get_metric_sum("async_throttled", "Throttles") == []
    return


@app.cell
def _(mo):
    mo.md(r"""
    Nope.

    It seems that for throttling due to zero reserved concurrency, nothing is published to the `Throttles` metric.
    So we can't use it to check retries.

    AWS provides some async-specific metrics, including:
      - `AsyncEventsReceived`, which counts the number of events for this function which arrived in Lambda's internal queue, and
      - `AsyncEventsDropped`, which counts the number of events dropped because of processing failures.

    Let's look at them.
    """)
    return


@app.cell
def _(get_metric_sum, pprint):
    async_events_received = get_metric_sum("async_throttled", "AsyncEventsReceived")
    pprint(async_events_received)

    assert len(async_events_received) == 1
    [(count, timestamp)] = async_events_received
    assert count == 1.0

    async_events_dropped = get_metric_sum("async_throttled", "AsyncEventsDropped")
    pprint(async_events_dropped)

    assert len(async_events_dropped) == 1
    [(count, timestamp)] = async_events_dropped
    assert count == 1.0
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We see that the event was received and immediately dropped.

    This confirms the docs: no retries for functions with zero reserved concurrency.

    But what about retries for genuine throttles?
    That's what we really care about.
    How to investigate that?

    Strategy:
    Set the reserved concurrency to 1,
    then invoke the function twice in quick succession.
    The first invocation will succeed.
    The handler will sleep for 60s.
    The second invocation will be throttled,
    as will its retries, for 60s,
    and we can check retries in that window.

    It won't show us retries outside 60s, but it'll be something.
    """)
    return


@app.cell
def _(lambda_):
    try:
        lambda_.put_function_concurrency(FunctionName="async_throttled", ReservedConcurrentExecutions=1)
    except lambda_.exceptions.InvalidParameterValueException:
        print("It looks like your account's concurrency quota is too low. Try the modified strategy explained below.")
    return


@app.cell
def _(mo):
    mo.md(r"""
    For newish accounts, the default account-level concurrency is 10.
    Yes, 10.
    But aws doesn't let you set a function's reserved concurrency if the leftover concurrency would be less than 100.
    So in that case you can't set reserved concurrency to 1. [3]

    I hit this problem and upped my concurrency quota in aws.
    You could do the same, or you could follow try this modified strategy:
    Unset reserved concurrency.
    Then invoke the function 11 times in quick succession.
    The first 10 invocations will succeed.
    The last will be throttled and we can check any retries within 60s.
    """)
    return


@app.cell
def _(call_times, datetime, lambda_):
    call_times["async_throttled"] = datetime.datetime.now(datetime.UTC)
    for _ in range(2):
        lambda_.invoke(FunctionName="async_throttled", InvocationType="Event")
    return


@app.cell
def _(mo):
    mo.md(r"""
    Now let's check throttles again.
    """)
    return


@app.cell
def _(get_metric_sum, pprint):
    pprint(get_metric_sum("async_throttled", "Throttles"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    Nice! We can see that there were a bunch of retries.

    But metrics only have a one-minute resolution.
    So we can't see in much detail when the retries happened.

    Maybe `AsyncEventsReceived` gives a richer picture?
    """)
    return


@app.cell
def _(get_metric_sum, pprint):
    pprint(get_metric_sum("async_throttled", "AsyncEventsReceived"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    No.
    `AsyncEventsReceived` only counts an event once, no matter how many retries.
    So it just counted two events, corresponding to our two invocations.

    However, there is another async-specific metric we can use [2]:

    > The `AsyncEventAge` metric is a measure of the difference between the time that an event is first enqueued
    in the internal queue and the time the Lambda service invokes the function.
    With retries, Lambda emits this metric every time it attempts to invoke the function with the event.
    An increasing value shows retries because of error or throttles.
    """)
    return


@app.cell
def _(call_times, cloudwatch, datetime):
    def get_async_event_age_metric(function_name: str) -> list:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="AsyncEventAge",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            StartTime=call_times[function_name],
            EndTime=datetime.datetime.now(datetime.UTC),
            Period=60,
            Statistics=["SampleCount", "Minimum", "Average", "Maximum"],
        )

        return sorted(response["Datapoints"], key=lambda datapoint: datapoint["Timestamp"])
    return (get_async_event_age_metric,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    (Why those 4 statistics? We'll see shortly.)

    Fingers crossed.
    """)
    return


@app.cell
def _(get_async_event_age_metric, pprint):
    pprint(get_async_event_age_metric("async_throttled"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    Ok, that's looking better.

    We can see that Lambda is backing off and retrying.

    Let's also get the call time and the start times from the logs, then think about what the numbers are telling us.
    """)
    return


@app.cell
def _(call_times, get_invocations_from_logs):
    print("boto3 call time:")
    print(f"\t{call_times['async_throttled']}")
    print("function invocation times:")
    for invocation_time in get_invocations_from_logs("async_throttled"):
        print(f"\t{invocation_time}")
    return


@app.cell
def _(mo):
    mo.md(r"""
    We asynchronously invoked the function twice at about 01:19:59.
    So two events got enqueued about then.

    Focus on the first `AsyncEventAge` datapoint.
    It shows Lambda first tried to invoke the function 35ms after enqueueing (`'Minimum': 35`).
    That try was successful, the event was removed from the queue, and the function ran for 60s.
    The datapoint shows one additional try (`'SampleCount': 2`) 2ms later (`'Maximum`: 37`), corresponding to the second event.
    That try failed.

    The second datapoint shows Lambda tried to invoke the function 6 more times,
    the first of those about 1s after enqueuing,
    and the last about 59s after.
    We can't tell exactly when the intermediate tries were,
    but the numbers (`'Average': 19675`) are consistent with expanding waits between tries.
    (This is why we fetched all four metrics.)
    Again, all the tries failed.

    The third datapoint shows Lambda tried yet again about 117s after enqueuing.
    This try was successful and the function started running at about 01:21:56.
    So no more datapoints.

    Lambda could have successfully tried earlier than 117s after enqueuing.
    The concurrency was only used up for 60s.
    But Lambda couldn't know that.

    It also looks from the numbers that Lambda uses _jittered_ backoff.

    In short:
    for the throttled invocation
    there were 7 failed tries in the 60s window
    followed by 1 successful try quite a while later.

    Let's `assert` about this as best we can.
    """)
    return


@app.cell
def _(get_async_event_age_metric):
    def assert_at_least_five_tries(function_name: str) -> None:
        datapoints = get_async_event_age_metric(function_name)
        assert sum(datapoint["SampleCount"] for datapoint in datapoints) >= 5
        # it would be nice to assert capped increasing intervals, but how to do it robustly?
        print("\N{WHITE HEAVY CHECK MARK} Retries as expected.")
    return (assert_at_least_five_tries,)


@app.cell
def _(assert_at_least_five_tries):
    assert_at_least_five_tries("async_throttled")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Synchronous, exception
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    Lambda does not retry failed synchronous invocations,
    whether it fails from throttling, timeout, exception, whatever.
    How could it?
    For a synchronous invocation,
    the requester gets the function's return value or error in the response,
    and the connection is closed.
    So if a failed invocation were retried, it's too late to respond.

    Still, for completeness, let's check.
    """)
    return


@app.cell
def _(call_times, get_invocations_from_logs):
    def assert_one_invocation_only(function_name: str) -> None:
        print("boto3 call time:")
        print(f"\t{call_times[function_name]}")
        invocations = get_invocations_from_logs(function_name)
        print("function invocation times:")
        for invocation_time in invocations:
            print(f"\t{invocation_time}")

        assert len(invocations) == 1, f"Expected 1 invocation but got {len(invocations)}"
        print("\N{WHITE HEAVY CHECK MARK} Retries as expected.")
    return (assert_one_invocation_only,)


@app.cell
def _(assert_one_invocation_only):
    assert_one_invocation_only("sync_handler_raises_exception")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Synchronous, timeout
    """)
    return


@app.cell
def _(assert_one_invocation_only):
    assert_one_invocation_only("sync_invocation_times_out")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Synchronous, throttled
    """)
    return


@app.cell
def _(get_metric_sum):
    def assert_only_one_throttle(function_name: str) -> None:
        throttles_datapoints = get_metric_sum("sync_throttled", "Throttles")
        assert len(throttles_datapoints) == 1
        value, timestamp = throttles_datapoints[0]
        assert value == 1.0
        print("\N{WHITE HEAVY CHECK MARK} Retries as expected")
    return (assert_only_one_throttle,)


@app.cell
def _(assert_only_one_throttle):
    assert_only_one_throttle("sync_throttled")
    return


@app.cell
def _(mo):
    mo.md(r"""
    No retries.
    We saw the same with the asynchronous invocation.
    But in that case, there _were_ retries for genuine throttles (rather than zero reserved concurrency).
    Is it the same here?

    Surely not, for reasons explained above.
    But let's check anyway.

    We'll set reserved concurrency to 1
    then synchronously invoke the function twice, like before.
    But for a synchronous invocation, the boto3 call blocks until the function returns.
    So invoking the function twice in a loop won't tell us anything:
    the second invocation will only happen after the first has completed,
    and both will succeed.
    What we can do instead is to invoke in two threads.
    """)
    return


@app.cell
def _(lambda_):
    try:
        lambda_.put_function_concurrency(FunctionName="sync_throttled", ReservedConcurrentExecutions=1)
    except lambda_.exceptions.InvalidParameterValueException:
        print("It looks like your account's concurrency quota is too low.")
    return


@app.cell
def _(botocore, lambda_):
    def invoke_and_suppress_throttling_exception():
        try:
            lambda_.invoke(FunctionName="sync_throttled", InvocationType="RequestResponse")
        except botocore.exceptions.ClientError as err:
            if err.response["Error"]["Code"] != "TooManyRequestsException":
                raise err
    return (invoke_and_suppress_throttling_exception,)


@app.cell
def _(call_times, datetime, invoke_and_suppress_throttling_exception):
    # this will take as long as the lambda function takes
    from threading import Thread

    call_times["sync_throttled"] = datetime.datetime.now(datetime.UTC)
    thread1 = Thread(target=invoke_and_suppress_throttling_exception)
    thread2 = Thread(target=invoke_and_suppress_throttling_exception)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    return


@app.cell
def _(assert_only_one_throttle):
    assert_only_one_throttle("sync_throttled")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Summary

    |           | **exception or timeout**              | **throttled because zero provisioned concurrency** | **throttled normally**                                                               |
    |-----------|---------------------------------------|----------------------------------------------------|--------------------------------------------------------------------------------------|
    | **async** | try, ~1m wait, retry, ~2m wait, retry | no retry                                           | capped jittered exponential backoff until timeout<br>(typically: cap 5m, timeout 6h) |
    | **sync**  | no retry                              | no retry                                           | no retry                                                                             |
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Clean up
    """)
    return


@app.cell
def _(repo_root, subprocess):
    subprocess.run(
        ["cdk", "destroy", "--force", "LambdaRetriesStack"],
        check=True,
        cwd=repo_root,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## References

    [1] https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html

    [2] https://aws.amazon.com/blogs/compute/introducing-new-asynchronous-invocation-metrics-for-aws-lambda/

    [3] https://benellis.cloud/my-lambda-concurrency-applied-quota-is-only-10-but-why

    [4] https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html
    """)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
