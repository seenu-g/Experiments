## **S3 commands**

#### create bucket 
aws s3api create-bucket --bucket seenu-models --region us-east-1

#### list bucket contents
aws s3 ls s3://mobisirgsvasan
aws s3 ls s3://soai

#### delete bucket
aws s3 rb s3://mobisirsrini

#### copy files from local folder to s3
aws s3 cp Rajesh.pdf s3://soai/temp1.pdf

#### delete bucket
aws s3 rb s3://mobisirsrini
#### delete object present in bucket
aws s3 rm s3://soai/temp1.pdf 
#### delete recursively
aws s3 rm s3://soai --recursive

#### copy files to S3 and back
aws s3 cp Rajesh.pdf s3://soai/temp1.pdf
aws s3 cp /Users/srinivasang/Desktop/Rajesh.pdf s3://soai/temp1.pdf
aws s3api put-object --bucket soai --key test/ 
aws s3api put-object --bucket soai --key test/temp.pdf --body /Users/srinivasang/Desktop/Rajesh.pdf
aws s3 ls s3://soai

#### associate policy with S3
aws s3api put-bucket-policy --bucket soai --policy file://s3_all_policy.json --profile Administrator
aws s3api get-bucket-policy --bucket soai --profile Administrator
aws s3api delete-bucket-policy --bucket soai --profile Administrator
# generates policy skeleton for customization
aws s3api put-bucket-acl --bucket soai --generate-cli-skeleton

#### control access to S3
#### #Deny for dev-gsvasan
aws s3 ls s3://soai --profile dev-gsvasan
aws s3 ls s3://soai --profile dev-srini