#### iam commands

<!--Administrator belongs to admin group-->
aws configure --profile Administrator

<!--- credentials file is located at ~/.aws/credentials on Linux or macOS
config file is located at ~/.aws/config on Linux or macOS -->
aws configure set region us-west-2 --profile integ
aws configure get region --profile Administrator

aws configure import –csv /Users/srinivasang/credentials.csv
aws configure list-profiles <!-- list all your profile names -->
aws configure list

aws s3 ls --profile Administrator <!-- luse profile name with S3 -->

<!-- list all users >
aws iam list-users --profile Administrator

#### create group

aws iam create-group --group-name MyIamGroup --profile Administrator

#### create user

aws iam create-user --user-name MyUser

#### add user to group

aws iam add-user-to-group --user-name MyUser --group-name MyIamGroup

#### Check whether user is present in the group

aws iam get-group --group-name MyIamGroup

#### set password

aws iam create-login-profile --user-name MyUser --password 'XXX@789' --password-reset-required

#### create policy and attach policy to user

export POLICYARN=$(aws iam list-policies --query 'Policies[?PolicyName==`PowerUserAccess`].{ARN:Arn}' --output text)
echo $POLICYARN
aws iam attach-user-policy --user-name MyUser --policy-arn $POLICYARN

#### check whether user is attached to the policy.

aws iam list-attached-user-policies --user-name MyUser

## check whether user is attached to the policy.
aws iam list-attached-user-policies --user-name MyUser