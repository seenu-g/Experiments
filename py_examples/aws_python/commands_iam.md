#### iam commands

<!--Administrator belongs to admin group-->
<!-- create profile -->
aws configure --profile Administrator

<!--- credentials file is located at ~/.aws/credentials on Linux or macOS
config file is located at ~/.aws/config on Linux or macOS -->
aws configure set region us-west-2 --profile integ
aws configure get region --profile Administrator

aws configure import –csv /Users/srinivasang/credentials.csv
aws configure list-profiles <!-- list all your profile names -->
aws configure list

aws s3 ls --profile Administrator <!-- luse profile name with S3 -->

<!-- where are credential and config present on linux or macOs -->
ls ~/.aws
cat ~/.aws/credentials
cat ~/.aws/config

<!-- Once you set local environment variable using export paramter, you can call without mentioning --profile -->
export AWS_PROFILE=dev-srini,
aws s3 ls 
<!-- You can unset this  -->
unset AWS_PROFILE

<!-- list all users -->
aws iam list-users --profile Administrator

<!-- create group -->
aws iam create-group --group-name MyIamGroup --profile Administrator
<!-- create user -->
aws iam create-user --user-name MyUser --profile Administrator

<!-- AWS user is identified by arn:aws:iam::account-ID-without-hyphens:user/MyUser
# if there is console access, access using URL https://<<numberic>>.signin.aws.amazon.com/console -->

<!-- add user to group -->
aws iam add-user-to-group --user-name MyUser --group-name MyIamGroup --profile Administrator
<!-- Check whether user is present in the group -->
aws iam get-group --group-name MyIamGroup --profile Administrator
aws iam get-group  --profile Administrator
<!-- set password -->
aws iam create-login-profile --user-name MyUser --password 'XXX@789' --password-reset-required --profile Administrator
<!-- get user -->
aws iam get-user --user-name MyUser --profile Administrator
<!-- list all groups-->
aws iam list-groups --profile Administrator
<!-- get group details -->
aws iam get-group --group-name MyIamGroup --profile Administrator
<!-- get groups that user belong to  -->
aws iam  list-groups-for-user --user-name MyUser --profile Administrator

<!-- create policy and attach policy to user -->
export POLICYARN=$(aws iam list-policies --query 'Policies[?PolicyName==`PowerUserAccess`].{ARN:Arn}' --output text)
echo $POLICYARN
aws iam attach-user-policy --user-name MyUser --policy-arn $POLICYARN --profile Administrator

aws iam attach-group-policy --group-name MyIamGroup --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile Administrator
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile Administrator

<!-- list policies to check whether user is attached to the policy -->
aws iam list-attached-user-policies --user-name MyUser --profile Administrator
aws iam list-user-policies --user-name MyUser --profile Administrator  

aws iam list-ssh-public-keys --profile Administrator
aws iam list-service-specific-credentials --profile Administrator
aws iam list-access-keys --profile Administrator
aws iam list-signing-certificates --profile Administrator
<!-- describe about Administrator -->
aws opsworks --region us-east-1 describe-my-user-profile --profile Administrator
<!-- describe ec2 instances -->
aws ec2 describe-instances --profile Administrator
