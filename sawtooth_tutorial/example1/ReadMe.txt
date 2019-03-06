Example 1

// download .yaml file from website.
mv sawtooth-default.yaml docker-compose.yaml
docker-compose up
docker-compose down

//this will shutdown sawtooth
docker-compose -f sawtooth-default.yaml down

// to delete container
docker rm name_of_the_docker_container
// some times you have to run the above multiple times.


// Prior to run server, test environment by running the following in another terminal window, send transactions to your validator:
intkey create_batch
intkey load

// Prior to run client ## Generate public/private keys and a placeholder Sawtooth REST API URL
node init.js

// By default, the intkey client will attempt to connect to a Sawtooth REST API at http://localhost:8008.
// To connect to a REST API at a different URL, please edit .env file
// The next time you run node index.js the URL you specified in .env will be used automatically
/  To host of HTTPS, use https://, set the host to the public domain address of your server, and use port 8888.


//Once you got server and client working. You can look at validator terminal to verify whether blocks are mined
// Go to Browser and navigate to URL
http://localhost:8008/state



