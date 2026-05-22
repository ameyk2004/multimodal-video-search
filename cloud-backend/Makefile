.PHONY: build deploy teardown clean release

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
	@# Sync .env secrets into samconfig.toml
	@python3 -c "import sys; sys.path.insert(0,'../scripts'); from packaging import load_env, update_samconfig; update_samconfig(load_env('../.env'))"
	@# Try a non-interactive deploy
	@if sam deploy \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		2>/dev/null; then \
		echo ""; \
		echo "✅ Stack updated successfully!"; \
		UI_BUCKET=$$(aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='UiBucketName'].OutputValue" --output text 2>/dev/null); \
		WEBSITE_URL=$$(aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" --output text 2>/dev/null); \
		if [ -n "$$UI_BUCKET" ] && [ "$$UI_BUCKET" != "None" ]; then \
			echo "📦 Building Frontend..."; \
			cd ../frontend && npm install && npm run build; \
			echo "☁️ Uploading Frontend to $$UI_BUCKET..."; \
			aws s3 sync dist s3://$$UI_BUCKET/ --exclude "config.json"; \
			echo ""; \
			echo "🎉 Frontend is live at: $$WEBSITE_URL"; \
		fi; \
		sam list stack-outputs --stack-name $(STACK_NAME); \
	else \
		echo "Stack not found or credentials missing. Generating Quick Create link..."; \
		python3 ../scripts/packaging.py; \
	fi

teardown:
	@echo "Tearing down AWS CloudFormation stack..."
	@UI_BUCKET=$$(aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='UiBucketName'].OutputValue" --output text 2>/dev/null || echo ""); \
	if [ -n "$$UI_BUCKET" ] && [ "$$UI_BUCKET" != "None" ]; then \
		echo "🧹 Emptying UI Bucket $$UI_BUCKET before deletion..."; \
		aws s3 rm s3://$$UI_BUCKET --recursive || true; \
	fi
	sam delete --no-prompts
	@$(MAKE) clean

clean:
	@echo "Cleaning up local build artifacts..."
	rm -rf .aws-sam
	@echo "Clean complete."
