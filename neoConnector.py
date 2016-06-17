# coding=utf-8
from neo4jrestclient.query import Q
from neo4jrestclient.client import GraphDatabase
from random import random
from base64 import b64encode as enc
from requests import post
import json
from neo4jrestclient.exceptions import NotFoundError
from random import choice
from random import randint
class neo():
	def __init__(self,host='http://localhost:7474',usr='neo4j',pwd='neo4j.'):
		self.payload ={u'Authorization':'Basic %s'%enc('%s:%s'%(usr,pwd)), 'Content-Type':'application/json','Accept':'application/json; charset=UTF-8'}
		self.host = host
		self.gdb = GraphDatabase(host,username=usr,password=pwd)
	def getNode(self,nodeKey,key='name'):
		search = Q(key,iexact=nodeKey)
		return self.gdb.nodes.filter(search)[0]
	def nodeExists(self,nodeKey,key='name'):
		search = Q(key,iexact=nodeKey)
		return len(self.gdb.nodes.filter(search))>0
	def getNodeById(self,idToLook):
		return self.gdb.nodes.get(idToLook)
	def createNode(self,properties,labels=['monex_card','status','korriban']): #Properties es un Dic, label es un texto
		new = self.gdb.nodes.create()
		new.properties = properties
		for label in labels: new.labels.add(label)
		return new
	def relateNodes(self,n1,n2,properties,tag):
		rel = n1.relationships.create(tag, n2)
		rel.properties = properties
		return rel
	def relateNodeById(self,fromId,toId,properties,tag):
		n1 = self.getNodeById(fromId)
		n2 = self.getNodeById(toId)		
		rel = n1.relationships.create(tag, n2)
		rel.properties = properties
		return rel

	def deleteNodeById(self,nodeId):
		n1 = self.getNodeById(nodeId)
		for r in n1.relationships.all(): r.delete()
		n1.delete()
	def deleteNode(self,node,key='name'):
		n1 = self.getNode(node,key=key)
		for r in n1.relationships.all(): r.delete()
		n1.delete()
	def deleteRelationById(self,relId):
		self.gdb.relationships.get(relId).delete()
	def deleteRelationsBetweenNodes(self,fromN,toN,key='name'):
		n1 = self.getNode(fromN,key=key)
		for rel in n1.relationships.outgoing(): rel.delete()
	def switchCompletedRelation(self,relId): #Cambia de Development a Action
		r=self.gdb.relationships.get(relId)
		finito = r.type=='Development' #SI es TRUE significa que debemos poner Action
		newRel = self.relateNodeById(r.start.id, r.end.id, r.properties,testFinished=finito)
		r.delete()
		print 'New relation Id = %s, Type: %s'%(newRel.id,newRel.type)
		return newRel
	def changeRelationEnd(self,relId,newEndId):
		r = self.gdb.relationships.get(relId)
		start = r.start.id
		properties = r.properties
		finished = r.type=='Action'

		nwRel = self.relateNodeById(start ,newEndId ,properties,testFinished= finished)
		r.delete()
		print 'New relation Id= %s ,  End Id: %s'%(nwRel.id,nwRel.end.id)
		return nwRel
		
	def nodeSetLabels(self,nodeId,labels):
		n = self.getNodeById(nodeId)
		copyLabels = [l for l in n.labels]
		for label in copyLabels: 
			n.labels.remove(label._label)  #Borrar todas
		for label in labels: 
			n.labels.add(label)			  #Agregar todas
		print n.labels

	def getDijkstraPaths(s, fromNode, toNode, key='name'):
		if key=='id': fr, to= s.getNodeById(fromNode ), s.getNodeById(toNode )
		else: fr, to= s.getNode(fromNode,key=key), s.getNode(toNode,key=key)
		query={"to" :to.url,
  				"cost_property" : "weight",
				"relationships" : {"type" : "Action", "direction" : "out"},
				"algorithm" : "dijkstra"}
		r = post('%s/db/data/node/%s/paths'%(s.host,fr.id),headers=s.payload, json=query)
		return r.text
	def getAllAvailablePaths(s, fromNode, toNode, key='name'):
		if key=='id': fr, to= s.getNodeById(fromNode), s.getNodeById(toNode)
		else: fr, to= s.getNode(fromNode,key=key), s.getNode(toNode,key=key)
		query={"to" :to.url,
				"max_depth" : 60,
				"relationships" : {"type" : "Action", "direction" : "out"},
				"algorithm" : "allPaths"}
		r = post('%s/db/data/node/%s/paths'%(s.host,fr.id),headers=s.payload, json=query)
		return r.text
	def getAllPaths(s, fromNode, toNode, key='name'):
		if key=='id': fr, to= s.getNodeById(fromNode), s.getNodeById(toNode)
		else: fr, to= s.getNode(fromNode,key=key), s.getNode(toNode,key=key)
		query={"to" :to.url,
				"max_depth" : 60,
				"relationships" : [{"type" :"Action", "direction" : "out"},{"type" :"Development", "direction" : "out"}],
				"algorithm" : "allPaths"}
		r = post('%s/db/data/node/%s/paths'%(s.host,fr.id),headers=s.payload, json=query)
		return r.text
	def getOnePath(s,fromNode,toNode, key='id'):
		if key=='id': fr, to= s.getNodeById(fromNode), s.getNodeById(toNode)
		else: fr, to= s.getNode(fromNode,key=key), s.getNode(toNode,key=key)
		query={"to" :to.url,
				"max_depth" : 60,
				"relationships" : [{"type" :"Action", "direction" : "out"},{"type" :"Development", "direction" : "out"}],
				"algorithm" : "shortestPath"}
		r = post('%s/db/data/node/%s/path'%(s.host,fr.id),headers=s.payload, json=query)
		return r.text
		
	def getRandomPathTests(self,fromNodeKey,toNodeKey,key='name',paths=[],relationProperty='test'): #Creates Path based on 'weight' property
		if key=='id': fNode= self.getNodeById(fromNodeKey) 
		else: fNode=self.getNode(fromNodeKey,key=key)
		relations = fNode.relationships.outgoing()[:]
		start,rand,maxRand,previousWeight = 0,random(),0,0
		if fromNodeKey==toNodeKey or len(relations)==0: 		 #FinalizarRecursividad si Origen=Destino 
			return paths 										 #O si no hay a donde mas ir
		for relation in relations: maxRand+=relation.properties['weight'] 
		rand *= maxRand #Si los pesos no estan bien puestos
		for relation in relations:
			weight=relation.properties['weight']
			if start<=rand<=weight+previousWeight: 
				if key=='id': return self.getRandomPathTests(relation.end.id,toNodeKey,key='id',paths=paths+[relation.properties[relationProperty]])
				else: return self.getRandomPathTests(relation.end.properties[key],toNodeKey,paths=paths+[relation.properties[relationProperty]])
			start+=weight
			previousWeight = weight
		return paths
	def changeRelationProperty(self,relationId,propertyKey,value):
		rel=self.gdb.relationships.get(relationId)
		print rel.properties
		if propertyKey in rel.properties:
			copy = rel.properties.copy()
			copy[propertyKey] = value
			rel.properties = copy 
			print rel.properties
		else:
			print 'Propiedad "%s" No existe en relacion'%(propertyKey)
	
	#relationships , weight ,length ,directions ,nodes
	def getAttributesFromPaths(self,jsonPaths,attrib): 
		response = []
		jsonPaths = json.loads(jsonPaths)
		for path in jsonPaths:
			tempRes = []
			res = path[attrib]
			if hasattr(res, '__contains__'):#PODEMOS ITERAR
				for r in res: 
					tempRes.append(r)
			else: 
				tempRes.append(res)
			response.append(tempRes)
		return response
	def getAttributeFromPathsRelations(self,jsonPaths,attrib,rand=False):
		totalPathsRels = self.getAttributesFromPaths(jsonPaths,'relationships')
		del jsonPaths
		if rand: 
			resp = []
			for r in choice(totalPathsRels):
				rIdi = r.rfind('/')
				at = self.gdb.relationships.get(r[rIdi+1:]).properties[attrib]
				if at: resp.append(at)
			yield resp
		else:
			for pathRelations in totalPathsRels:
				resp = []
				for r in pathRelations:
					rIdi = r.rfind('/')
					at = self.gdb.relationships.get(r[rIdi+1:]).properties[attrib]
					if at: resp.append(at)
				yield resp
	def dumpAllPaths(self,fromId,toId,available=True):
		p = self.getAllAvailablePaths(fromId,toId,key='id') if available else getAllPaths(fromId,toId,key='id')
		with open('pruebas%s.txt'%('' if available else 'ProdYDev'),'w+') as f:
			pathsDescriptions = self.getAttributeFromPathsRelations(p , 'description')
			f.write('Total de Pruebas: %s\n'%len(json.loads(p))) 
			for descriptionOfPath in pathsDescriptions:
				for description in descriptionOfPath:
					f.write(description)
					f.write('\n') 
				f.write('\n')
	def getTotalPaths(self,fromId,toId,available=True):
		func = self.getAllAvailablePaths if available else self.getAllPaths 
		return len(json.loads(func(fromId,toId,key='id')))
	def pathExists(self,fromId,toId,available=False):
		return not 'exception' in json.loads(self.getOnePath(fromId,toId)) 
		
	def copyGraph(self,fromId,toId,relationNodes=None,validated=False):
		if not validated:
			if not self.pathExists(fromId,toId): 
				raise Exception('No existe ese camino, verificar los Ids Origen y destino')
		if relationNodes == None: relationNodes={}      				 #Relacion Nodo Viejo -> Nodo Nuevo
		fNode= self.getNodeById(fromId) 
		relations = fNode.relationships.outgoing()[:]  					 #Obtener todas las relaciones que tiene este nodo
		if fNode.id not in relationNodes:  								 #Crear una copia si aun no la tenemos
			newNode = self.createNode(fNode.properties,labels=[l._label for l in fNode.labels]) 
			relationNodes[fNode.id]=newNode.id 							 #Guardamos que ya fue visitado
		else: return 													 #SI YA EXISTE ES POR QUE YA ESTA TODO RELACIONADO
		if fromId==toId: return 										 #Llegamos al Final, Ya no lo relacionamos
		for relation in relations: 										 #Obtenemos relaciones y las generamos para la copia
			nextNode = relation.end
			self.copyGraph(nextNode.id,toId,relationNodes=relationNodes,validated=True) 
																		 #Esta cosa se debe encargar que exista el proximo Nodo
			nextNode = self.getNodeById(relationNodes[nextNode.id])	     #Aqui ya existe, obtener su equivalente nuevo
			rel = newNode.relationships.create(relation.type,nextNode)	 #Reacionar con los datos originales
			rel.properties = relation.properties
	def deleteNodesBetween(self,fromId,toId,erased=None):
		p = self.getAllPaths(fromId,toId,key='id')
		nodesIds = self.getAttributesFromPaths(p,'nodes')
		toDel = set()
		for path in nodesIds:
			for node in path:
				toDel.add(node)
		for node in toDel:
			nodeId = node[node.rfind('/')+1:]
			self.deleteNodeById(nodeId)
			print nodeId

