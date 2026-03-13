. "$PSScriptRoot\_common.ps1"

Set-ProjectLocation
Import-ProjectEnv

alembic upgrade head
