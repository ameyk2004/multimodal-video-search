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
	@# 1. Create Artifacts Bucket if it doesn't exist
	@ACCOUNT_ID=$$(python3.12 ../scripts/aws_helper.py --action get_account 2>/dev/null || echo "") ; \
	if [ -n "$$ACCOUNT_ID" ] && [ "$$ACCOUNT_ID" != "None" ]; then \
		ARTIFACTS_BUCKET="multimodal-video-search-artifacts-$$ACCOUNT_ID" ; \
		echo "📦 Creating/verifying Artifacts Bucket: $$ARTIFACTS_BUCKET" ; \
		python3.12 ../scripts/aws_helper.py --action create_bucket --bucket $$ARTIFACTS_BUCKET ; \
		echo "📦 Building Frontend..." ; \
		cd ../frontend && npm install && npm run build && cd ../cloud-backend ; \
		echo "☁️ Uploading Frontend to Artifacts Bucket..." ; \
		python3.12 ../scripts/aws_helper.py --action upload --bucket $$ARTIFACTS_BUCKET --source ../frontend/dist ; \
		echo "🔄 Updating SAM config with Secrets and UiArtifactsBucket=$$ARTIFACTS_BUCKET..." ; \
		python3 -c "import sys; sys.path.insert(0,'../scripts'); from packaging import load_env, update_samconfig; update_samconfig(load_env('../.env'), {'UiArtifactsBucket': '$$ARTIFACTS_BUCKET'})" ; \
	else \
		echo "⚠️ AWS CLI failed. Skipping frontend artifacts sync..." ; \
		python3 -c "import sys; sys.path.insert(0,'../scripts'); from packaging import load_env, update_samconfig; update_samconfig(load_env('../.env'))" ; \
	fi
	@# 2. Try a non-interactive deploy
	@if sam deploy \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		2>/dev/null; then \
		echo ""; \
		echo "✅ Stack updated successfully!"; \
		WEBSITE_URL=$$(aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" --output text 2>/dev/null); \
		echo "🎉 Frontend is live at: $$WEBSITE_URL"; \
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
