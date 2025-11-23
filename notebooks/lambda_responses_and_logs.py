import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Lambda Response and Logs

    When you invoke a lambda function,
    what do the responses and logs look like
    - for cold versus warm start?
    - if the init raises an exception?
    - if the handler raises an exception?
    - if the init times out?
    - if the handler times out?
    - if the handler returns an unserializable object?
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Stack

    Just a bunch of lambdas:
    - `slow_init`
    - `init_exception`
    - `handler_exception`
    - `init_times_out`
    - `handler_times_out`
    - `handler_returns_unserializable`

    each doing what its name suggests, via `sleep()` or `raise Exception` or `return set()`.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Setup
    """)
    return


@app.cell
def _():
    import datetime

    import boto3

    return boto3, datetime


@app.cell
def _(boto3):
    lambda_ = boto3.client("lambda")
    logs = boto3.client("logs")
    return lambda_, logs


@app.cell
def _(datetime, lambda_):
    call_times = {}
    responses = {}

    for function_name in (
        "slow_init",
        "slow_init",  # twice, to contrast cold versus warm start
        "init_exception",
        "handler_exception",
        "init_times_out",
        "handler_times_out",
        "handler_returns_unserializable",
    ):
        # the dict values are all lists so i can treat once-called and twice-called functions uniformly
        call_times.setdefault(function_name, []).append(datetime.datetime.now(datetime.UTC))
        response = lambda_.invoke(FunctionName=function_name)
        del response["ResponseMetadata"]  # just noise for our purposes
        del response["ExecutedVersion"]  # "$LATEST"
        # the "Payload" value is a botocore.response.StreamingBody object
        # it's file-like, so has a `read()` method, returning bytes
        response["Payload"] = response["Payload"].read().decode("utf-8")
        responses.setdefault(function_name, []).append(response)
    return call_times, responses


@app.cell
def _(call_times, datetime, logs):
    def print_logs(function_name):
        earliest_call_time = min(call_times[function_name])

        earliest_call_timestamp_in_ms = int(earliest_call_time.timestamp()) * 1000
        response = logs.filter_log_events(
            logGroupName=f"/aws/lambda/{function_name}",
            startTime=earliest_call_timestamp_in_ms,
        )

        nice_logs = ""
        for event in response["events"]:
            t = datetime.datetime.fromtimestamp(event["timestamp"] / 1000, datetime.UTC)
            message = event["message"]
            nice_logs += f"{t}: {message}"

        print(nice_logs)

    return (print_logs,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Results
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `slow_init`
    """)
    return


@app.cell
def _(responses):
    responses["slow_init"]
    return


@app.cell
def _(call_times):
    call_times["slow_init"]
    return


@app.cell
def _(print_logs):
    print_logs("slow_init")
    return


@app.cell
def _(mo):
    mo.md(r"""
    The `StatusCode` key is from the Lambda service, not the function.

    In happy cases, like this one, the `"Payload"` is the `json.dumps()` of the function's return value.

    The first, cold invocation has an `INIT_START` message and an `Init Duration` in the `REPORT` message.
    The second, warm invocation has neither.

    The first invocation's `Billed Duration` is the _sum_ of its `Init Duration` and (handler) `Duration`, rounded up to the nearest millsecond.
    So you're billed for the init time.
    That's a recent change.
    Before August 1 2025, the init time for

    > on-demand invocations of Lambda functions packaged as ZIP files that use managed runtimes

    were not billed.

    The function's timeout is 3s (the default).
    The init was 4s.
    But no timeout.
    So the init does not count towards the function's timeout.

    Payloads are meant to be json,
    but `"hi there"` isn't json, is it?
    Sure it is [2]:

    > A JSON text is a serialized value. Note that certain previous specifications of JSON constrained a JSON text to be an object or an array.

    [3] explains the confusion nicely.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `init_exception`
    """)
    return


@app.cell
def _(responses):
    responses["init_exception"]
    return


@app.cell
def _(call_times):
    call_times["init_exception"]
    return


@app.cell
def _(print_logs):
    print_logs("init_exception")
    return


