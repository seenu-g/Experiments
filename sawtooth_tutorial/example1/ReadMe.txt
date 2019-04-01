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

//In Local machine
// To completely reset the Sawtooth environment and start from first
// To view logs
sudo ls -l /var/log/sawtooth
// To delete the blockchain data, remove all files from /var/lib/sawtooth. 
  rm -R /var/lib/sawtooth/*
// To delete the Sawtooth logs, remove all files from /var/log/sawtooth/.
// find /var/log/sawtooth/ -mtime +1 -name *.log -exec rm -rf {} \;
// find /var/log/sawtooth/ -name *.log -exec rm -rf {} \;
// To delete the Sawtooth keys, remove the key files /etc/sawtooth/keys/validator.\* and /home/yourname/.sawtooth/keys/yourname.\*.
// Ensure that sawtooth keys are generated // use --force if needed to overwrite existing files
sawtooth keygen

sawset genesis
sudo -u sawtooth sawadm genesis config-genesis.batch

// Generate root key for validator // use --force if needed
sudo sawadm keygen

// start Validator  in separate terminal
sudo -u sawtooth sawtooth-validator -vv

//Run devmode consenus engine
sudo -u sawtooth devmode-engine-rust -vv --connect tcp://localhost:5050

//start REST API // defauly output is "Running on http://127.0.0.1:8008" 
sudo -u sawtooth sawtooth-rest-api -v

//start settings processor
sudo -u sawtooth settings-tp -v

//check if setting returns values set
sawtooth settings list

// start intkey processor. You can test values go to validator
sudo -u sawtooth intkey-tp-python -v

intkey create_batch --count 10 --key-count 5
intkey load -f batches.intkey
