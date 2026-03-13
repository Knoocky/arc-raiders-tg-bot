. "$PSScriptRoot\_common.ps1"

Set-ProjectLocation
Import-ProjectEnv

python -m pytest

