import boto3
import logging
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logging.info("Starting Lambda")
#    print(event)
    accountId = event['Records'][0]['messageAttributes']['accountId']['stringValue']
    amiId = event['Records'][0]['messageAttributes']['amiId']['stringValue']
    amiName = event['Records'][0]['messageAttributes']['amiName']['stringValue']
    snapId = event['Records'][0]['messageAttributes']['snapId']['stringValue']
    amiList = []    #List of AMI IDs and regions from the copy image process
    print(accountId, amiId, amiName, snapId)

    ec2 = boto3.client('ec2')
    regions = ec2.describe_regions()
    print(regions)
    # for region in regions['Regions']:
    #     print(region['RegionName'])
    #     amiList.append(str(region['RegionName'])+':'+str(amiId))
    # print(amiList)

    share_ami = boto3.client('ec2')
    launch_permissions = {"Add": []}
    launch_permissions['Add'].append({"UserId": accountId})

    modifyLaunchPermission = ec2.modify_image_attribute(ImageId=amiId,
                                    LaunchPermission=launch_permissions
                                        )
    print("modifyLaunchPermission =",modifyLaunchPermission)

    create_volume_permission = {"Add": []}
    create_volume_permission['Add'].append({"UserId": accountId})
    print("createVolumeResponse= ",create_volume_permission)

    describe_image = ec2.describe_images(ImageIds=[amiId], Owners=['752576941788'])
    print("Describe image =",describe_image)
    #quit()


    for block_device in describe_image['Images'][0]['BlockDeviceMappings']:
#        try:
        snapshot_id=(block_device['Ebs']['SnapshotId'])
        print("snapshotId =",snapshot_id)
        modifySnapResponse=ec2.modify_snapshot_attribute(Attribute='createVolumePermission',CreateVolumePermission=create_volume_permission,SnapshotId=snapshot_id)
        print("modifySnapResponse= ",modifySnapResponse)
#        except:
#            pass

    for region in regions['Regions']:
        print(region['RegionName'])
        regionName = region['RegionName']
        try:
            print(" in loop --> ", regionName,amiName,amiId)
            ec2 = boto3.client('ec2', region_name=regionName)
            copyAMIResponse = ec2.copy_image(SourceRegion='us-east-1',SourceImageId=amiId,Name="-".join([amiName,datetime.datetime.now().strftime('%Y-%m-%d'),]))
            print("copyAMIResponse= ",copyAMIResponse)
            quit()
        except Exception as e:
            print("errorFound = ",e)
