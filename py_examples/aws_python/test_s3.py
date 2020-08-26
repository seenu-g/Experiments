import boto3

# Create IAM user with programmatic access and also attache the policy "AmazonS3FullAccess"
# Confiugr this IAM user using aws configure to run the code.
import uuid
def create_bucket_name(bucket_prefix):
    # The generated bucket name must be between 3 and 63 chars long
    return ''.join([bucket_prefix, str(uuid.uuid4())])

def create_bucket(s3_client,bucket_name, region=None):
    bucket_response = None
    try:
        if region is None:
            bucket_response = s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            bucket_response = s3_client.create_bucket(Bucket=bucket_name,CreateBucketConfiguration=location)
    except Exception as e:
        print(e)
        return False
    if bucket_response != None:
        print(bucket_name,"created")
        return bucket_name

def delete_bucket(s3_client,bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except Exception as e:
        print(e)
        return False    
    print(bucket_name,"deleted")

def get_buckets(s3_client):
    response = None
    try:
          # Call S3 to list current buckets
          response = s3_client.list_buckets()
    except Exception as e:
        print("Oops!", e.__class__, "occurred.")
        
    if(response!= None) :
        # Get a list of all bucket names from the response
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        #print(response['Buckets'])
        #dates = [bucket['CreationDate'] for bucket in response['Buckets']]
        
        # Print out the bucket list
        print("Bucket List: %s" % buckets)
    else :
        print("No buckets got returned")

def get_bucket_policy(s3_client,bucket_name):

    response = None
    try:
        response = s3_client.get_bucket_policy(
            Bucket = bucket_name
        )
    except Exception as e:
        print(e)
        
    if(response!= None) :
        print(" Bucket Policy:",response['Policy'])

def upload_object(s3_resource,bucket_name,file_name,key_name):
         
    try:
        # Uploads the given file using a managed uploader, which will split up large
        # files automatically and upload parts in parallel.
        s3_resource.Bucket(name=bucket_name).upload_file(file_name, key_name)
    except Exception as e:
        print(e)
        return
    print(key_name,"created in", bucket_name)

def delete_object(s3_resource,bucket_name,key_name):
    try :
        s3_resource.Object(bucket_name, key_name).delete()
    except Exception as e:
        print(e)
        return
    print(key_name,"deleted from", bucket_name)

# Create IAM user with programmatic access and also attache the policy "AmazonS3FullAccess"
# Confiugr this IAM user using aws configure to run the code.
def main() : 
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')

    get_buckets(s3_client)
    """ bucket_name = create_bucket(s3_client,create_bucket_name("soai"))
    upload_object(s3_resource,bucket_name,file_name="/Users/srinivasang/Desktop/Rajesh.pdf",key_name="temp.pdf")
    upload_object(s3_resource,bucket_name,file_name="/Users/srinivasang/Desktop/Technical Landscape.jpg",key_name="temp.jpg")
    delete_object(s3_resource,bucket_name,"temp.pdf")
    delete_object(s3_resource,bucket_name,"temp.jpg")
    delete_bucket(s3_client,bucket_name) """
    
# this means that if this script is executed, then 
# main() will be executed
if __name__ == '__main__':
    main()