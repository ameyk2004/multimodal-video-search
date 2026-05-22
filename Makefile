
upload-metadata:
	@echo "Uploading metadata to DynamoDB..."
	source .env && python3 data_pipeline/dynamo_uploader.py
