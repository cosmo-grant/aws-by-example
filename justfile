checks:
  ruff format
  ruff check --fix
  mypy .

open:
  open https://cosmo-grant.github.io/aws-by-example/

preview:
  open -a firefox file:///Users/cosmo.grant/git/personal/aws-by-example/docs
