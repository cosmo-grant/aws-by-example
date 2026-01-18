# CONTRIBUTING.md

## How to add a new example

1. Define a stack in `lib/` and add it to `app.py`.

2. Export any needed AWS variables, e.g. `AWS_PROFILE`, `ACCOUNT_ID`, `REGION`.

3. `cdk deploy`

4. Write the notebook.

5. Export as html to `docs`.

6. `uv run ./scripts/make_index.py`

7. `git push`

## Tips

### Make the notebooks runnable straight through

For example, if there has to be a wait between two cells
(to give the logs a chance to show up, say)
then use `time.sleep`, instead of relying on the user to wait.

## Make the comments insensitive to things in the output that might vary across runs (e.g. times)

You don't want to have to update the comments each time you run the notebook.

## Name the variable, construct id, and construct name such that _one_ search-and-replace can update them all at once

Good, because `s/slow_init/init_times_out/g` changes all at once:

```python
slow_init_log_group = logs.LogGroup(
    self,
    "slow_init_log_group",
    log_group_name="/aws/lambda/slow_init",
    removal_policy=RemovalPolicy.DESTROY,
    retention=logs.RetentionDays.ONE_DAY,
)
```

Bad, because the construct id may get out of sync:

```python
topic_target_lambda_log_group = logs.LogGroup(
    self,
    "TopicTargetLambdaLogGroup",
    log_group_name="/aws/lambda/topic_target",
    removal_policy=RemovalPolicy.DESTROY,
    retention=logs.RetentionDays.ONE_DAY,
)
```
