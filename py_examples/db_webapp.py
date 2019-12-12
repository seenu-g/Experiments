# -*- coding: utf-8 -*-
#download SQLlite3 and add executable folder to windows PATH
#.databases
#.tables
#CREATE TABLE books(id INT primary key, title varchar, author varchar, year_published varchar,meta_data varchar);
#.schema books
# insert into books(id,title,author,year_published,meta_data) values(1,"Machine Learning","Ramjee",2008,"cook book");
# insert into books(id,title,author,year_published,meta_data) values(2,"Learn Python","Saurabh",2002,"cook book");
# insert into books(id,title,author,year_published,meta_data) values(3,"Learn R","R",2001,"cook book"),(4,"Learn Ethereum","Vitalik",2016,"cook book");
# SELECT * FROM books;
#sqlite3 mydb.db
#.quit

#pip install Flask-SQLAlchemy
#pip install Flask-Restful
#pip install jsonify
#pip install SQlite3

import flask
from flask import request, jsonify
import sqlite3
from sqlite3 import Error

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Distant Reading Archive</h1>
      <p>A prototype API for distant reading of science fiction novels.</p>'''

@app.route('/api/v1/resources/books/all', methods=['GET'])
def api_all():
    conn = None
    try:
        conn = sqlite3.connect('.\mydb.db')
        #conn.row_factory = dict_factory
        #print(sqlite3.version)
        cur = conn.cursor()
        id = 0
        all_books = cur.execute("SELECT * FROM books where id > ?", (id,)).fetchall()
        return jsonify(all_books)
        #for book in all_books:
        #    print(book)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404
##book(2,"Who ate Cheese", 'Raymond', 1975, "life")               
def create_book(book):
    conn = None
    try:
        conn = sqlite3.connect('.\mydb.db')
        sql = ''' INSERT INTO books(id,title,author,year_published,meta_data)
              VALUES(?,?,?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, book)
        return cur.lastrowid
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def delete_book(id):
    conn = None
    try:
        conn = sqlite3.connect('.\mydb.db')
        sql = 'DELETE FROM books WHERE id=?'
        cur = conn.cursor()
        cur.execute(sql, (id,))
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

#book("Fountain Head", 'Ayan Rand', 1969, "idealism",2)               
def update_book(book):
    conn = None
    try:
        conn = sqlite3.connect('.\mydb.db')
        sql = ''' UPDATE books
              SET title = ? ,
                  author = ? ,
                  year_published = ?,
                  meta_data = ?
              WHERE id = ?'''
        cur = conn.cursor()
        cur.execute(sql, book)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
app.run()