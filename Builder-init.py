import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.info("Starting Lambda")
    print(event)

    # setup session connections
    client = boto3.client("sts")
    assume_resp = client.assume_role(
        RoleArn="arn",
        RoleSessionName="Builder-Init",
        ExternalId="AMIBuildTeam"
        )
    sqsclient = boto3.client("sqs")
    assumed_session = boto3.Session(aws_access_key_id=assume_resp["Credentials"]["AccessKeyId"],aws_secret_access_key=assume_resp["Credentials"]["SecretAccessKey"], aws_session_token=assume_resp["Credentials"]["SessionToken"])

    org_client = assumed_session.client("organizations")
    org_client_paginator = org_client.get_paginator("list_accounts")
    receipt_handle = event['Records'][0]['receiptHandle']
    amiId = event['Records'][0]['messageAttributes']['amiId']['stringValue']
    amiName = event['Records'][0]['messageAttributes']['amiName']['stringValue']
    snapId = event['Records'][0]['messageAttributes']['snapshotId']['stringValue']

    for account in org_client_paginator.paginate().build_full_result()["Accounts"]:
        if str(account["Status"])=="ACTIVE":
            sqlresp = sqsclient.send_message(
                QueueUrl="https://sqs.us-east-1.amazonaws.com/",
                DelaySeconds=10,
                MessageBody="{0}, {1}, {2}, {3}".format(amiId, amiName, snapId, account['Id']),
                MessageAttributes={
                    "amiId":{
                        "DataType": "String",
                        "StringValue": str(amiId)
                    },
                    "amiName":{
                        "DataType": "String",
                        "StringValue": str(amiName)
                    },
                    "snapId":{
                        "DataType": "String",
                        "StringValue": str(snapId)
                    },
                    "accountId":{
                        "DataType": "String",
                        "StringValue": account['Id']
                    }
                }
                )
            print("{0}, {1}, {2}".format(amiId, amiName, snapId, account['Id']))
