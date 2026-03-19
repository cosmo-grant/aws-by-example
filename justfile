checks:
  ruff format --exclude lib/resources/layers/
  ruff check --fix --exclude lib/resources/layers/
  mypy --exclude lib/resources/layers .

open:
  open https://cosmo-grant.github.io/aws-by-example/

preview:
  open -a firefox file:///Users/cosmo.grant/git/personal/aws-by-example/docs
