from flask import Flask, jsonify, abort, make_response #abort(404)
from flask.ext.httpauth import HTTPBasicAuth
from random import randint

app = Flask(__name__)

@app.route('/login/<number>')
def getRandomPyme(number):
	print 'Creado'
	return jsonify(msg = 'Creado')

@app.errorhandler(404)
def not_found():
	return make_response(jsonify({'error':'not found'}),404)

if __name__ ==  '__main__' : 
	app.run(host='0.0.0.0') #11633
