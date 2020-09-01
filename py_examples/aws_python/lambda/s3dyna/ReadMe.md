
# create deployment

# $URL is the base URL specified in the POST 

URL="https://gighrnwof0.execute-api.us-east-1.amazonaws.com/dev/asset"

# Get an asset pre-signed upload URL

curl -sX POST $URL | json_pp

-- Take value of upload_url in output of executing the above command and set the value SIGNED_URL
SIGNED_URL="https://s3dynauploader.s3.amazonaws.com/test/34e27fe2-ec80-11ea-8cf7-d2fbca33bb2c?AWSAccessKeyId=ASIASGHOWJK5SVAEZDFD&Signature=EjCwXjCFrfTtY5vyA5%2BOBAkP%2B6M%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEIP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCh4KGXd8sPvZRDHSqtPgsWvB0g9v6olnZkKEkygjgELQIgXVSN5n8xMKBJUOEZz19obNGUq5TPmOUN9PLgdwdCfskq1gEIfBADGgwxNTA4MjQ0Mzg0NTkiDGCDCSTe%2FAoTOA%2B4iSqzAaYlThD%2BswVTdgMk1xi5BFxEhoPg3K%2FOanOwXUa4zKYVEgE3Jr9dLxa58u%2FPKBNtHENmliaGXAkwRW9h5MrowDwD3QUgMlcS4vjoooHfJISDRcACKy0q2w6LeYFEQUByhPsdufpKwzXQg2m%2Fl9H5HnTok%2FQBZxgx8uWAr1otw3yhVmAQePngJFbEQOsLldoEVNvP6TEC5ty3%2Fj7emi2TIzRUY9VEBN4ZxeV%2FqIk4PUM2gH3HMNeluvoFOuAB2uAJGLfNXbg1ANO5TICgcSvsvBkHdB4KpmBWPMwfz7QALinrZg%2FbV4Sl9yIZjXHoCECC6IijSCUDVtdW6dz0QktnxaMLcdqZhjaKvRjIH2B5oqXKqfaHKWJJu6FQhHB3VM%2B6qaz22N0YpRm4hD0q2dSoQMdLNKTRmaMxMV251RQ%2F5u2bSytZDFZ6Cs8nVrKqqFOEGArOQFHIAKal5rAoln%2BmD7HqN2mZpnM%2B8wRNin4l%2B87GejkuwkivBC%2Bg92hSwOa%2BhcYjWfeFh2VUXfv18e1tpH0my63%2FAH%2BtTcG3Byw%3D&Expires=1598985217" 

# Upload a file to the URL

curl -sX PUT --upload-file requirements.txt $SIGNED_URL

# Upload a file after pre-signed URL has expired

 curl -sX PUT --upload-file serverless.yml $SIGNED_URL

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

SIGNED_URL="https://s3dynauploader.s3.amazonaws.com/test/34e27fe2-ec80-11ea-8cf7-d2fbca33bb2c?AWSAccessKeyId=ASIASGHOWJK5SVAEZDFD&Signature=EjCwXjCFrfTtY5vyA5%2BOBAkP%2B6M%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEIP%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIQCh4KGXd8sPvZRDHSqtPgsWvB0g9v6olnZkKEkygjgELQIgXVSN5n8xMKBJUOEZz19obNGUq5TPmOUN9PLgdwdCfskq1gEIfBADGgwxNTA4MjQ0Mzg0NTkiDGCDCSTe%2FAoTOA%2B4iSqzAaYlThD%2BswVTdgMk1xi5BFxEhoPg3K%2FOanOwXUa4zKYVEgE3Jr9dLxa58u%2FPKBNtHENmliaGXAkwRW9h5MrowDwD3QUgMlcS4vjoooHfJISDRcACKy0q2w6LeYFEQUByhPsdufpKwzXQg2m%2Fl9H5HnTok%2FQBZxgx8uWAr1otw3yhVmAQePngJFbEQOsLldoEVNvP6TEC5ty3%2Fj7emi2TIzRUY9VEBN4ZxeV%2FqIk4PUM2gH3HMNeluvoFOuAB2uAJGLfNXbg1ANO5TICgcSvsvBkHdB4KpmBWPMwfz7QALinrZg%2FbV4Sl9yIZjXHoCECC6IijSCUDVtdW6dz0QktnxaMLcdqZhjaKvRjIH2B5oqXKqfaHKWJJu6FQhHB3VM%2B6qaz22N0YpRm4hD0q2dSoQMdLNKTRmaMxMV251RQ%2F5u2bSytZDFZ6Cs8nVrKqqFOEGArOQFHIAKal5rAoln%2BmD7HqN2mZpnM%2B8wRNin4l%2B87GejkuwkivBC%2Bg92hSwOa%2BhcYjWfeFh2VUXfv18e1tpH0my63%2FAH%2BtTcG3Byw%3D&Expires=1598985217" 

# Download asset

curl -sX GET $SIGNED_URL  --output file.txt

# Download asset with expired URL

curl -sX GET $SIGNED_URL

# remove deployment

sls remove  --aws-profile serverless-admin