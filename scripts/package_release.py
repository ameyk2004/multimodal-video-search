import os
import re
import urllib.parse
import subprocess


def load_env(filepath: str) -> dict:
    """Parse a .env file and return a dictionary of keys/values."""
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, val = parts
                        env_vars[key.strip()] = val.strip("\"'")
    return env_vars


def update_samconfig(env_vars: dict, extra_overrides: dict = None):
    """Update samconfig.toml with parameter overrides from .env so non-interactive deploy works."""
    if extra_overrides is None:
        extra_overrides = {}
        
    qdrant_url = env_vars.get("QDRANT_URL", "")
    qdrant_api_key = env_vars.get("QDRANT_API_KEY", "")
    hf_api_key = env_vars.get("HF_API_KEY", "")
    gemini_api_key = env_vars.get("GEMINI_API_KEY", "")

    samconfig_path = "samconfig.toml"
    if not os.path.exists(samconfig_path):
        return

    with open(samconfig_path, "r") as f:
        lines = f.readlines()

    # Build the new parameter_overrides line using SAM's expected TOML format
    overrides = [
        f'QdrantUrl=\\"{qdrant_url}\\"',
        f'QdrantApiKey=\\"{qdrant_api_key}\\"',
        f'HfApiKey=\\"{hf_api_key}\\"',
        f'GeminiApiKey=\\"{gemini_api_key}\\"'
    ]
    for k, v in extra_overrides.items():
        overrides.append(f'{k}=\\"{v}\\"')
        
    new_line = 'parameter_overrides = "' + ' '.join(overrides) + '"\n'

    with open(samconfig_path, "w") as f:
        for line in lines:
            if line.strip().startswith("parameter_overrides"):
                f.write(new_line)
            else:
                f.write(line)


def main():
    print("🚀 Preparing Quick Create Release...")

    # Load secrets from .env to avoid committing them
    env_vars = load_env("../.env")

    # Sync samconfig.toml with latest .env values
    update_samconfig(env_vars)

    # 1. Create a wrapper template to force SAM to upload our real template to S3
    wrapper_content = """AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Resources:
  App:
    Type: AWS::Serverless::Application
    Properties:
      Location: .aws-sam/build/template.yaml
"""
    with open("wrapper.yaml", "w") as f:
        f.write(wrapper_content)

    # 2. Package using SAM (handles S3 bucket resolution and uploads)
    print("📦 Packaging template via SAM...")
    try:
        subprocess.run([
            "sam", "package",
            "--template-file", "wrapper.yaml",
            "--resolve-s3",
            "--output-template-file", "packaged-wrapper.yaml"
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("❌ Error: SAM package failed.")
        print(e.stderr.decode("utf-8"))
        return

    # 3. Extract the S3 URL from the packaged wrapper
    with open("packaged-wrapper.yaml", "r") as f:
        packaged_content = f.read()

    match = re.search(r"Location:\s*(s3://[^\s]+|https://[^\s]+)", packaged_content)
    if not match:
        print("❌ Error: Could not extract S3 URL from packaged template.")
        return

    s3_url = match.group(1).strip()

    # CloudFormation Quick Create needs an https:// URL
    if s3_url.startswith("s3://"):
        parts = s3_url[5:].split("/", 1)
        bucket_name = parts[0]
        key = parts[1]
        template_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
    else:
        template_url = s3_url

    # 4. Construct Quick Create URL
    region = "us-east-1"
    stack_name = "sadhananandadeep-backend"

    qdrant_url = env_vars.get("QDRANT_URL", "ENTER_QDRANT_URL")
    qdrant_api_key = env_vars.get("QDRANT_API_KEY", "ENTER_QDRANT_API_KEY")
    hf_api_key = env_vars.get("HF_API_KEY", "ENTER_HF_API_KEY")
    gemini_api_key = env_vars.get("GEMINI_API_KEY", "ENTER_GEMINI_API_KEY")

    params = {
        "templateURL": template_url,
        "stackName": stack_name,
        "param_QdrantUrl": qdrant_url,
        "param_QdrantApiKey": qdrant_api_key,
        "param_HfApiKey": hf_api_key,
        "param_GeminiApiKey": gemini_api_key,
    }

    query_string = urllib.parse.urlencode(params)
    quick_create_url = (
        f"https://console.aws.amazon.com/cloudformation/home"
        f"?region={region}#/stacks/create/review?{query_string}"
    )

    print("\n✅ Release packaged successfully!")
    print("\n🔗 ------------------------------------------------ 🔗")
    print("Click this link to deploy directly from your browser:")
    print(quick_create_url)
    print("🔗 ------------------------------------------------ 🔗\n")

    # Cleanup
    for fname in ("wrapper.yaml", "packaged-wrapper.yaml"):
        if os.path.exists(fname):
            os.remove(fname)


if __name__ == "__main__":
    main()
