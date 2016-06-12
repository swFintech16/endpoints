from flask import Flask, jsonify, abort, make_response #abort(404)
#from flask.ext.httpauth import HTTPBasicAuth
from random import randint
from neoConnector import neo
from datetime import datetime
app = Flask(__name__)

def checkPhoneNode(phone,name):
	phone,name = str(phone), str(name)
	if '_' in name: name = name.replace('_',' ')
	if neoCon.nodeExists(phone,key='phone'): return neoCon.getNode(phone,key='phone')	
	else:           return neoCon.createNode({'name':name,'phone':phone,'amount':0,'description':''},labels=['person'])
def amountMoneyNeeds(phone):
	k = checkPhoneNode(phone,'Needio Money')
	am = k.properties['amount']
	if am<0:
		for i in k.relationships.incoming():
			print i
		return am*-1


	else: #Es numero verde, el anda prestando
		print 'No necesita dinero'
		return 0


@app.route('/')
def t(phone,name):
	print 'Working'

@app.route('/login/<phone>/<name>')
def login(phone,name):
	a = checkPhoneNode(phone,name)
	return jsonify(name=a.properties['name'],phone=a.properties['phone'])

@app.route('/contacts/<origin_phone>/<origin_name>/<friend_phone>/<friend_name>')
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

@app.route('/contacts/<origin_phone>/lend/<friend_phone>/<amount>/<due_date>')
def lendMoney(origin_phone,friend_phone,amount,due_date):
	origin = checkPhoneNode(origin_phone,'Pedro Debt')
	friend = checkPhoneNode(friend_phone,'Pedro Debt')
	today = datetime.now().strftime("%Y-%m-%d")
	due_date = due_date.replace('_','-')
	dt = {
		'since':today,
		'due_date':due_date,
		'amount':amount,
		'description':'',
	}

	if amountMoneyNeeds(friend_phone)>=amount:
		neoCon.relateNodes(origin,friend,dt,'Lends')
	else:
		print 'No necesita tanto dinero'
	return jsonify(msg='success')


@app.route('/contacts/ask/<origin_phone>/<amount>/<description>')
def askMoney(origin_phone,amount,description):
	origin = checkPhoneNode(origin_phone,'Updan Mon')
	temp = origin.properties
	temp['amount'] = int(amount)*-1
	temp['description'] = description.replace('_',' ')
	origin.properties = temp
	return jsonify(msg='success')

@app.route('/contacts/<origin_phone>/payments/<friend_phone>/<amount>')
def payDebt(origin_phone,friend_phone,amount):
	origin = checkPhoneNode(origin_phone,'Juan Pay')
	friend = checkPhoneNode(friend_phone,'Juan Pay')
	today = datetime.now().strftime("%Y-%m-%d")
	dt = {
		'since':today,
		'amount':amount,
		'description':'',
	}

	neoCon.relateNodes(origin,friend,dt,'Pays')

	return jsonify(msg='success')

if __name__ ==  '__main__' :
	neoCon = neo(host = 'http://the.rabit.club:7474/')
	#neoCon.deleteNodeById(5)
	#neoCon.deleteRelationById(10)
	app.run(host='0.0.0.0') #11633

	'''k = checkPhoneNode(5591011416,'Needio Money')
	am = k.properties['amount']
	if am<0:
		for i in k.relationships.incoming(types=["Lends"]):
			print i
		print am
	'''
	#LOGIN
	#http://the.rabit.club:5000/login/5529199527/Mario_Amador
	#AddFriend , R/A valen madres
	#http://the.rabit.club:5000/contacts/5591011416/R/5529199527/A
	#ASK money 
	#http://the.rabit.club:5000/contacts/ask/5591011416/3500/Me_Quiero_Comprar_Una_Ipad
	#Lend Money
	#http://the.rabit.club:5000/contacts/5529199527/lend/5591011416/400/2016_09_01
