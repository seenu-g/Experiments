# Create IAM user with programmatic access and also attache the policy "AmazonEC2FullAccess"
# Confiugr this IAM user using aws configure to run the code.

import boto3
    
def get_EC2_Key_pair(ec2):
    key_pair = None
    try:
        # create a file to store the key locally
        outfile = open('ec2-keypair.pem','w')
        # # call the boto ec2 function to create a key pair
        key_pair = ec2.create_key_pair(KeyName='ec2-keypair')
    except Exception as e:
        print(e)
        return False
    
    try:
        # capture the key and store it in a file
        KeyPairOut = str(key_pair.key_material)
        print(KeyPairOut)
        outfile.write(KeyPairOut)
    except Exception as e:
        print(e)
        return False

def create_new_EC2_instance(ec2):
    instance ={}
    try :
        #create a new EC2 instance
        instance = ec2.create_instances(
            ImageId='ami-02354e95b39ca8dec',
            MinCount=1,
            MaxCount=2,
            InstanceType='t2.micro',
            KeyName='ec2-keypair' #defines the name of the key pair that will allow access to the instance. 
        )  
    except Exception as e:
        print(e)
        return False
    print (instance[0].id)

def get_instance(ec2,id) :
    instance = None
    try:
         instance = ec2.Instance(id)
    except Exception as e:
        print(e)
        return False
    if(instance != None):
        print("Details of instance:", id)
        print("instance_type:",instance.instance_type)
        print("launch_time:",instance.launch_time)
        print("instance_id:",instance.instance_id)
        print("image_id",instance.image_id)
        print(instance.placement)
        print(instance.cpu_options)
        print(instance.public_ip_address)
        print(instance.public_dns_name)
        print(instance.tags)
        print(instance.state)

def remove_instance(ec2,id) :
    instance = None
    try:
         instance = ec2.Instance(id)
         if(instance != None):
              instance.stop(Force=True)
              instance.terminate()
    except Exception as e:
        print(e)
        return False
    
# Create IAM user with programmatic access and also attache the policy "AmazonEC2FullAccess"
# Confiugr this IAM user using aws configure to run the code.
def main():
    ec2 = boto3.resource('ec2')
    #get_EC2_Key_pair(ec2)
    #create_new_EC2_instance(ec2)
    
    # When uncommentin the create function above, please code below.
    id = "i-083c0dd8d474342cc"
    get_instance(ec2,id)
    remove_instance(ec2,id)

# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()