@app.cell
def _(mo):
    mo.md(r"""
    `"StatusCode": 200` in the response,
    despite the exception,
    because it's about your request to the Lambda service,
    not about your function [4].

    > The status code in the API response doesn’t reflect function errors. Error codes are reserved for errors that prevent your function from executing, such as permissions errors, quota errors, or issues with your function’s code and configuration.

    What does flag that something went wrong
    is the presence of `"FunctionError"`.
    The value is `"Unhandled"`,
    which makes sense,
    but I wonder if any other values are possible.

    The payload is rich
    — even a stacktrace ("traceback" in the logs).

    The response doesn't explicitly flag that the error was in the init.
    In this case, it's plain from the stacktrace.
    In actual cases, it might not be.

    Notice the empty request id in the payload
    but populated request id in the last few logs.

    The logs have an `INIT_REPORT` message this time,
    including `Phase: init` and `Status: error`.
    That's helpful
    — no mistaking that the init errored.
    I guess we get an `INIT_REPORT` only when the init goes wrong?

    We also get a `LAMBDA_WARNING` message from the Lambda service,
    and the same traceback as was in the response.

    In fact we get these messages
    — the `LAMBDA_WARNING`, traceback, and `INIT_REPORT`
    — twice!
    But the second `INIT_REPORT` is slightly different:
    a different duration
    and `Phase: invoke`.

    And we also get a `REPORT`,
    with yet a different duration.

    Puzzling.
    Why does an `INIT_REPORT` refer to `Phase: invoke`?
    Why repeat the warning and traceback?
    Why three different durations?
    Why request id in logs but not payload?
    Does Lambda try to invoke your function even when the init failed?
    Or is it just pretending that it tried?
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `handler_exception`
    """)
    return


@app.cell
def _(responses):
    responses["handler_exception"]
    return


@app.cell
def _(call_times):
    call_times["handler_exception"]
    return


@app.cell
def _(print_logs):
    print_logs("handler_exception")
    return


@app.cell
def _(mo):
    mo.md(r"""
    No surprises here.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `init_times_out`
    """)
    return


@app.cell
def _(responses):
    responses["init_times_out"]
    return


@app.cell
def _(call_times):
    call_times["init_times_out"]
    return


@app.cell
def _(print_logs):
    print_logs("init_times_out")
    return


@app.cell
def _(mo):
    mo.md(r"""
    The init timed out after 10s.
    But the payload says "Task timed out after 3.00 seconds".

    We have two `INIT_REPORT`s,
    as we did for `init_exception`.
    One is for the init phase and records a duration of 10s.
    The other is for the invoke phase and records a duration of about 3s.

    We have a `REPORT` too,
    this with a duration of exactly 3s.

    Puzzling again,
    like for `init_exception`.

    The response and the logs are half-subsuming the init into the invoke.

    My takeaway: the logs are geared for the normal case, not init failures.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `handler_times_out`
    """)
    return


@app.cell
def _(responses):
    responses["handler_times_out"]
    return


@app.cell
def _(call_times):
    call_times["handler_times_out"]
    return


@app.cell
def _(print_logs):
    print_logs("handler_times_out")
    return


@app.cell
def _(mo):
    mo.md(r"""
    No surprises here.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### `handler_returns_unserializable`
    """)
    return


@app.cell
def _(responses):
    responses["handler_returns_unserializable"]
    return


@app.cell
def _(call_times):
    call_times["handler_returns_unserializable"]
    return


@app.cell
def _(print_logs):
    print_logs("handler_returns_unserializable")
    return


@app.cell
def _(mo):
    mo.md(r"""
    The error type in the response is `Runtime.MarshalError`,
    not `TypeError`, which is what `json.dumps(set())` raises.
    That makes sense:
    a Lambda procedure failed,
    so we get Lambda-specific errors,
    even if that procedure is mimicking Python's `json.dumps()`.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## References

    [1] https://aws.amazon.com/blogs/compute/aws-lambda-standardizes-billing-for-init-phase/

    [2] https://www.ietf.org/rfc/rfc7159.txt

    [3] https://stackoverflow.com/a/7487892

    [4] https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/invoke.html
    """)
    return


if __name__ == "__main__":
    app.run()
