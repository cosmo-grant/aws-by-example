import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Lambda Who What Where

    What are things like for your lambda function?

    For example:
    - which user is it?
    - what's its working directory?
    - what's on the filesystem?
    - what's its local time zone?
    - which shell does it have access to, if any?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stack

    Just a lambda, investigating its world.
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

    return boto3, datetime, time


@app.cell
def _(boto3):
    lambda_ = boto3.client("lambda")
    logs = boto3.client("logs")
    return lambda_, logs


@app.cell
def _(datetime, logs):
    def print_logs(function_name, start_time):
        start_time_in_ms = int(start_time.timestamp()) * 1000
        response = logs.filter_log_events(
            logGroupName=f"/aws/lambda/{function_name}",
            startTime=start_time_in_ms,
        )

        nice_logs = ""
        for event in response["events"]:
            t = datetime.datetime.fromtimestamp(event["timestamp"] / 1000, datetime.UTC)
            message = event["message"]
            nice_logs += f"{t}: {message}"

        print(nice_logs)

    return (print_logs,)


@app.cell
def _(datetime, lambda_, print_logs, time):
    call_time = datetime.datetime.now(datetime.UTC)
    lambda_.invoke(FunctionName="who_what_where")
    time.sleep(60)  # give logs time to appear
    print_logs("who_what_where", call_time)
    return


@app.cell
def _(mo):
    mo.md(r"""
    The user is `sbx_user1051`, not `root`.
    The `1051` looks random to me,
    but it does persist across invocations, cold and warm, and cdk updates.
    I wonder if it's the same across runtimes.

    The working directory is `/var/task`,
    containing just the lambda code,
    which makes sense.

    `/` contains some things of interest,
    e.g. `lambda-entrypoint.sh`,
    which I'll look at another time.

    The function can't write to its working directory,
    nor presumably anywhere,
    (except for `/tmp`, which is provided explicitly for ephemeral storage).

    The shell is GNU bash.
    And the stdout of the subprocess running via the shell shows up in the logs.
    That also makes sense: stdout is logged, no matter its source.
    There's no `SHELL` environment variable.

    `time.tzname` is

    > A tuple of two strings: the first is the name of the local non-DST timezone, the second is the name of the local DST timezone.

    Its value for me locally (in the UK) is `('GMT', 'BST')`.
    But in the lambda it's `('UTC', 'UTC')`.
    I presume that's the case no matter the region.
    Which is nice: one less thing to worry about.
    """)
    return


if __name__ == "__main__":
    app.run()
