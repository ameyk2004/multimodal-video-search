#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Teardown Script — Multimodal Guru Video Search
# Destroys the entire AWS CloudFormation stack and cleans up
# local SAM build artifacts.
#
# To run this script:
#   chmod +x scripts/cleanup.sh
#   ./scripts/cleanup.sh
# ─────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLOUD_DIR="$PROJECT_ROOT/cloud-backend"

echo "============================================"
echo "  Tearing down AWS resources..."
echo "============================================"

cd "$CLOUD_DIR"

# Destroy the CloudFormation stack (non-interactive)
echo "Running 'sam delete --no-prompts'..."
sam delete --no-prompts

# Clean up local build cache
if [ -d ".aws-sam" ]; then
    echo "Removing local .aws-sam build cache..."
    rm -rf .aws-sam
fi

echo ""
echo "============================================"
echo "  ✅ Cleanup complete!"
echo "  All AWS resources have been terminated."
echo "  Local build cache has been removed."
echo "============================================"
