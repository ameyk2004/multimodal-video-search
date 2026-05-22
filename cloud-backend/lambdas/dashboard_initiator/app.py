import json
import urllib.request
import urllib.error
import boto3

def send_cfn_response(event, context, response_status, response_data, physical_resource_id=None, no_echo=False):
    response_url = event['ResponseURL']
    print(response_url)
    response_body = {
        'Status': response_status,
        'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': physical_resource_id or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }
    json_response_body = json.dumps(response_body).encode('utf-8')
    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }
    try:
        req = urllib.request.Request(response_url, data=json_response_body, headers=headers, method='PUT')
        with urllib.request.urlopen(req) as response:
            print("Status code:", response.getcode())
    except Exception as e:
        print("send(..) failed executing requests.put(..):", e)

def handler(event, context):
    try:
        request_type = event['RequestType']
        if request_type == 'Delete':
            send_cfn_response(event, context, 'SUCCESS', {})
            return
            
        props = event['ResourceProperties']
        bucket = props['BucketName']
        api_url = props['ApiUrl']
        
        config_content = json.dumps({"VITE_API_URL": api_url})
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket=bucket,
            Key='config.json',
            Body=config_content,
            ContentType='application/json',
            CacheControl='no-cache'
        )
        
        send_cfn_response(event, context, 'SUCCESS', {})
    except Exception as e:
        print("Error:", e)
        send_cfn_response(event, context, 'FAILED', {})
