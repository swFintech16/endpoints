# coding=utf-8
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
		for i in k.relationships.incoming(types=["Lends"]):
			am += i.properties['amount']
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
	amount = float(amount)
	today = datetime.now().strftime("%Y-%m-%d")
	due_date = due_date.replace('_','-')
	dt = {
		'since':today,
		'due_date':due_date,
		'amount':amount,
		'description':'',
	}
	needs = amountMoneyNeeds(friend_phone)
	if needs>amount:
		neoCon.relateNodes(origin,friend,dt,'Lends')
	elif needs==amount: #SE PAGA LA DEUDA, sigue teniendo gente a quien pagarle
		neoCon.relateNodes(origin,friend,dt,'Lends')
		temp = friend.properties
		temp['amount'] = 0
		temp['description'] = ''
		friend.properties = temp
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

@app.route('/contacts/<origin_phone>')
def get_contacts(origin_phone):
	origin = checkPhoneNode(origin_phone,'')
	response = {'friends':[]}
	for i in origin.relationships.outgoing(types=["Conoce"]):
		temp = i.end.properties
		temp['status'] = 'Neutro' 
		for j in i.end.labels:
			temp["last_name"] = j._label
			break
		response['friends'].append(temp) #Lista de Amigos
	for i in origin.relationships.outgoing(types=['Paga']):
		temp = i.end.properties
		temp['status'] = 'Prestamista'
		for j in i.end.labels:
			temp["last_name"] = j._label
			break 
		temp['amount']+=i.properties['cantidad']
		response['friends'].append(temp)
	for i in origin.relationships.outgoing(types=['Presta']):
		temp = i.end.properties
		temp['status'] = 'Deudor' 
		for j in i.end.labels:
			temp["last_name"] = j._label
			break
		temp['amount']+=i.properties['cantidad']
		response['friends'].append(temp)
	for i in response['friends']:
		if i['status']=='Neutro':
			i['amount']=0
	return jsonify(response=response)

@app.route('/contacts/<origin_phone>/payments/<friend_phone>/<amount>')
def payDebt(origin_phone,friend_phone,amount):
	origin = checkPhoneNode(origin_phone,'Juan Pay')
	friend = checkPhoneNode(friend_phone,'Juan Pay')
	today = datetime.now().strftime("%Y-%m-%d")
	amount = float(amount)
	dt = {
		'since':today,
		'amount':amount,
		'description':'',
	}
	totalDebt = 0

	for i in origin.relationships.incoming(types=["Lends"]): 
		if i.start==friend:
			totalDebt+= i.properties['amount']
	for i in origin.relationships.outgoing(types=["Pays"]): 
		if i.end==friend:
			totalDebt-= i.properties['amount']
 	
 	if totalDebt>amount:
		neoCon.relateNodes(origin,friend,dt,'Pays')
		return jsonify(msg='success')

	elif totalDebt==amount:
		neoCon.relateNodes(origin,friend,dt,'Pays')
		for i in origin.relationships.incoming(types=["Lends"]): 
			if i.start==friend:
				neoCon.deleteRelationById(i.id) #Borrar deudas con amigo
		temp = origin.properties
		temp['amount'] = temp['amount']+totalDebt
		if temp['amount']==0:
			temp['description'] = ''
		friend.properties = temp
		return jsonify(msg ='Se pago toda la deuda')
	else:
		return jsonify(msg='No necesitas pagar tanto dinero')

if __name__ ==  '__main__' :
	neoCon = neo(host = 'http://the.rabit.club:7474/')
	app.run(host='0.0.0.0') #11633

	#LOGIN
	#http://the.rabit.club:5000/login/5529199527/Mario_Amador
	#AddFriend , R/A valen madres
	#http://the.rabit.club:5000/contacts/5591011416/R/5529199527/A
	#ASK money 
	#http://the.rabit.club:5000/contacts/ask/5591011416/3500/Me_Quiero_Comprar_Una_Ipad
	#Lend Money
	#http://the.rabit.club:5000/contacts/5529199527/lend/5591011416/400/2016_09_01
	#Pay debt
	#http://the.rabit.club:5000/contacts/5591011416/payments/5529199527/100000
	#Get List of Friends /w status
	#http://the.rabit.club:5000/contacts/5591011416

