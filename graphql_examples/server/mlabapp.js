const express = require('express');
const graphqlHTTP = require('express-graphql');
const schema = require('./mschema');
const mongoose = require('mongoose');
const cors = require('cors');

const app = express();

// allow cross-origin requests
app.use(cors());

// connect to mlab database
// make sure to replace my db string & creds with your own
mongoose.connect('mongodb://srini:Accion123@ds125469.mlab.com:25469/dbgraphql')
mongoose.connection.once('open', () => {
    console.log('application connected to database');
});

// bind express with graphql
app.use('/graphql', graphqlHTTP({
    schema, // pass in a schema property
    graphiql: true

}));

app.listen(4000, () => {
    console.log('now listening for requests on port 4000');
});  //http://localhost:4000/graphql
