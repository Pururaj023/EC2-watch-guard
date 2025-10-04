# 🖥️ AWS EC2 Monitoring with Lambda, CloudWatch Events & SNS

## 📘 Overview
This project automates EC2 instance monitoring using **AWS Lambda**, **CloudWatch Events**, and **SNS**.  
It performs two key functions:
1. **Detects and notifies** when a new EC2 instance is launched.
2. **Monitors EC2 runtime** — if any instance runs for more than **1 hour**, it sends a warning notification.

This automation helps reduce **unnecessary cloud costs** and provides **better visibility** into EC2 activity.

---

## ⚙️ Architecture
**AWS Services Used:**
- **Lambda:** Executes the monitoring logic automatically.
- **CloudWatch Events (EventBridge):** Triggers the Lambda function on EC2 state changes.
- **SNS (Simple Notification Service):** Sends email notifications to subscribed users.
- **EC2:** The monitored service.

**Workflow:**
1. When a new EC2 instance enters the **running** state, **CloudWatch Events** trigger the **Lambda function**.  
2. Lambda sends an **SNS email notification** to inform the user of the new instance.  
3. Lambda also periodically checks all running instances.  
   - If any instance has been running for more than **1 hour**, it sends a **warning email** with the instance ID and runtime.

---

## 🧠 How It Works

### 1. EC2 Instance Creation Alert
Triggered via **CloudWatch Event**:
- Event type: `EC2 Instance State-change Notification`
- When an instance state = `running`, Lambda sends an SNS email:
  > ✅ New EC2 Instance i-0abcd12345 is now in 'running' state.

### 2. Long-Running Instance Detection
Lambda also queries all EC2 instances using the **EC2 API**:
- Filters instances in the `running` state.
- Compares current time with `LaunchTime`.
- If runtime > 1 hour, sends an SNS alert:
  > ⚠️ EC2 Instance i-0abcd12345 has been running for 1.25 hours.

---

## 📄 Code Explanation

```python
import boto3
import datetime

ec2 = boto3.client('ec2')
sns = boto3.client('sns')
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:889279754965:ec2-monitor-topic"

def lambda_handler(event, context):
    now = datetime.datetime.now(datetime.timezone.utc)

    # Part 1: Check instances running >1 hour
    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            launch_time = instance['LaunchTime']
            running_time = now - launch_time
            if running_time.total_seconds() > 3600:
                message = f"⚠️ EC2 Instance {instance_id} has been running for {running_time.total_seconds()/3600:.2f} hours."
                sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="EC2 Instance Running Too Long")

    # Part 2: Detect EC2 creation via CloudWatch Event
    if "detail-type" in event and event["detail-type"] == "EC2 Instance State-change Notification":
        instance_id = event["detail"]["instance-id"]
        state = event["detail"]["state"]
        if state == "running":
            message = f"✅ New EC2 Instance {instance_id} is now in '{state}' state."
            sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject="EC2 Instance Launched")

    return {"status": "completed"}
