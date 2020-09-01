# output

  POST - https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model
  GET - https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model
  GET - https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model/{todo_id}
  DELETE - https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model/{todo_id}


<!-- TEST API Endpoints -->
<!--create-->
curl -X POST https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model --data '{ "text": "Learn AWS Lambda" }'
curl -X POST https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model --data '{ "text": "Learn Docker & Kubernetes"}' 
curl -X POST https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model --data '{ "text": "Learn AI/ML" }' 
<!-- list-->
curl -X GET https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model 
<!-- get one passing todo_ID received as output of earlier command-->
curl -X GET https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model/1a282ab8-ec43-11ea-b16e-a2a5d1a5d2e6


curl -X DELETE https://bricz2qbj7.execute-api.us-east-1.amazonaws.com/dev/model/1a282ab8-ec43-11ea-b16e-a2a5d1a5d2e6