neoCon = neo(host = 'http://the.rabit.club:7474/')
#neoCon.deleteRelationById(700)
#neoCon.createNode({'name':'Ruben','phone':5591011416,'amount':-100},labels=['Cuadra']) #393
#neoCon.createNode({'name':'Dulce','phone':5591011416,'amount':-100},labels=['Villarreal']).id #394
#neoCon.createNode({'name':'David','phone':5591011416,'amount':100},labels=['Mimila']).id #395

#neoCon.createNode({'name':'Mariana','phone':5591011416,'amount':-2000},labels=['Luna']).id #396
#neoCon.createNode({'name':'Ralph','phone':5591011416,'amount':2000},labels=['Luna']).id #397
#neoCon.createNode({'name':'Conejo','phone':5591011416,'amount':0},labels=['Rabit']).id #398
#neoCon.createNode({'name':'Pedro','phone':5591011416,'amount':-650},labels=['Amador']).id #399
#neoCon.createNode({'name':'Mario','phone':5591011416,'amount':650},labels=['Amador']).id #400

#neoCon.relateNodeById(399,400,{'cantidad':200},'Paga')


'''
neoCon.relateNodeById(394,395,{'since':'28/05/16'},'amigos')
neoCon.relateNodeById(395,394,{'since':'28/05/16'},'amigos')
neoCon.relateNodeById(395,394,{'cantidad':100},'Presta')
#neoJenkins().dumpAllPaths(25,24)
'''
'''
raise
neoCon = neo(host = 'http://the.rabit.club:7474/')
from gen import RandomUser
leadrs = []
for i in xrange(0,10):	
	print 'Creado Padre'
	father = RandomUser()
	f_node = father.createAsNode(neoCon)
	family = [f_node]
	for j in xrange(0,randint(4,6)):
		n = RandomUser(last_name=father.last).createAsNode(neoCon)
		family.append(n)

	for i in xrange(0,len(family)):
		fromN = choice(family)
		toN=choice(family)
		while fromN==toN:
			toN = choice(family)
		if randint(0,5)>1: #knows
			ya = False
			for i in fromN.relationships.outgoing(type='Conoce'):
				if i.end==toN:
					ya = True
					break
			if ya:
				pass
			else:
				neoCon.relateNodes(fromN,toN,{},'Conoce')
				neoCon.relateNodes(toN,fromN,{},'Conoce')
		else: #Presta
			neoCon.relateNodes(fromN,toN,{'cantidad':randint(1,2000)},'Presta')
			if randint(0,1)==0:
				neoCon.relateNodes(toN,fromN,{'cantidad':randint(1,2000)},'Paga')
		print 'Relacionando'
	leadrs.append(choice(family))

t =len(leadrs)
for i in xrange(0,t):
	fromN = choice(leadrs)
	toN=choice(leadrs)
	while fromN==toN:
		toN = choice(leadrs)
	if randint(0,5)>1: #knows
		ya = False
		for i in fromN.relationships.outgoing(type='Conoce'):
			if i.end==toN:
				ya = True
				break
		if ya:
			pass
		else:
			neoCon.relateNodes(fromN,toN,{},'Conoce')
			neoCon.relateNodes(toN,fromN,{},'Conoce')
	else: #Presta
		neoCon.relateNodes(fromN,toN,{'cantidad':randint(1,2000)},'Presta')
		if randint(0,1)==0:
			neoCon.relateNodes(toN,fromN,{'cantidad':randint(1,2000)},'Paga')
	print 'Relacionando Familias'
'''