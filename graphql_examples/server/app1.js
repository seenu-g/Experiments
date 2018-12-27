const express = require('express');
const graphqlHTTP = require('express-graphql');
const schema = require('./schema1');

const app = express();

// bind express with graphql
app.use('/graphql', graphqlHTTP({
    schema1, // pass in a schema property
    graphiql: true

}));

app.listen(4000, () => {
    console.log('now listening for requests on port 4000');
});  //http://localhost:4000/graphql
