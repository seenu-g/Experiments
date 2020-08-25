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
       
def create_user(iam,user_name):

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

def delete_user(iam,user_name):

    try:
        # Create user
        response = iam.delete_user(
            UserName=user_name
        )
    except Exception as e:
        print(e)
        return False
    print(response)   
    return True

def get_user(iam,user_name=None):
    print ("\n Get User")
    user_response = None
    try :
        if(user_name != None):
            user_response = iam.get_user(UserName=user_name)
        else:
            user_response = iam.get_user()
    except Exception as e :
        print(e)
        return False
    #user_response = iam.get_user(UserName='dev-srini')
    print("User Details :", user_response)
    
def attach_policy(iam, user_name,policy_arn):
    try:
        iam.attach_user_policy(
            UserName = user_name, 
            PolicyArn = policy_arn
        )
    except Exception as e :
        print(e)
        return False
    return True
def detach_policy(iam, user_name,policy_arn):
    try:
        iam.detach_user_policy(
        UserName = user_name, 
        PolicyArn = policy_arn
        )
    except Exception as e :
        print(e)
        return False
    return True

def get_users(iam):
    print ("\n Get All Users")
    try :
        for user in iam.list_users()['Users']:
            print("User: {0} ARN : {1} UserID: {2} Created On: {3}\n".format(
                    user['UserName'],user['Arn'],user['UserId'],user['CreateDate']
                    )
                )
    except Exception as e :
        print(e)
        return False
        
def main() :

    session = get_session_details()
    get_local_user_profiles(session)
    get_current_user(session)

    iam = boto3.client('iam')    

    get_user(iam)
    new_user ="mili"
    #create_user(iam,new_user)
    #get_user(iam,new_user)
    #get_users(iam)
    
    ec2_policy = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
    #attach_policy(iam,new_user,ec2_policy)
    #detach_policy(iam,new_user,ec2_policy)
    #delete_user(iam,new_user)
    
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()