# AWS Lambda subscribes to S3 events

## Creating S3 Bucket

- Create s3 bucker of name lambdawiths3

## Create Role that Works with S3 and Lambda

- Create IAM Role
- Select Lambda
- Add Permission AmazonS3FullAccess, AWSLambdaFullAccess and CloudWatchFullAccess.
- Save Role

## Create Lambda function and Add S3 Trigger

- Create lambda function based on NodeJS
- add the S3 trigger.
-- Specify bucket name to whose event lambda subscribes
-- Select Object Created (All), as we need AWS Lambda trigger when file is uploaded, removed etc.
--  add Prefix and File pattern  to filter the files added for which trigger happens

## Here is lambda code in NodeJS

exports.handler = function(event, context, callback) {
   console.log("Incoming Event: ", event);
   const bucket = event.Records[0].s3.bucket.name;
   const filename = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
   const message = `File is uploaded in - ${bucket} -> ${filename}`;
   console.log(message);
   callback(null, message);
};

## Associate create lambda with created role

## upload files to S# and watch Cloudwatch

--select CloudWatch. Open the logs for the Lambda function 
--AWS Lambda function gets triggered when file is uploaded in S3 bucket and the details are logged in Cloudwatch