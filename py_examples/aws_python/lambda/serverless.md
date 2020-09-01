# serverless commands

<!-- install serverless -->
npm i -g serverless

<!-- create python template -->
serverless create --template aws-python

<!-- deploy lambda service. The output has URL that can be used to access the function-->
sls deploy --aws-profile serverless-admin

<!-- invoke function and capture logs -->
serverless invoke --function hello --log --aws-profile serverless-admin

<!-- remove lambda service-->
sls remove --aws-profile serverless-admin

<!-- install -->
sls plugin install -n serverless-python-requirements
