# Sawtooth_Meetup
Hands on session on June 1st at Pingala

i) Docker installation:
   
 sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

 sudo apt-get update
 sudo apt-get install -y docker-ce
 sudo usermod -aG docker ${USER}
 su - ${USER} 
 sudo usermod -aG docker <username>

ii) Docker Compose installation:

 sudo apt-get install build-essential

 sudo curl -L "https://github.com/docker/compose/releases/download/1.23.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

 sudo chmod +x /usr/local/bin/docker-compose


iii) clone the repository

    git clone https://github.com/reginaldshub/Sawtooth_Meetup.git

    
iv) steps to execute structured-bank

 1) start the validator:

   a) cd Sawtooth_Meetup/structured-bank
   b) docker-compose -f sawtooth-default.yaml up

2) Run Processor

   a)cd Sawtooth_Meetup/structured-bank/processor
   b)npm install
   c)node index.js

3) Run Client

   a)cd Sawtooth_Meetup/structured-bank/client
   b)npm install

  i) Create account

    ex: node app.js 'regi' '{"verb":"create_account","customer_id":"101","customer_name":"regi","savings_balance":5000,"checking_balance":3000}'

   'regi'-> is the username  to create keys to sign the transaction
   "checking_balance" -> is the wallet balance

  ii)To deposit money from account
    ex: node app.js 'regi' '{"verb":"deposit_money","customer_id":"101","amount":2000}'

  iii)To withdraw money from account
  ex: node app.js 'regi' '{"verb":"withdraw_money","customer_id":"101","amount":4000}'

  iv)To transfer money from account

   Note: To transfer money  we need to create another account  with  different id.

   ex: node app.js 'regi' '{"verb":"transfer_money","source_customer_id":"101","dest_customer_id":"102", "amount":1000}'


