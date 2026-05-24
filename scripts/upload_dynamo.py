import sys
import os
import importlib
import logging

# Ensure the root of the repository is in the Python path
if os.path.exists("/content/repo"):
    root_dir = "/content/repo"
else:
    # Local fallback: Add the parent directory of this script to the path
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.insert(0, root_dir)

from data_pipeline.dynamo_uploader import upload_metadata

# Temporarily force logging to show everything
logging.getLogger().setLevel(logging.INFO)

upload_metadata(input_dir=f"{root_dir}/data_pipeline/enriched_metadata")
print("✅ DynamoDB upload cell finished!")