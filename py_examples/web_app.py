# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 22:08:24 2019

@author: g.srinivasan
"""
#pip install virtualenv
#pip install virtualenvwrapper-win
#pip install Flask

from flask import Flask, jsonify,abort, make_response, url_for
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

actions = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Machine learning',
        'description': u'Need to find a good machine learning sample data and tutorial on the web', 
        'done': False
    }
]
#http://127.0.0.1:5000/todo/api/v1.0/actions
@app.route('/todo/api/v1.0/actions', methods=['GET'])
def get_actions():
    return jsonify({'actions': actions})

#http://127.0.0.1:5000/todo/api/v1.0/actions/2
@app.route('/todo/api/v1.0/actions/<int:action_id>', methods=['GET'])
def get_action(action_id):
    action = [action for action in actions if action['id'] == action_id]
    if len(action) == 0:
        abort(404)
    return jsonify({'action': action[0]})

#http://127.0.0.1:5000/todo/api/v1.0/actions/2
@app.route('/todo/api/v1.0/actions/<int:action_id>', methods=['DELETE'])
def delete_action(action_id):
    action = [action for action in actions if action['id'] == action_id]
    if len(action) == 0:
        abort(404)
    actions.remove(action[0])
    return jsonify({'result': True})

def make_public_action(action):
    new_action = {}
    for field in action:
        if field == 'id':
            new_action['uri'] = url_for('get_action', action_id=action['id'], _external=True)
        else:
            new_action[field] = action[field]
    return new_action

@app.route('/todo/api/v1.0/actionURLs', methods=['GET'])
def get_actionURLs():
    return jsonify({'actions': [make_public_action(action) for action in actions]})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)