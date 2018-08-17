import boto3
from operator import itemgetter



################################################################################
# Variables for local testing - THESE WILL NOT BE USED IF RUNNING FROM A LAMBDA
################################################################################
### Set this to the AWS Profile name for the account you want to test in
TEST_PROFILE = 'default'

################################################################################
# Configuration List
################################################################################
ami_name_list = [
                    {
                        'name_filter': 'amzn-ami-hvm-*x86_64-gp2',
                        'target_description': "Newest Amazon Linux AMI ID",
                        'target_name': "SourceAmazonLinux",
                        'owner': 'amazon'
                    },
                    {
                        'name_filter': 'amzn2-ami-hvm-*x86_64-gp2',
                        'target_description': "Newest Amazon Linux 2 AMI ID",
                        'target_name': "SourceAmazonLinux2",
                        'owner': '137112412989'
                    },
                    {
                        'name_filter': ['CentOS Linux 6 x86_64 HVM EBS*'],
                        'target_description': "Newest CentOS6 AMI ID",
                        'target_name': "SourceCentOS6",
                        'owner': '679593333241'
                    },
                    {
                        'name_filter': ['CentOS Linux 7 x86_64 HVM EBS *'],
                        'target_description': "Newest CentOS7 AMI ID",
                        'target_name': "SourceCentOS7",
                        'owner': '679593333241'
                    },
                    {
                        'name_filter': 'Windows_Server-2016-English-Full-Base*',
                        'target_description': "Latest AWS Windows 2016 AMI",
                        'target_name': "Source2016",
                        'owner': '801119661308'
                    },
                    {
                        'name_filter': 'Windows_Server-2016-English-Full-ECS_Optimized-*',
                        'target_description': "Latest AWS Windows 2016 ECS AMI",
                        'target_name': "Source2016ECS",
                        'owner': 'amazon'
                    },
                    {
                        'name_filter': 'Windows_Server-2016-English-Core-Base*',
                        'target_description': "Latest AWS Windows 2016 Core AMI",
                        'target_name': "Source2016Core",
                        'owner': '801119661308'
                    },
                    {
                        'name_filter': 'Windows_Server-2012-R2_RTM-English-64Bit-Base*',
                        'target_description': "Newest Windows 2012 R2 AMI ID",
                        'target_name': "Source2012",
                        'owner': '801119661308'
                    },
                    {
                        'name_filter': 'ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-*',
                        'target_description': "Newest Ubuntu AMI ID",
                        'target_name': "SourceUbuntu",
                        'owner': '099720109477'
                    }
                ]

#######################################
### Function: lambda_handler
def lambda_handler(event, context):
    print(context)
    print(event)
    # If we're running within the Lambda framework, the try will succeed and pull in the data.
    try:
        invoke_arn = context.invoked_function_arn
        thisAccountsId = invoke_arn.split(':')[4]
        thisRegion = invoke_arn.split(':')[3]
        profile = None
    # If we're running local for testing, we'll populate the data here instead
    except:
        thisAccountsId = None
        thisRegion = 'us-east-1'
        profile = TEST_PROFILE

    # Initialize AWS_Clients session
    session = boto3.Session(region_name=thisRegion, profile_name=profile)

    # Create an ssm client
    ssm_client = session.client('ssm')
    ec2_client = session.client('ec2')

    # Request AWS EC2 Parameter

    for item in ami_name_list:
        get_response = ec2_client.describe_images(
                                                    ExecutableUsers=['all'],
                                                    Filters=[
                                                        {
                                                            'Name': 'name',
                                                            'Values': [item['name_filter']]
                                                        },
                                                        {
                                                            'Name': 'state',
                                                            'Values': ['available']
                                                        }
                                                    ],
                                                    Owners=[item['owner']]
                                                )
        item['ImageCount'] = len(get_response['Images'])
        if item['ImageCount'] > 0:
            latest = sorted(get_response['Images'], key=itemgetter('CreationDate'))[-1]
            item['amiId'] = latest['ImageId']
            item['creationDate'] = latest['CreationDate']

            put_response = ssm_client.put_parameter(Name=item['target_name'],
                                                    Description=item['target_description'] + " - " + latest['CreationDate'],
                                                    Value = latest['ImageId'],
                                                    Type='String',
                                                    Overwrite=True
                                                    )

        print(item)
        #print(put_response)

#######################################
### HELPER: If we're running locally, this will kick off the lambda_handler function
if __name__ == '__main__':
    lambda_handler('', '')
