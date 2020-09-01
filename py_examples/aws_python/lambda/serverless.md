# serverless commands

<!-- install serverless -->
npm i -g serverless

<!-- create python template -->
serverless create --template aws-python 

<!-- deploy lambda service-->
sls deploy --aws-profile serverless-admin

<!-- remove lambda service-->
sls remove --aws-profile serverless-admin