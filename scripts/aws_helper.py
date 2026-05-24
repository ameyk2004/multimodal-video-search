import os
import mimetypes
import boto3
import argparse
import sys

def upload_directory_to_s3(bucket_name, source_dir):
    s3 = boto3.client('s3')
    
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename == "config.json":
                continue # Skip config.json
                
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, source_dir)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(local_path)
            if content_type is None:
                content_type = 'binary/octet-stream'
                
            print(f"Uploading {relative_path} to s3://{bucket_name}/{relative_path} ({content_type})")
            s3.upload_file(
                local_path, 
                bucket_name, 
                relative_path,
                ExtraArgs={'ContentType': content_type}
            )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', required=True, choices=['get_account', 'create_bucket', 'upload', 'empty_bucket', 'delete_bucket', 'get_stack_bucket', 'list_buckets', 'get_stack_output', 'invalidate'])
    parser.add_argument('--bucket', required=False)
    parser.add_argument('--source', required=False)
    parser.add_argument('--stack', required=False)
    parser.add_argument('--logical_id', required=False)
    parser.add_argument('--distribution_id', required=False)
    args = parser.parse_args()

    if args.action == 'get_account':
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity().get('Account')
        print(account_id)
        
    elif args.action == 'get_stack_bucket':
        if not args.stack or not args.logical_id:
            sys.exit(1)
        cfn = boto3.client('cloudformation')
        try:
            res = cfn.describe_stack_resource(StackName=args.stack, LogicalResourceId=args.logical_id)
            print(res['StackResourceDetail']['PhysicalResourceId'])
        except:
            pass

    elif args.action == 'get_stack_output':
        if not args.stack or not args.logical_id:
            sys.exit(1)
        cfn = boto3.client('cloudformation')
        try:
            res = cfn.describe_stacks(StackName=args.stack)
            outputs = res['Stacks'][0].get('Outputs', [])
            for out in outputs:
                if out['OutputKey'] == args.logical_id:
                    print(out['OutputValue'])
                    sys.exit(0)
        except:
            pass

    elif args.action == 'empty_bucket':
        if not args.bucket: sys.exit(1)
        s3 = boto3.resource('s3')
        try:
            bucket = s3.Bucket(args.bucket)
            bucket.objects.all().delete()
        except:
            pass

    elif args.action == 'delete_bucket':
        if not args.bucket: sys.exit(1)
        s3 = boto3.client('s3')
        try:
            s3.delete_bucket(Bucket=args.bucket)
        except:
            pass
        
    elif args.action == 'create_bucket':
        if not args.bucket:
            print("Missing --bucket")
            sys.exit(1)
        s3 = boto3.client('s3')
        try:
            s3.head_bucket(Bucket=args.bucket)
            print(f"Bucket {args.bucket} already exists")
        except:
            print(f"Creating bucket {args.bucket}")
            # mb doesn't need LocationConstraint for us-east-1
            session = boto3.session.Session()
            region = session.region_name
            if region == 'us-east-1' or not region:
                s3.create_bucket(Bucket=args.bucket)
            else:
                s3.create_bucket(
                    Bucket=args.bucket,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
                
    elif args.action == 'upload':
        if not args.bucket or not args.source:
            print("Missing --bucket or --source")
            sys.exit(1)
        upload_directory_to_s3(args.bucket, args.source)
        
    elif args.action == 'list_buckets':
        s3 = boto3.client('s3')
        for bucket in s3.list_buckets().get('Buckets', []):
            print(bucket['Name'])
            
    elif args.action == 'invalidate':
        if not args.distribution_id:
            print("Missing --distribution_id")
            sys.exit(1)
        cf = boto3.client('cloudfront')
        import time
        try:
            res = cf.create_invalidation(
                DistributionId=args.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': 1,
                        'Items': ['/*']
                    },
                    'CallerReference': str(time.time())
                }
            )
            invalidation_id = res['Invalidation']['Id']
            print(f"🚀 Started invalidation {invalidation_id} for CloudFront {args.distribution_id}")
            print("⏳ Waiting for CloudFront edge caches to clear globally (this usually takes 1-3 minutes)...")
            
            waiter = cf.get_waiter('invalidation_completed')
            waiter.wait(
                DistributionId=args.distribution_id,
                Id=invalidation_id,
                WaiterConfig={
                    'Delay': 15,
                    'MaxAttempts': 60
                }
            )
            print(f"✅ CloudFront invalidation completed 100%! New UI is fully live globally.")
        except Exception as e:
            print(f"Failed to invalidate: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
