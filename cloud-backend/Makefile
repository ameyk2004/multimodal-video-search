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
	@# Try a non-interactive deploy (works if stack already exists and creds are set)
	@if sam deploy \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		2>/dev/null; then \
		echo ""; \
		echo "✅ Stack updated successfully!"; \
		echo ""; \
		sam list stack-outputs --stack-name $(STACK_NAME); \
	else \
		echo "Stack not found or credentials missing. Generating Quick Create link..."; \
		python3 ../scripts/packaging.py; \
	fi

teardown:
	@echo "Tearing down AWS CloudFormation stack..."
	sam delete --no-prompts
	@$(MAKE) clean

clean:
	@echo "Cleaning up local build artifacts..."
	rm -rf .aws-sam
	@echo "Clean complete."
