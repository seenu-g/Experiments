const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");

const app = express();
app.use(cors());
app.use(bodyParser.json());

const port = 4000;

app.get("/", (req, res) => res.send("Hello World!"));

const dummyDb = { subscription: null }; //dummy in memory store

const saveToDatabase = async subscription => {
  // Since this is a demo app, I am going to save this in a dummy in memory store. Do not do this in your apps.
  // Here you should be writing your db logic to save it.
  dummyDb.subscription = subscription;
};

// The new /save-subscription endpoint
app.post("/save-subscription", async (req, res) => {
  const subscription = req.body;
  await saveToDatabase(subscription); //Method to save the subscription to Database
  res.json({ message: "success" });
});

app.listen(port, () => console.log(`Example app listening on port ${port}!`));


const vapidKeys = {
  publicKey:
    'BMVcnU5eg9d8pe9b6e61CFKxbp7ZWozwXqULsWQLIUAWa_FwemHC5PJoKr72AMVP5tT7WCmOGlJIMvN2YB637vM',
  privateKey: 'VhFmFOHtsI2jf1mGO9GZkKSOf6HAcXrLbwEMEU3caPw',
}
//setting our previously generated VAPID keys
webpush.setVapidDetails(
  'mailto:srinivasan.gsvasan@gmail.com',
  vapidKeys.publicKey,
  vapidKeys.privateKey
)

//function to send the notification to the subscribed device
const sendNotification = (subscription, dataToSend) => {
  webpush.sendNotification(subscription, dataToSend)
}
//route to test send notification
app.get('/send-notification', (req, res) => {
  const subscription = dummyDb.subscription //get subscription from your databse here.
  const message = 'Hello World'
  sendNotification(subscription, message)
  res.json({ message: 'message sent' })
})
app.listen(port, () => console.log(`Example app listening on port ${port}!`))