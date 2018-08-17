import json
import boto3
import datetime

print('Loading function')

######
# Function: Update SSM Parameters
def update_ssm_parameter(event):
    # get SSM client
    client = boto3.client('ssm')

    #confirm  parameter exists before updating it
    response = client.describe_parameters(
       Filters=[
          {
           'Key': 'Name',
           'Values': [event['parameterName']]
          },
        ]
    )

    if not response['Parameters']:
        print('No such parameter')
        return 'SSM parameter not found.'

    #if parameter has a Descrition field, update it PLUS the Value
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

    reponseString = 'Updated parameter %s with value %s.' % (event['parameterName'], event['parameterValue'])

    print(reponseString)

def get_aws_accounts(event):
    ssm = boto3.client('ssm')
    # Obtain the comma-delmited list of account numbers from SSM Parameter
    parameter = ssm.get_parameter(
        Name='RETS_aws_accounts',
        WithDecryption=False
    )

    # Then split the value on the comma to generate a python list object
    accounts = parameter['Parameter']['Value'].split(",")
    return accounts

def share_ami(event, accounts):
    image_id = event['parameterValue']
    ec2 = boto3.client('ec2')

    # The "LaunchPermissions" parameter needs to be a json dict following the
    # structure defined in the boto3 documentation
    # http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.modify_image_attribute
    # Example Dict:
    # {'Add': [{'UserId': '111111111111'}, {'UserId': '222222222222'}, {'UserId': '333333333333'}]}

    launch_permissions = {"Add": []}

    for account in accounts:
        launch_permissions['Add'].append({"UserId": account})

    response = ec2.modify_image_attribute(ImageId=image_id,
                                    LaunchPermission=launch_permissions
                                        )
    print(response)

def share_snapshot(event, accounts):
    image_id = event['parameterValue']
    ec2 = boto3.client('ec2')

    # The "CreateVolumePermission" parameter needs to be a json dict following the
    # structure defined in the boto3 documentation
    # http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.modify_image_attribute
    # Example Dict:
    # {'Add': [{'UserId': '111111111111'}, {'UserId': '222222222222'}, {'UserId': '333333333333'}]}

    create_volume_permission = {"Add": []}

    for account in accounts:
        create_volume_permission['Add'].append({"UserId": account})

    # describe the image, to discover the snapshot IDs
    response = ec2.describe_images(ImageIds=[image_id])
    print(response)

    # For each snapshot id we found, modify it's attributes to share it out to the account list
    for block_device in response['Images'][0]['BlockDeviceMappings']:
        try:
            snapshot_id = block_device['Ebs']['SnapshotId']
            response=ec2.modify_snapshot_attribute(  Attribute='createVolumePermission',
                                                        CreateVolumePermission=create_volume_permission,
                                                        SnapshotId=snapshot_id)
            print(response)
        except:
            pass

def copy_ami(event):
    image_id = event['parameterValue']
    target_regions = ['eu-west-1','ap-southeast-1','ap-southeast-2','us-west-1','us-east-2','us-west-2']

    global_image_ids = []

    for region in target_regions:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.copy_image( SourceRegion='us-east-1',
                        SourceImageId=image_id,
                        Name="-".join([event['parameterName'],
                        datetime.datetime.now().strftime('%Y-%m-%d')]))
        print(response)
        global_image_ids.append({'Region': region, 'ImageId': response['ImageId']})
    global_image_ids.append({'Region': 'us-east-1', 'ImageId': image_id})
    return global_image_ids

def publish_notification(event,global_image_ids):
    sns = boto3.client('sns')
    global_image_ids = json.dumps(global_image_ids).replace('"','\"')
    response=sns.publish(TopicArn='arn',
                        Subject='AMI Release {0}'.format(event['parameterName']),
                        MessageStructure='json',
                        Message = json.dumps({
                            "default": '{0}'.format(global_image_ids)#,
#                            "email": "New versions of the following RETS Hardened AMIs have been published: {0}".format(global_image_ids),
              #              "lambda": global_image_ids
                        })
    )
    print(response)

#Expects parameterName, parameterValue
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    update_ssm_parameter(event)
    accounts = get_aws_accounts(event)
    share_ami(event, accounts)
    share_snapshot(event, accounts)
    global_image_ids = copy_ami(event)
    publish_notification(event,global_image_ids)
