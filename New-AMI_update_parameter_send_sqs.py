from __future__ import print_function

import json
import boto3
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

print('Loading function')


#Updates an SSM parameter
#Expects parameterName, parameterValue
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # get SSM client
    client = boto3.client('ssm')

    #confirm  parameter exists before updating it
    response = client.describe_parameters(
       Filters=[
          {
           'Key': 'Name',
           'Values': [ event['parameterName'] ]
          },
        ]
    )

    if not response['Parameters']:
        print('No such parameter')
        return 'SSM parameter not found.'

    #if parameter has a Description field, update it PLUS the Value
    if 'Description' in response['Parameters'][0]:
        description = response['Parameters'][0]['Description']

        response = client.put_parameter(
          Name=event['parameterName'],
          Value=event['parameterValue'],
          Description=description,
          Type='String',
          Overwrite=True
        )

    #otherwise just update Value
    else:
        response = client.put_parameter(
          Name=event['parameterName'],
          Value=event['parameterValue'],
          Type='String',
          Overwrite=True
        )

    # describe the image, to discover the snapshot IDs
    ec2 = boto3.client('ec2')
    image_id = event['parameterValue']
    response = ec2.describe_images(ImageIds=[image_id])
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        try:
            snapshot_id = str(block_device['Ebs']['SnapshotId'])
            print(snapshot_id)
            type(snapshot_id)


        except:
            pass



    #Sends SQS with AMI ID, AMI Name and Snapshot ID
    sqsclient = boto3.client('sqs')
    sqlresp = sqsclient.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/",
        DelaySeconds=10,
        MessageBody="{0}, {1}".format(event['parameterName'],event['parameterValue']),
        MessageAttributes={
            'amiId':{
                'DataType': 'String',
                'StringValue': str(event['parameterValue'])
            },
            'amiName':{
                'DataType': 'String',
                'StringValue': str(event['parameterName'])
            },
            'snapshotId':{
                'DataType': 'String',
                'StringValue': snapshot_id
            }
        }
    )
#    logger.info(str(event['parameterValue']), str(event['parameterName']), snapshot_id
