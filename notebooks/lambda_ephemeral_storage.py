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
    # Lambda Ephemeral Storage

    Lambda provides ephemeral storage for functions in `/tmp`.
    Do files in `/tmp` persist across executions?
    A cold start will get a clean `/tmp`, certainly,
    but what about warm starts?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stack

    Just a lambda.
    It checks whether `/tmp/foobar` exists.
    If not, it creates it.
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
    import boto3

    lambda_ = boto3.client("lambda")
    return (lambda_,)


@app.cell
def _(lambda_):
    cold_response = lambda_.invoke(FunctionName="ephemeral_storage")
    cold_response["Payload"].read().decode("utf-8")
    return


@app.cell
def _(lambda_):
    warm_response = lambda_.invoke(FunctionName="ephemeral_storage")
    warm_response["Payload"].read().decode("utf-8")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So __`/tmp` persists across warm starts.__

    If your function interacts with `/tmp`, remember that it may contain gunk from previous invocations.
    """)
    return


if __name__ == "__main__":
    app.run()
