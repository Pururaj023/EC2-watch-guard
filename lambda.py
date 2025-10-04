import boto3
import datetime

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

# Hardcoding SNS ARN (you can also set via ENV variable)
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:889279754965:ec2-monitor-topic"

def lambda_handler(event, context):
    # Get current time in UTC
    now = datetime.datetime.now(datetime.timezone.utc)

    # -------- Part 1: Check Running Instances (>1 hour) --------
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            launch_time = instance['LaunchTime']  # UTC datetime

            # Calculate running time
            running_time = now - launch_time

            if running_time.total_seconds() > 3600:  # more than 1 hour
                message = (
                    f"⚠️ EC2 Instance {instance_id} has been running for "
                    f"{running_time.total_seconds()/3600:.2f} hours."
                )
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message,
                    Subject="EC2 Instance Running Too Long"
                )

    # -------- Part 2: Detect EC2 Instance Creation --------
    # If Lambda is invoked by EventBridge EC2 event
    if "detail-type" in event and event["detail-type"] == "EC2 Instance State-change Notification":
        instance_id = event["detail"]["instance-id"]
        state = event["detail"]["state"]

        if state == "running":  # notify only when instance is launched/started
            message = f"✅ New EC2 Instance {instance_id} is now in '{state}' state."
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject="EC2 Instance Launched"
            )

    return {"status": "completed"}
