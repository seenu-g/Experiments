import json
import datetime
import time


def hello(event, context):
    current_time = datetime.datetime.now().time()
    body = {
        "message": "Hello from Serverless! " + str(current_time)
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    
    print("Function Name, Function Version :",context.function_name, context.function_version)
    print("invoked_function_arn: ",context.invoked_function_arn)

    print("Log stream name: ", context.log_stream_name)
    print("Log group name: ",  context.log_group_name)
    print("Request ID: ",context.aws_request_id)
        
    print("Mem. limits(MB):", context.memory_limit_in_mb)
    #  Code will execute quickly, so we add a 1 second intentional delay so you can see that in time remaining value.
    time.sleep(5) 
    print("Time remaining (MS):", context.get_remaining_time_in_millis())
    
    return response