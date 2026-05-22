.PHONY: build deploy teardown clean release

# Fix Homebrew Python/libexpat linking issue on macOS
export DYLD_LIBRARY_PATH := /opt/homebrew/lib:$(DYLD_LIBRARY_PATH)

# By default, use the template in the templates directory
TEMPLATE_FILE ?= templates/template.yaml
STACK_NAME    ?= multimodal-video-search

build:
	@echo "Building SAM application..."
	sam build -t $(TEMPLATE_FILE)

deploy: build
	@echo "Deploying SAM application (guided mode)..."
	sam deploy --guided

release: build
	@echo "🚀 Releasing $(STACK_NAME)..."
	@ACCOUNT_ID=$$(python3.12 ../scripts/aws_helper.py --action get_account 2>/dev/null || echo "") ; \
	if [ -n "$$ACCOUNT_ID" ] && [ "$$ACCOUNT_ID" != "None" ]; then \
		ARTIFACTS_BUCKET="multimodal-video-search-artifacts-$$ACCOUNT_ID" ; \
		echo "📦 Creating/verifying Artifacts Bucket: $$ARTIFACTS_BUCKET" ; \
		python3.12 ../scripts/aws_helper.py --action create_bucket --bucket $$ARTIFACTS_BUCKET ; \
		echo "📦 Building Frontend..." ; \
		cd ../frontend && npm install && npm run build && cd ../cloud-backend ; \
		echo "☁️ Uploading Frontend to Artifacts Bucket..." ; \
		python3.12 ../scripts/aws_helper.py --action upload --bucket $$ARTIFACTS_BUCKET --source ../frontend/dist ; \
		echo "🔄 Updating SAM config with UiArtifactsBucket=$$ARTIFACTS_BUCKET..." ; \
		python3 -c "import sys; sys.path.insert(0,'../scripts'); from packaging import load_env, update_samconfig; update_samconfig(load_env('../.env'), {'UiArtifactsBucket': '$$ARTIFACTS_BUCKET'})" ; \
	else \
		echo "⚠️ AWS CLI failed. Skipping frontend artifacts sync..." ; \
		python3 -c "import sys; sys.path.insert(0,'../scripts'); from packaging import load_env, update_samconfig; update_samconfig(load_env('../.env'))" ; \
	fi
	@if sam deploy --no-confirm-changeset --no-fail-on-empty-changeset 2>/dev/null; then \
		echo ""; \
		echo "✅ Stack updated successfully!"; \
		UI_BUCKET=$$(python3.12 ../scripts/aws_helper.py --action get_stack_output --stack $(STACK_NAME) --logical_id UiBucketName 2>/dev/null || echo ""); \
		REGION=$$(python3 -c "import boto3; print(boto3.session.Session().region_name or 'us-east-1')" 2>/dev/null || echo "us-east-1"); \
		echo "🎉 Frontend is live at: http://$$UI_BUCKET.s3-website-$$REGION.amazonaws.com"; \
		sam list stack-outputs --stack-name $(STACK_NAME); \
	else \
		echo "Stack not found or credentials missing. Generating Quick Create link..."; \
		python3 ../scripts/packaging.py; \
	fi

teardown:
	@echo "Tearing down AWS CloudFormation stack..."
	@UI_BUCKET=$$(python3.12 ../scripts/aws_helper.py --action get_stack_bucket --stack $(STACK_NAME) --logical_id UiBucket 2>/dev/null || echo ""); \
	if [ -n "$$UI_BUCKET" ] && [ "$$UI_BUCKET" != "None" ]; then \
		echo "🧹 Emptying UI Bucket $$UI_BUCKET before deletion..."; \
		python3.12 ../scripts/aws_helper.py --action empty_bucket --bucket $$UI_BUCKET || true; \
	fi
	@ACCOUNT_ID=$$(python3.12 ../scripts/aws_helper.py --action get_account 2>/dev/null || echo ""); \
	if [ -n "$$ACCOUNT_ID" ] && [ "$$ACCOUNT_ID" != "None" ]; then \
		ARTIFACTS_BUCKET="multimodal-video-search-artifacts-$$ACCOUNT_ID"; \
		echo "🧹 Emptying Artifacts Bucket $$ARTIFACTS_BUCKET before deletion..."; \
		python3.12 ../scripts/aws_helper.py --action empty_bucket --bucket $$ARTIFACTS_BUCKET || true; \
		python3.12 ../scripts/aws_helper.py --action delete_bucket --bucket $$ARTIFACTS_BUCKET || true; \
	fi
	sam delete --no-prompts
	@$(MAKE) clean

clean:
	@echo "Cleaning up local build artifacts..."
	rm -rf .aws-sam
	@echo "Clean complete."

refresh:
	@echo "🔄 Refreshing Frontend and Backend..."
	@echo "📦 Building Frontend..."; \
	cd ../frontend && npm install && npm run build && cd ../cloud-backend; \
	echo "🔨 Building SAM Application..."; \
	sam build -t $(TEMPLATE_FILE) && \
	echo "☁️ Deploying SAM Application..."; \
	sam deploy --no-confirm-changeset --no-fail-on-empty-changeset && \
	UI_BUCKET=$$(python3.12 ../scripts/aws_helper.py --action get_stack_output --stack $(STACK_NAME) --logical_id UiBucketName 2>/dev/null || echo ""); \
	if [ -n "$$UI_BUCKET" ]; then \
		echo "☁️ Pushing Frontend directly to UI Bucket: $$UI_BUCKET"; \
		python3.12 ../scripts/aws_helper.py --action upload --bucket $$UI_BUCKET --source ../frontend/dist; \
	fi; \
	REGION=$$(python3 -c "import boto3; print(boto3.session.Session().region_name or 'us-east-1')" 2>/dev/null || echo "us-east-1"); \
	echo "🎉 Refresh Complete! Frontend is live at: http://$$UI_BUCKET.s3-website-$$REGION.amazonaws.com"
