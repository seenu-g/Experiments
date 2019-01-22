from pymongo import MongoClient
connection = MongoClient("ds125469.mlab.com", 25469)
db = connection['dbgraphql']
db.authenticate("srini", "Accion123")

print 'List Collections'
print db.collection_names()

collist = db.collection_names()
if "books" in collist:
  print("books collection exists.")
if "authors" in collist:
      print("authors collection exists.")

books = db['books']
print(books.count())
tempBooks = books.find().sort("genre")
for item in tempBooks:
    print (item['name'] , item['genre'])

authors = db['authors']
print( authors.count())
tempAuthors = authors.find({'age': {'$gte': 43}})
for item in tempAuthors:
    print (item['name'] , item['age'])


# newAuthor = { "name": "Akilan", "age":88 }
# x = authors.insert_one(newAuthor)
# print(x.inserted_id) 

myquery = { "genre": "Fantasy" }
fantasybooks = books.find(myquery)
for y in fantasybooks:
    print (y['name'] , y['genre'])

connection.close()
