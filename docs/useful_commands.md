# Useful commands

Copying files

```shell
rsync -avz  --exclude="*__pycache__*" --exclude=".git" --exclude=".secrets"  --exclude=".zencoder"  --exclude=".ipynb_checkpoints"  --exclude=".zenflow" --exclude=".vscode" \
--exclude=".idea"  --exclude=".venv"  --exclude=".history" --exclude=".claude" \
$(pwd)/perf_engineering_course /Volumes/SeconBrain
```
