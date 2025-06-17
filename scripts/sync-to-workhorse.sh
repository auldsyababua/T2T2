#\!/bin/bash
echo "Syncing to Workhorse..."
rsync -avz --exclude node_modules --exclude .venv --exclude venv . workhorse@'10.0.0.2'":~/projects/t2t2/"
echo "Sync complete\!"
