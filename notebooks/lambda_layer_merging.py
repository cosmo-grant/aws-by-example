import marimo

__generated_with = "0.18.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Lambda Layer Merging

    A Lambda layer is a .zip file archive that contains supplementary code or data,
    e.g. dependencies, a custom runtime or configuration files.

    If you associate multiple layers with a function, how are they merged?
    For example, what happens if:
    - layer1 contains `cool-pkg 1.0` and layer2 contains `cool-pkg 2.0`?
    - layer1 contains `conf.txt` with content "foo" and layer2 contains `conf.txt` with content "bar"?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stack

    Two layers associated to a lambda.
    One layer contains `requests 2.30`.
    The other contains `requests 2.31`.

    I got `requests` locally via `uv pip install requests -t lib/resources/layers/requests-<major>-<minor>/python`.

    The lambda handler returns import-related stuff, to reveal how layers are merged.
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
    return boto3, lambda_


@app.cell
def _(lambda_):
    invoke_response = lambda_.invoke(FunctionName="layer_merging")
    return (invoke_response,)


@app.cell
def _(invoke_response):
    import json

    json.loads(invoke_response["Payload"].read().decode("utf-8"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### How layers are merged

    Our layers got put in `/opt/python`.

    `/opt/python` is in `sys.path`, the module search path.
    But `PYTHONPATH` is set to `/var/runtime`.
    So `/opt/python` got in `sys.path` by some other means,
    and **`PYTHONPATH` is being used for a non-layer purpose.**

    The `/opt/python` listing reveals **how the layers are merged: rsync-style!**
    Both `requests-2.30.0.dist-info` and `requests-2.31.0.dist-info` are listed.
    So it's not that one version is selected.
    Rather, they're just merged as directories, rsync-style.
    No package manager magic.

    I guess this makes sense.
    Layers can contain any kinds of files, not just dependencies.
    Even if a package manager got involved, how could it sensibly pick a winner?
    So rsync-style merging is the only option.

    Still, couldn't it lead to Dr Moreau packages and mad bugs?
    **If layers contain different versions of a package,
    you end up with a hybrid.**
    In this case it's harmless,
    but couldn't it be harmful in some cases?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Merging order

    The 2.31 layer was merged into the 2.30 layer.
    So we effectively get 2.31.
    That's confirmed by `requests.__version__` in the handler.

    How come?

    In the cdk it's `layers=[requests_2_31_layer, requests_2_30_layer]`.

    In the template, it's the other way round: 2.30 then 2.31.
    """)
    return


@app.cell
def _(boto3):
    cf = boto3.client("cloudformation")

    template_response = cf.get_template(StackName="LambdaLayerMergingStack")
    resources = template_response["TemplateBody"]["Resources"]
    function_resource = next(props for props in resources.values() if props["Type"] == "AWS::Lambda::Function")
    function_resource["Properties"]["Layers"]
    return


@app.cell
def _(mo):
    mo.md(r"""
    It turns out that cdk sorts your list of layers in-place [1]:

    ```typescript
    private renderLayers() {
        if (!this._layers || this._layers.length === 0) {
          return undefined;
        }

        if (FeatureFlags.of(this).isEnabled(LAMBDA_RECOGNIZE_LAYER_VERSION)) {
          this._layers.sort();
        }

        return this._layers.map(layer => layer.layerVersionArn);
    }
    ```

    `LAMBDA_RECOGNIZE_LAYER_VERSION` defaults to `true` when you run `cdk init`.
    So cdk moved 2.31 _after_ 2.30.
    That's why 2.31 won.

    Why does cdk sort layers? The docs [2]:

    >An additional update to the hashing logic fixes two issues surrounding layers. Prior to this change, updating the lambda layer version would have no effect on the function version. Also, the order of lambda layers provided to the function was unnecessarily baked into the hash.
    >
    >This has been fixed in the AWS CDK starting with version 2.27. If you ran cdk init with an earlier version, you will need to opt-in via a feature flag. If you run cdk init with v2.27 or later, this fix will be opted in, by default.

    The first issue makes sense: bumping a layer version should bump the function version.
    But I'm puzzled by the second issue.
    This comment seems spot-on to me [3]:

    >But because layers can overwrite each other, the order in which they're extracted is crucial and Lambda functions which register the same layers in a different order should always have a different hash.
    >
    >Regardless of the previous point, why is it necessary to mutate the layers array to calculate the Lambda function hash? A sorted copy can be used to calculate the same hash. This would cause the layers to maintain the original ordering and be extracted in the expected order.

    Beware: **layer order matters, but by default cdk sorts your list in place.**
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## References

    [1] https://github.com/aws/aws-cdk/blob/v2.243.0/packages/aws-cdk-lib/aws-lambda/lib/function.ts#L1562

    [2] https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_lambda-readme.html#currentversion-updated-hashing-logic-for-layer-versions

    [3] https://github.com/aws/aws-cdk/discussions/26395

    [4] https://damianjanik.com/blog/aws-cdk-lambda-layer-merge-order
    """)
    return


if __name__ == "__main__":
    app.run()
