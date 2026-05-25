import boto3
import time

def get_logs():
    client = boto3.client('logs', region_name='us-east-1')
    log_group = '/aws/lambda/multimodal-video-search-SadhanaNandadeepSearchFunc-fIJa18nyTWBd'
    
    # Get latest log stream
    streams = client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    
    if not streams['logStreams']:
        print("No log streams found.")
        return
        
    stream_name = streams['logStreams'][0]['logStreamName']
    print(f"Fetching logs from {stream_name}")
    
    events = client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        limit=50
    )
    
    for event in events['events']:
        print(event['message'].strip())

if __name__ == '__main__':
    get_logs()
