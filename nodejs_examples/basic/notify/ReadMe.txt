https://medium.com/izettle-engineering/beginners-guide-to-web-push-notifications-using-service-workers-cb3474a17679

#Frontend
npm install -g http-server
npm install -g web-push
web-push generate-vapid-keys # provides public key and private key

#Frontend run
http-server

#Backend
npm init
npm install --save express

#Backend run
node index.js # copy private key and public key
