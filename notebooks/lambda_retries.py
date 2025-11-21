import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Lambda Retries

    When a function invocation fails, does the Lambda service retry it?
    How often, and with what backoff?
    Does it depend on the invocation type (synchronous or asynchronous) or the failure reason (timeout, exception, throttling)?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stack

    A bunch of functions:

    - `async_handler_raises_exception`
    - `sync_handler_raises_exception`
    - `async_invocation_times_out`
    - `sync_invocation_times_out`
    - `async_throttled`
    - `sync_throttled`

    each doing what its name suggests,
    and a log group for each.

    The `async*` and `sync*` prefixes just indicate how I'll call the functions,
    nothing about the functions themselves.

    I have `async` and `sync` versions
    so I can call them concurrently without getting confused.

    By default functions sends logs to an automatically created log group.
    But that log group is not configurable
    (e.g. you should not set its removal policy).
    So the docs recommend creating your own and passing it in,
    which is what I've done.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Investigation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Set up boto3 clients

    We'll use boto3 to invoke and monitor the functions.

    But by default boto3 automatically retries for certain errors, such as `ThrottlingException` [1].
    We don't want boto3 to retry: it would be confusing.
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
    The `retries` dictionary accepts
    a `total_max_attempts` key, which _includes_ the initial attempt,
    or a `max_attempts` key, which _excludes_ it.
    Confusing!

    Using "retries" is always confusing.
    Does "third retry" mean third try or fourth try?
    Throw 0 vs 1-indexing into the mix
    (say you store an array with an item for each try)
    and you're asking for trouble.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Throttle

    Two of the lambdas are for checking retries given throttling.
    So let's throttle them.
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
    ### Invoke the functions
    """)
    return


@app.cell
def _():
    import datetime
    from pprint import pprint
    return datetime, pprint


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
def _(botocore, call_times, datetime, lambda_, pprint):
    call_times["sync_throttled"] = datetime.datetime.now(datetime.UTC)
    try:
        lambda_.invoke(FunctionName="sync_throttled", InvocationType="RequestResponse")
    except botocore.exceptions.ClientError as err:
        if err.response["Error"]["Code"] == "TooManyRequestsException":
            # sync invocation of throttled lambda, so we expect to get TooManyRequestsException
            pprint(err.response)
        else:
            raise err
    return


@app.cell
def _(mo):
    mo.md(r"""
    The sync calls get 200 OK.

    Except for `sync_throttled`,
    which throws a `TooManyRequestsException`
    with underlying `'HTTPStatusCode': 429` (TooManyRequests).

    The async calls get 202 Accepted:

    > The request has been received but not yet acted upon.
    > It is noncommittal, since there is no way in HTTP to later send an asynchronous response indicating the outcome of the request.
    > It is intended for cases where another process or server handles the request, or for batch processing. [5]
    """)
    return


@app.cell
def _(call_times, pprint):
    pprint(call_times)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's wait a while to give Lambda a chance to retry.
    """)
    return


@app.cell
def _():
    from time import sleep
    return (sleep,)


@app.cell
def _(sleep):
    sleep(5 * 60)
    return


@app.cell
def _(mo):
    mo.md(r"""
    I'll be using the logs to find function invocations,
    since logs have high resolution timestamps.

    I'll write a helper for that.
    """)
    return


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
            if event["message"].startswith("START")
        ]
        invocations = sorted(invocations)

        return invocations
    return (get_invocations_from_logs,)


@app.cell
def _(mo):
    mo.md(r"""
    Now let's check retries.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### asynchronous, errors
    """)
    return


