import boto3

def get_session_details():
    # Create an S3 client
    session = boto3.session.Session()
    if(session!= None) :
       print("\n EC2 Regions:")
       print(session.get_available_regions('ec2'))
                     
       print(session.get_available_partitions)
       print(session.get_available_resources)
       print(session.get_available_services) 
    return session    

def get_current_user(session):
    if(session!= None) :
        identity = session.client('sts').get_caller_identity()
        print(identity['Account'])
        print(identity['Arn'])
    
def get_local_user_profiles(session):
    if(session!= None) :
       print("Session alive")
       print(session.available_profiles)
       
def create_user(user_name):
    # Create IAM client
    iam = boto3.client('iam')
    try:
        # Create user
        response = iam.create_user(
            UserName=user_name
        )
    except Exception as e:
        print(e)
        return False
    print(response)   
    return True

def get_bucket_policy(bucket_name):
     # Create an S3 client
    s3 = boto3.client('s3')
    response = None

    try:
        response = s3.get_bucket_policy(
            Bucket = bucket_name
        )
    except Exception as e:
        print(e)
        
    if(response!= None) :
        print(" Bucket Policy:",response['Policy'])
        
def main() :
    iam = boto3.resource('iam')
    current_user = iam.CurrentUser()
    print("Current user is ",current_user)
    
    session = get_session_details()
    get_local_user_profiles(session)
    get_current_user(session)
    #create_user("mili")
    get_bucket_policy("eva4-2")

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()