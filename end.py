from flask import Flask, jsonify, abort, make_response #abort(404)
#from flask.ext.httpauth import HTTPBasicAuth
from random import randint
from neoConnector import neo
from datetime import datetime

app = Flask(__name__)

def checkPhoneNode(phone,name):
	phone,name = str(phone), str(name)
	if neoCon.nodeExists(phone,key='phone'): return neoCon.getNode(phone,key='phone')	
	else:           return neoCon.createNode({'name':name,'phone':phone},labels=['person'])

@app.route('/login/<phone>/<name>')
def login(phone,name):
	a = checkPhoneNode(phone,name)
	return jsonify(name=a.properties['name'],phone=a.properties['phone'])

@app.route('/contacts/<originphone>/<originname>/<friendphone>/<friendname>')
def addFriend(origin_phone,origin_name,friend_phone,friend_name): #DEBE EXISTIR O TRONARA
	origin = checkPhoneNode(origin_phone,origin_name)
	friend = checkPhoneNode(friend_phone,friend_name)
	today = datetime.now().strftime("%Y-%m-%d")
	'''Relacion Yo -> Amigo'''
	ends = (rel.end for rel in origin.relationships.outgoing()) 	
	if friend in ends: print 'YA EXISTE'
	else:  neoCon.relateNodes(origin,friend,{'since':today},'Knows')
	'''Relacion Amigo -> Yo'''
	ends = (rel.end for rel in friend.relationships.outgoing())
	if origin in ends: print 'YA EXISTE'
	else:  neoCon.relateNodes(friend,origin,{'since':today},'Knows')
	return jsonify(msg='success')

@app.route('/contacts/<originphone>/debts/<tophone>/<amount>/<due_date>')
def addDebt(origin_phone,friend_phone,amount,due_date):
	origin = checkPhoneNode(origin_phone,origin_name)
	friend = checkPhoneNode(friend_phone,friend_name)
	today = datetime.now().strftime("%Y-%m-%d")
	dt = {
		'since':today,
		'due_date':due_date,
		'amount':amount,
		'rule':'',
	}
	print neoCon.relateNodes(origin,friend,dt,'Lends')
	return jsonify(msg='success')

if __name__ ==  '__main__' :
	neoCon = neo(host = 'http://the.rabit.club:7474/')
	app.run(host='0.0.0.0',port='6666') #11633