@app.cell
def _(call_times, get_invocations_from_logs, pprint):
    print("call time:", call_times["async_handler_raises_exception"])
    pprint(get_invocations_from_logs("async_handler_raises_exception"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    The first invocation was a moment after the boto3 call.
    That makes sense: the function has to init first.
    The second invocation was about 1 minute later.
    The third was about 2 minutes after that.

    This matches the docs [4]:

    > If the function returns an error,
    > by default Lambda attempts to run it two more times,
    > with a one-minute wait between the first two attempts,
    > and two minutes between the second and third attempts

    except the waits are only _approximately_ one and two minutes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### async, times out
    """)
    return


@app.cell
def _(call_times, get_invocations_from_logs, pprint):
    print("call time:", call_times["async_invocation_times_out"])
    pprint(get_invocations_from_logs("async_invocation_times_out"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    Same as for error:
    try,
    about 1 minute wait,
    try,
    about 2 minute wait,
    try.

    This matches the docs too:

    > Function errors include errors returned by the function's code and errors returned by the function's runtime, such as timeouts.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### async, throttled
    """)
    return


@app.cell
def _(call_times, get_invocations_from_logs, pprint):
    print("call time:", call_times["async_throttled"])
    pprint(get_invocations_from_logs("async_throttled"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    That makes sense: it's throttled so no invocations so no logs.

    Can we use the `Throttles` metric instead?
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
def _(get_metric_sum, pprint):
    pprint(get_metric_sum("async_throttled", "Throttles"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Nope.

    It seems that for throttling due to zero reserved concurrency,
    nothing is published to the `Throttles` metric.
    So we can't use it to check retries.

    What to do?
    I found a helpful aws blog post [2].
    It describes async-specific metrics, including:
      - `AsyncEventsReceived`, which counts the number of events for this function which arrived in Lambda's internal queue, and
      - `AsyncEventsDropped`, which counts the number of events dropped because of processing failures.

    Let's try them.
    """)
    return


@app.cell
def _(get_metric_sum, pprint):
    async_events_received = get_metric_sum("async_throttled", "AsyncEventsReceived")
    pprint(async_events_received)

    async_events_dropped = get_metric_sum("async_throttled", "AsyncEventsDropped")
    pprint(async_events_dropped)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So the event was received and immediately dropped.

    Conclusion: no retries for functions with zero reserved concurrency.

    That is mentioned in the blog post, though I haven't found it in the main aws docs.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    But what about retries for _genuine_ throttles?
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

    Here we go.
    """)
    return


@app.cell
def _(lambda_):
    lambda_.put_function_concurrency(FunctionName="async_throttled", ReservedConcurrentExecutions=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The first time I tried this,
    I got an `InvalidParameterValueException`.
    The message complained that the operation was forbidden
    because it would reduce my account's `UnreservedConcurrentExecution` below the minimum value of 100.
    Does that mean my account concurrency was 101?
    Isn't the default 1000?

    I found a blog post explaining the situation [3].
    It turns out that for newish accounts, like mine, the default account concurrency is 10.
    Yes, 10.
    But aws only lets you set a function's reserved concurrency if
    you're setting it to 0 (like we did above)
    or the leftover concurrency would be at least 100.

    What to do?
    I could have:
    Unset reserved concurrency.
    Then invoked the function 11 times in quick succession.
    The first 10 invocations would succeed.
    The last would be throttled and we could check retries within 60s.

    But I opted for a simpler approach:
    I asked to up my account concurrency to 1000,
    and waited a few hours for aws to approve it.

    Now we can try again.
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
    We'll wait a bit to give the metrics a chance to update
    """)
    return


@app.cell
def _(sleep):
    sleep(5 * 60)
    return


@app.cell
def _(mo):
    mo.md(r"""
    then check throttles again.
    """)
    return


@app.cell
def _(get_metric_sum, pprint):
    pprint(get_metric_sum("async_throttled", "Throttles"))
    return


@app.cell(hide_code=True)
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

    However, the blog post describes another async-specific metric we can use:

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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We asynchronously invoked the function twice at about 16:29:33.
    So two events got enqueued about then.

    Focus on the first `AsyncEventAge` datapoint.
    It shows Lambda first tried to invoke the function 33ms after enqueueing (`'Minimum': 33`).
    That try was successful, the event was removed from the queue, and the function ran for 60s.
    The datapoint shows 5 additional tries (`'SampleCount': 6`),
    all for the second event,
    the last of which was about 17s after enqueueing (`'Maximum`: 16645`).
    We can't tell exactly when the intermediate tries were,
    but the numbers (`'Average': 4791`) suggest expanding waits between tries.
    (This is why we fetched all four metrics.)
    Those tries all failed.

    The second datapoint shows Lambda tried again to invoke the function
    about 33s after enqeueing (`'Minimum': 32790`).
    That try failed too.
    It tried yet again about 68s after enqueueing (`'Maximum': 67932`).
    That try was successful,
    because the first run had completed by then,
    and the function re-started at about 16:30:42.
    So no more datapoints.

    In short:
    for the throttled invocation
    there were 6 failed tries in the 60s window
    followed by 1 successful try a bit later.

    This matches the docs:

    > For throttling errors (429) and system errors (500-series),
    > Lambda returns the event to the queue and attempts to run the function again for up to 6 hours by default.
    > The retry interval increases exponentially from 1 second after the first attempt to a maximum of 5 minutes.

    except the the docs don't explicitly say what's plain from the numbers:
    that Lambda uses _jittered_ backoff.

    Lambda could have successfully tried earlier than 68s after enqueuing.
    The concurrency was only used up for 60s.
    But Lambda couldn't know that.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### synchronous, exception
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

    The _caller_ may retry
    (whether that's you, or an aws service, or whatever).
    But Lambda itself does not — could not sensibly — retry.

    Still, for completeness, let's check.
    """)
    return


@app.cell
def _(get_invocations_from_logs, pprint):
    pprint(get_invocations_from_logs("sync_handler_raises_exception"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    One invocation only, as expected.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### synchronous, timeout
    """)
    return


@app.cell
def _(get_invocations_from_logs, pprint):
    pprint(get_invocations_from_logs("sync_invocation_times_out"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    Ditto.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### synchronous, throttled
    """)
    return


@app.cell
def _(get_invocations_from_logs, pprint):
    pprint(get_invocations_from_logs("sync_throttled"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    No retries.

    We saw the same with the asynchronous invocation.
    But in that case, there _were_ retries for genuine throttles
    (rather than throttles because of zero reserved concurrency).
    Is it the same here?

    Surely not, for reasons explained above.
    But let's confirm anyway.

    We'll set reserved concurrency to 1
    then synchronously invoke the function twice, like before.

    For a synchronous invocation, the boto3 call blocks until the function returns.
    So invoking the function twice in a loop won't tell us anything:
    the second invocation will only happen after the first has completed,
    and both will succeed.

    What we can do instead is to invoke concurrently, in two threads.
    """)
    return


@app.cell
def _(lambda_):
    lambda_.put_function_concurrency(FunctionName="sync_throttled", ReservedConcurrentExecutions=1)
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
    # this will run for at least as long as the function runs
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
def _(sleep):
    sleep(2 * 60)
    return


@app.cell
def _(get_metric_sum, pprint):
    pprint(get_metric_sum("sync_throttled", "Throttles"))
    return


@app.cell
def _(mo):
    mo.md(r"""
    As expected: 1 throttle, meaning 0 retries.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Summary
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    |           | **exception or timeout**              | **throttled because zero provisioned concurrency** | **genuine throttle**                                                               |
    |-----------|---------------------------------------|----------------------------------------------------|--------------------------------------------------------------------------------------|
    | **async** | try, ~1m wait, retry, ~2m wait, retry | no retry                                           | capped jittered exponential backoff until timeout<br>(typically: cap 5m, timeout 6h) |
    | **sync**  | no retry                              | no retry                                           | no retry                                                                             |
    """)# noqa: E501
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## References

    [1] https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html

    [2] https://aws.amazon.com/blogs/compute/introducing-new-asynchronous-invocation-metrics-for-aws-lambda/

    [3] https://benellis.cloud/my-lambda-concurrency-applied-quota-is-only-10-but-why

    [4] https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html

    [5] https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status#successful_responses
    """)
    return


if __name__ == "__main__":
    app.run()
