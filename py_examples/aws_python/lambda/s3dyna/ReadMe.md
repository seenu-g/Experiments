# $URL is the base URL specified in the POST 

export URL="https://r8nkn0ipda.execute-api.us-east-1.amazonaws.com/dev/asset"

# Get an asset pre-signed upload URL

curl -sX POST URL | json_pp

# Mark asset as uploaded

curl -sX PUT $URL/fe9102b4-ec76-11ea-a3b8-eed5525ef6d5 | json_pp

# Get download URL for asset:

curl -sX GET $URL/fe9102b4-ec76-11ea-a3b8-eed5525ef6d5 | json_pp

# List all assets

curl -sX GET $URL | json_pp

# Get one Asset download URL

curl -sX GET $URL/57226ed30e-11e7-bda4-129b5a655d2d | json_pp

# Delete an asset

curl -sX DELETE $URL/947f8a20-ec77-11ea-a3b8-eed5525ef6d5 | json_pp

# Download asset

curl -sX GET "<SIGNED_URL>"  --output file.txt

# Download asset with expired URL

curl -sX GET "<SIGNED_URL>"