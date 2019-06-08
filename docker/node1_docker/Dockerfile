FROM node:8

# Create app directory
WORKDIR /usr/src/app
# Install app dependencies. Copy both package.json AND package-lock.json 
# do not copy entire contents http://bitjudo.com/blog/2014/03/13/building-efficient-dockerfiles-node-dot-js/
COPY package*.json ./
# install dependencies
RUN npm install
# production
# RUN npm install --only=production
COPY . .
#export listening port in container to localhost
EXPOSE 8080
CMD [ "npm", "start" ]
# CMD [ "node", "server.js" ]