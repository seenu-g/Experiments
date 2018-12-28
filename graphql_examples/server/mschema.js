//https://mlab.com/databases/dbgraphql/collections/books
const graphql = require('graphql');
const Book = require('./book');
const Author = require('./author');
const _ = require('lodash');

const{ 
    GraphQLObjectType, GraphQLString, GraphQLSchema,
    GraphQLID,GraphQLInt,GraphQLList,GraphQLNonNull
    } = graphql;

// dummy data
var books = [
    { name: 'Name of the Wind', genre: 'Fantasy', id: '1', authorId: '1' },
    { name: 'The Final Empire', genre: 'Fantasy', id: '2', authorId: '2' },
    { name: 'The Hero of Ages', genre: 'Fantasy', id: '4', authorId: '2' },
    { name: 'The Long Earth', genre: 'Sci-Fi', id: '3', authorId: '3' },
    { name: 'The Colour of Magic', genre: 'Fantasy', id: '5', authorId: '3' },
    { name: 'The Light Fantastic', genre: 'Fantasy', id: '6', authorId: '3' },
];

var authors = [
    { name: 'Patrick Rothfuss', age: 44, id: '1' },
    { name: 'Brandon Sanderson', age: 42, id: '2' },
    { name: 'Terry Pratchett', age: 66, id: '3' }
];

const BookType = new GraphQLObjectType({
    name: 'Book',
    fields: ( ) => ({
        id: { type: GraphQLID },
        name: { type: GraphQLString },
        genre: { type: GraphQLString },
        author: {
            type: AuthorType,
            resolve(parent, args){
                //console.log(parent);
                //return _.find(authors, { id: parent.authorId });
                return Author.findById(parent.authorId);
            }
        }
    })
});

const AuthorType = new GraphQLObjectType({
    name: 'Author',
    fields: ( ) => ({
        id: { type: GraphQLID },
        name: { type: GraphQLString },
        age: { type: GraphQLInt },
        books: {
            type: new GraphQLList(BookType),
            resolve(parent, args){
                //return _.filter(books, { authorId: parent.id });
                return Book.find({ authorId: parent.id });
            }
        }
    })
});

const RootQuery = new GraphQLObjectType({
    name: 'RootQueryType',
    fields: {
        book: {   // book will name of attribute in result
            type: BookType,
            args: { id: { type: GraphQLID } },
            resolve(parent, args){
                //console.log(typeof(args.id));
                // code to get data from db / other source
                //return _.find(books, { id: args.id });
                return Book.findById(args.id);
            }
        },
        author: {
            type: AuthorType,
            args: { id: { type: GraphQLID } },
            resolve(parent, args){
                //return _.find(authors, { id: args.id });
                return Author.findById(args.id);
            }
        },
        books:{
            type: new GraphQLList(BookType),
            resolve(parent, args){
                return Book.find({}); // returns all books
            }
        },
        authors:{
            type: new GraphQLList(AuthorType),
            resolve(parent, args){
                return Author.find({}); // returns all authors
            }
        }
    }
});

const Mutation = new GraphQLObjectType({
    name: 'Mutation',
    fields: {
        addAuthor: {
            type: AuthorType,
            args: {
                name: { type: new GraphQLNonNull(GraphQLString) },
                age: { type: GraphQLInt }
            },
            resolve(parent, args){
                let author = new Author({
                    name: args.name,
                    age: args.age
                });
                return author.save();
            }
        },
        addBook: {
            type: BookType,
            args: {
                name: { type: new GraphQLNonNull(GraphQLString) },
                genre: { type:  GraphQLString },
                authorId: { type: new GraphQLNonNull(GraphQLID) }
            },
            resolve(parent, args){
                let book = new Book({
                    name: args.name,
                    genre: args.genre,
                    authorId: args.authorId
                });
                return book.save();
            }
        }

    }
});

module.exports = new graphql.GraphQLSchema({
    query: RootQuery,
    mutation: Mutation
});

/*
mutation{
  addAuthor(name:"Patrick Rothfuss",age: 44){
        name
        age
      }
}
mutation{
  addAuthor(name:"Brandon Sanderson",age: 42){
        name
        age
      }
}
mutation{
  addAuthor(name:"Terry Pratchett",age: 66){
        name
        age
      }
}
mutation{
    addBook(name:"Name of the Wind", genre:"Fantasy", authorId: ){
        name
        genre
        authorId
    }
}
mutation{
    addBook(name:"The Final Empire", genre:"Fantasy", authorId: ){
        name
        genre
    }
}
mutation{
    addBook(name:"The Hero of Ages", genre:"Fantasy", authorId: ){
        name
        genre
    }
}
mutation{
    addBook(name:"The Long Earth", genre:"Sci-Fi", authorId: ){
        name
        genre
    }
}
mutation{
    addBook(name:"The Colour of Magic", genre:"Fantasy", authorId: ){
        name
        genre
    }
}
mutation{
    addBook(name:"The Light Fantastic", genre:"Fantasy", authorId: ){
        name
        genre
    }
}
*/

/*
{
  author(id : "5c25d7985882542324c35fdf"){
    name
    age
    books{
      name
      genre
      id
    }
  }
}
*/
/*
{
  authors{
    name
    age
  }
}
*/
/*
{
    book(id:""){
        name
        genre
        author{
            name
            books {
                name
            }
        }
    }
}
*/