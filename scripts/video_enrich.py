# !rm -rf /content/repo/data_pipeline/enriched_metadata/*


import sys
import os

# Ensure the root of the repository is in the Python path
if os.path.exists("/content/repo"):
    sys.path.insert(0, "/content/repo")
else:
    # Local fallback: Add the parent directory of this script to the path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_pipeline.video_enricher import VideoEnricher
# Determine root directory based on environment
if os.path.exists("/content/repo"):
    root_dir = "/content/repo"
else:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

enricher = VideoEnricher(
    input_dir=f"{root_dir}/data_pipeline/output",
    output_dir=f"{root_dir}/data_pipeline/enriched_metadata",
)
results = enricher.process_all()
print(f"✅ Enriched {len(results)} videos")