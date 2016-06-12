from neo4jrestclient.query import Q
from neo4jrestclient.client import GraphDatabase
from random import random
from base64 import b64encode as enc
from requests import post
import json
from neo4jrestclient.exceptions import NotFoundError
from random import choice
class neoMarkov():
	def __init__(self,host='http://localhost:7474',usr='neo4j',pwd='neo4j.'):
		self.payload ={u'Authorization':'Basic %s'%enc('%s:%s'%(usr,pwd)), 'Content-Type':'application/json','Accept':'application/json; charset=UTF-8'}
		self.host = host
		self.gdb = GraphDatabase(host,username=usr,password=pwd)
	def getNode(self,nodeKey,key='name'):
		search = Q(key,iexact=nodeKey)
		return self.gdb.nodes.filter(search)[0]
	def getNodeById(self,idToLook):
		return self.gdb.nodes.get(idToLook)
	def createNode(self,properties,labels=['monex_card','status','korriban']): #Properties es un Dic, label es un texto
		new = self.gdb.nodes.create()
		new.properties = properties
		for label in labels: new.labels.add(label)
		return new
	def relateNodes(self,fromN,toN,properties,testFinished=True,key='name'):
		n1 = self.getNode(fromN,key=key)
		n2 = self.getNode(toN,key=key)		
		tag = 'Action' if testFinished else 'Development'
		rel = n1.relationships.create(tag, n2)
		rel.properties = properties
		return rel
	def relateNodeById(self,fromId,toId,properties,testFinished=True):
		n1 = self.getNodeById(fromId)
		n2 = self.getNodeById(toId)		
		tag = 'Action' if testFinished else 'Development'
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

#neoJenkins().dumpAllPaths(25,24)
#con=neoJenkins()
#con.copyGraph(30,12)
#con.deleteNodesBetween(74,82)
#con.deleteNodeById(76)
#con.deleteNodeById(77)
#con.deleteNodeById(83)

'''
con.switchCompletedRelation(91)
con.switchCompletedRelation(93)

env = con.createNode({'name':'Envio Domicilio'},labels=lab)
con.relateNodeById(env.id,23,dicValues)
dicValues= {'weight':0.5,'test':'MONdomSEPOMEX','description':'Envio a Domicilio metodo SEPOMEX','shortname':'SEPOMEX'}
con.relateNodeById(env.id,23,dicValues)
dicValues= {'weight':0.3,'test':'agendarMONdomO','description':'Agendar Monex envio de Tarjeta a Domiciio Oficina','shortname':'Envio Domicilio Oficina'}
con.relateNodeById(30,env.id,dicValues)
dicValues= {'weight':0.4,'test':'agendarMONdomC','description':'Agendar Monex envio de Tarjeta a Domiciio Casa','shortname':'Envio Domicilio Casa'}
con.relateNodeById(30,env.id,dicValues)
dicValues= {'weight':0.3,'test':'agendarMONdomX','description':'Agendar Monex envio de Tarjeta a Domiciio Extra','shortname':'Envio Domicilio Extra'}
con.relateNodeById(30,env.id,dicValues)

con.relateNodeById(21,32,dicValues,testFinished=False)
dicValues= {'weight':1,'test':'img_upload_tatooine','description':'Subir Imagenes desde Tatooine','shortname':'Subir Imagenes Tatooine'}
con.relateNodeById(21,32,dicValues,testFinished=False)
'''
#con.switchCompletedRelation(55)
#con.changeRelationProperty(44,'test','cancelar_agendacion')
"""
gdb = GraphDatabase("http://endor.mimoni.com:7474/db/data/",username='neo4j',password='m1m0n100')

monex_card = gdb.labels.create('monex_card')
status = gdb.labels.create('status')
krb = gdb.labels.create('korriban')
action = 'Action'

'''CREAR NODOS'''
noneCard = gdb.node.create(name='None')
oficina = gdb.node.create(name='Oficina')
asignada = gdb.node.create(name='Asignada')
asignadaMal = gdb.node.create(name='Asignada')
disponible = gdb.node.create(name='Disponible')
disponibleMal = gdb.node.create(name='Disponible')
porConf =  gdb.node.create(name='Por Confirmar')
porConfMal =  gdb.node.create(name='Por Confirmar')
entregada =  gdb.node.create(name='Entregada')
entregadaMal =  gdb.node.create(name='Entregada')
porDictaminar = gdb.node.create(name='Por Dictaminar')
porRealizar = gdb.node.create(name='Por Realizar')
dispersada = gdb.node.create(name='Dispersada')
'''Add labels'''
monex_card.add(noneCard,oficina,asignada,asignadaMal,disponible,disponibleMal,porConf,porConfMal,entregada,entregadaMal,porDictaminar,porRealizar,dispersada)
status.add(noneCard,oficina,asignada,asignadaMal,disponible,disponibleMal,porConf,porConfMal,entregada,entregadaMal,porDictaminar,porRealizar,dispersada)
krb.add(noneCard,oficina,asignada,asignadaMal,disponible,disponibleMal,porConf,porConfMal,entregada,entregadaMal,porDictaminar,porRealizar,dispersada)

'''CREAR RELATIONS'''
noneCard.relationships.create(action,oficina,weight=1.0,test='uploadCards',shortname='Subir Archivo de Tarjetas',description='Carga la tarjeta que usara el cliente')

oficina.relationships.create(action,asignada,weight=0.8,test='assignOffice',shortname='Asignar sucursal',description='Asigna la tarjeta a la sucursal en la que el cliente fue agendado')
oficina.relationships.create(action,asignadaMal,weight=0.20,test='assignWrongOffice',shortname='Asignar sucursal',description='Asigna la tarjeta en una sucursal diferente al cliente')

asignada.relationships.create(action,disponible,weight=1.0,test='acceptOffice',shortname='Recepcion Confirmada',description='Sucursal confirma recepcion')
asignadaMal.relationships.create(action,disponibleMal,weight=1.0,test='acceptOffice',shortname='Recepcion Confirmada',description='Sucursal confirma recepcion')

disponible.relationships.create(action,porConf,weight=0.50,test='activateCard',shortname='Activar Tarjeta',description='Activar tarjeta')
disponible.relationships.create(action,entregada,weight=0.50,test='assignCustomer',shortname='Asignar al Cliente',description='Asignar tarjeta al cliente')

porConf.relationships.create(action,porRealizar,weight=1.0,test='assignCustomer',shortname='Asignar al Cliente',description='Asignar tarjeta al cliente')
entregada.relationships.create(action,porRealizar,weight=1.0,test='activateCard',shortname='Activar Tarjeta',description='Activar tarjeta')

disponibleMal.relationships.create(action,porConfMal,weight=0.50,test='activateCard',shortname='Activar Tarjeta',description='Activar tarjeta')
disponibleMal.relationships.create(action,entregadaMal,weight=0.50,test='assignCustomer',shortname='Asignar al Cliente',description='Asignar tarjeta al cliente')

porConfMal.relationships.create(action,porDictaminar,weight=1.0,test='assignCustomer',shortname='Asignar al Cliente',description='Asignar tarjeta al cliente')
entregadaMal.relationships.create(action,porDictaminar,weight=1.0,test='activateCard',shortname='Activar Tarjeta',description='Activar tarjeta')

porDictaminar.relationships.create(action,porRealizar,weight=1.0,test='confirmPorDictaminar',shortname='Solicitar Dispersion',description='Acepta y solicita la dispersion')

porRealizar.relationships.create(action,dispersada,weight=1.0,test='dispPorRealizar',shortname='Subir Archivo de Dispersiones',description='Realizar Dispersion')
"""
'''
con.createNode({'name':'Cancelacion Solicitada'})
con.relateNodes('Oficina','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Asignada','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Disponible','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Entregada','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Por Confirmar','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Por Dictaminar','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Por Realizar','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodes('Dispersada','Cancelacion Solicitada',{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodeById(3,13,{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodeById(5,13,{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodeById(9,13,{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.relateNodeById(7,13,{'weight':0.2,'test':'cancelMonexCard','description':'Solicitar cancelacion de tarjeta monex','shortname':'Solicitar Cancelacion' },testFinished=False)
con.createNode({'name':'Cancelada'})
con.relateNodes('Cancelacion Solicitada','Cancelada',{'weight':0.5,'test':'acceptMonCancellation','description':'Aceptar cancelacion de la tarjeta','shortname':'Cancelar' },testFinished=False)
ini = con.createNode({'name':'Inicio'},labels=lab)
pa1=con.createNode({'name':'Pend_Aut'},labels=lab) #Manual
pa2=con.createNode({'name':'Pend_Aut'},labels=lab) #AUTO

np=con.createNode({'name':'No_Proc'},labels=lab)

nv = con.createNode({'name':'Nueva'},labels=lab)

con.createNode({'name':'Pendiente_Ref'},labels=lab)
con.createNode({'name':'Aprobada'},labels=lab)
con.createNode({'name':'Rechazo'},labels=lab)
con.createNode({'name':'Entrega_Fij'},labels=lab)
con.createNode({'name':'Entregada'},labels=lab)


iDict= {'weight':0.5,'test':'','description':'Ingreso a la Base de Datos','shortname':'Ingreso'}
con.relateNodeById(ini.id,pa1.id,iDict)
con.relateNodeById(ini.id,pa2.id,iDict)

dicValues['test']='noProc'
dicValues['description']='noProc'
dicValues['shortname']='No Procesable' 
con.relateNodeById(pa1.id,np.id,dicValues,testFinished=False)
dicValues['test']='autenticarManual'
dicValues['description']='Autenticar manualmente la solicitud'
dicValues['shortname']='Autenticado' 
con.relateNodeById(pa1.id,nv.id,dicValues)
dicValues['test']='autenticarAut'
dicValues['description']='Autenticar automaticamente la solicitud'
con.relateNodeById(pa2.id,nv.id,dicValues)
con.createNode({'name':'SIC-PHOX'},labels=lab)

dicValues['test']=''
dicValues['weight']=0.60
dicValues['description']='Phox acepto pero falta autenticar Referencias'
dicValues['shortname']='Aceptado' 
con.relateNodes('SIC-PHOX','Pendiente_Ref',dicValues)

dicValues['weight']=0.30
dicValues['description']='Phox acepto solicitud y referencias'
dicValues['shortname']='Aprobacion' 

con.relateNodes('SIC-PHOX','Aprobada',dicValues)
dicValues['test']=''
dicValues['weight']=0.10
dicValues['description']='Phox rechazo la solicitud'
dicValues['shortname']='Rechazada' 

con.relateNodes('SIC-PHOX','Rechazo',dicValues)

dicValues['test']='aprobarRefs'
dicValues['weight']=0.60
dicValues['description']='Autenticar Referencias'
dicValues['shortname']='Autenticar Referencias' 

con.relateNodes('Pendiente_Ref','Aprobada',dicValues)
dicValues['test']='sicphox'
dicValues['weight']=1
dicValues['description']='Simular envio al SIC y esperar repsuesta PHOX'
dicValues['shortname']='Envio SIC, Respuesta PHOX' 

con.relateNodes('Nueva','SIC-PHOX',dicValues)

canRef = con.createNode({'name':'Cancelada'},labels=lab)
canAp = con.createNode({'name':'Cancelada'},labels=lab)
canEnt = con.createNode({'name':'Cancelada'},labels=lab)

dicValues['test']='Cancelar'
dicValues['weight']=0.4
dicValues['description']='Cancelar solicitud'
dicValues['shortname']='Cancelar'

con.relateNodeById( 20 ,canRef.id,dicValues ,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( 21 ,canAp.id,dicValues,testFinished=False)  #'Aprobada'
con.relateNodeById( 23 ,canEnt.id,dicValues,testFinished=False) #'EntregaFij'
dicValues['test']='Reversar'
dicValues['weight']= 1
dicValues['description']='Reversar solicitud'
dicValues['shortname']='Reversar'

con.relateNodeById(  canRef.id,20,dicValues,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( canAp.id,21,dicValues,testFinished=False )  #'Aprobada'
con.relateNodeById( canEnt.id,23,dicValues,testFinished=False) #'EntregaFij'
dicValues['test']=''
dicValues['weight']= 1
dicValues['description']='Activacion de Contrato llega a Kamino'
dicValues['shortname']='Dispersada'

con.relateNodeById(12,24,dicValues) #Entregada Application con Dispersada Korriban - Kamino

dicValues['test']='agendarThiers'
dicValues['weight']= 0.2
dicValues['description']='Agendar Monex Oficina de Entrega Thiers'
dicValues['shortname']='Agendar MON-Thiers'
con.relateNodeById(30,23,dicValues)

dicValues['test']='agendarDomiclioCasa'
dicValues['weight']= 0.1
dicValues['description']='Agendar Monex envio de Tarjeta a Domiciio Casa'
dicValues['shortname']='Agendar MON-Domicilio Casa'
con.relateNodeById(30,23,dicValues)
dicValues['test']='agendarDomiclioOficina'
dicValues['weight']= 0.1
dicValues['description']='Agendar Monex envio de Tarjeta a Domiciio Oficina'
dicValues['shortname']='Agendar MON-Domicilio Oficina'
con.relateNodeById(30,23,dicValues)
dicValues['test']='agendarDomiclioOtro'
dicValues['weight']= 0.1
dicValues['description']='Agendar Monex envio de Tarjeta a Domiciio Otro'
dicValues['shortname']='Agendar MON-Domicilio Otro'
con.relateNodeById(30,23,dicValues)

con.deleteRelationById(63)

dicValues['test']='agendarOficinaENVIA'
dicValues['weight']= 0.3
dicValues['description']='Agendar Monex Cobertura Envia'
dicValues['shortname']='Agendar MON-Sucursal ENVIA'
con.relateNodeById(30,23,dicValues)

dicValues['test']='agendarOficina'
dicValues['weight']= 0.2
dicValues['description']='Agendar Monex Alguna Sucursal de Entrega'
dicValues['shortname']='Agendar MON-Sucursal'
con.relateNodeById(30,23,dicValues)
con.relateNodeById(23,0,dicValues)

lab = ['application','korriban']
EF_INT = con.createNode({'name':'Entrega_Fij'},labels=lab)
EF_INT_C = con.createNode({'name':'Cancelada'},labels=lab)

EF_BBVA = con.createNode({'name':'Entrega_Fij'},labels=lab)
EF_BBVA_C = con.createNode({'name':'Cancelada'},labels=lab)

EF_TD = con.createNode({'name':'Entrega_Fij'},labels=lab)
EF_TD_C = con.createNode({'name':'Cancelada'},labels=lab)

dicValues['test']='agendarINT'
dicValues['weight']=0.1
dicValues['description']='Agendar Solicitud con Intermex'
dicValues['shortname']='Agendar Intermex'
con.relateNodeById(30,EF_INT.id,dicValues)

dicValues['test']='agendarATM'
dicValues['weight']=0.1
dicValues['description']='Agendar Solicitud con ATM'
dicValues['shortname']='Agendar ATM'
con.relateNodeById(30,EF_BBVA.id,dicValues)

dicValues['test']='agendarVNT'
dicValues['weight']=0.1
dicValues['description']='Agendar Solicitud con VNT'
dicValues['shortname']='Agendar VNT'
con.relateNodeById(30,EF_BBVA.id,dicValues)

dicValues['test']='agendarTD'
dicValues['weight']=0.1
dicValues['description']='Agendar Solicitud con VNT'
dicValues['shortname']='Agendar VNT'
con.relateNodeById(30,EF_TD.id,dicValues)


dicValues['test']='Cancelar'
dicValues['weight']=0.4
dicValues['description']='Cancelar solicitud'
dicValues['shortname']='Cancelar'

con.relateNodeById( EF_TD.id ,EF_TD_C.id,dicValues ,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( EF_BBVA.id ,EF_BBVA_C.id,dicValues ,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( EF_INT.id ,EF_INT_C.id,dicValues ,testFinished=False) #'Pendiente_Ref'

dicValues['test']='Reversar'
dicValues['weight']= 1
dicValues['description']='Reversar solicitud'
dicValues['shortname']='Reversar'

con.relateNodeById( EF_TD_C.id,EF_TD.id, dicValues ,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( EF_BBVA_C.id,EF_BBVA.id  ,dicValues ,testFinished=False) #'Pendiente_Ref'
con.relateNodeById( EF_INT_C.id,EF_INT.id ,dicValues ,testFinished=False) #'Pendiente_Ref'

dicValues['test']='dispTD'
dicValues['weight']= 1
dicValues['description']='Validar Descargable de dispersion y subir CSV para Dispersar contrato'
dicValues['shortname']='Disperar TD'
con.relateNodeById(35,24,dicValues)

lab= ['korriban','intermex']
interDISP = con.createNode({'name':'Dispersada'},labels=lab)
interCOB = con.createNode({'name':'Cobrada'},labels=lab)

dicValues['test']='dispIntermex'
dicValues['weight']= 1
dicValues['description']='Solicitar dispersiond e Intermex'
dicValues['shortname']='Solicitar Dispersion Intermex'
con.relateNodeById(31,interDISP.id ,dicValues) #'Pendiente_Ref'
dicValues['test']='cobradaIntermex'
dicValues['weight']= 1
dicValues['description']='Proceso de Dispersada a Cobrada'
dicValues['shortname']='Cobro del cliente'
con.relateNodeById( interDISP.id,interCOB.id ,dicValues) #'Pendiente_Ref'
dicValues['test']=''
dicValues['weight']= 1
dicValues['description']='Contrato Activo listo en Kamino'
dicValues['shortname']='Dispersada'
con.relateNodeById( interCOB.id,24,dicValues) #'Pendiente_Ref'

lab= ['korriban','bbva','atm']
interDISP = con.createNode({'name':'Dispersada'},labels=lab)
interCOB = con.createNode({'name':'Cobrada'},labels=lab)

dicValues['test']='dispATM'
dicValues['weight']= 1
dicValues['description']='Validar Descargable de dispersion y subir CSV para Dispersar contrato'
dicValues['shortname']='Dispersar ATM'
con.relateNodeById(33,interDISP.id ,dicValues) #'Pendiente_Ref'
dicValues['test']='movimientosATM'
dicValues['weight']= 1
dicValues['description']='Subir archivo de movimientos ATM'
dicValues['shortname']='Cobro del cliente'
con.relateNodeById( interDISP.id,interCOB.id ,dicValues) #'Pendiente_Ref'
dicValues['test']=''
dicValues['weight']= 1
dicValues['description']='Contrato Activo listo en Kamino'
dicValues['shortname']='Dispersada'
con.relateNodeById( interCOB.id,24,dicValues) #'Pendiente_Ref'
'''
'''
lab= ['korriban','bbva','atm']
EntregaVNT = con.createNode({'name':'Entrega_Fij'},labels=['application','korriban']) 
interDISP = con.createNode({'name':'Dispersada'},labels=lab)
interCOB = con.createNode({'name':'Cobrada'},labels=lab)

dicValues['test']='dispVNT'
dicValues['weight']= 1
dicValues['description']='Validar Descargable de dispersion y subir CSV para Dispersar contrato'
dicValues['shortname']='Dispersar VNT'
con.relateNodeById(EntregaVNT.id,interDISP.id ,dicValues) #'Pendiente_Ref'
dicValues['test']='movimientosVNT'
dicValues['weight']= 1
dicValues['description']='Subir archivo de movimientos VNT'
dicValues['shortname']='Cobro del cliente'
con.relateNodeById( interDISP.id,interCOB.id ,dicValues) #'Pendiente_Ref'
dicValues['test']=''
dicValues['weight']= 1
dicValues['description']='Contrato Activo listo en Kamino'
dicValues['shortname']='Dispersada'
con.relateNodeById( interCOB.id,24,dicValues) #'Pendiente_Ref'

dicValues['test']='agendarVNT'
dicValues['weight']= 1
dicValues['description']='Agendar solicitud con BBVA VNT'
dicValues['shortname']='Agendar Ventanilla'

con.relateNodeById( 30,41,dicValues) #'Pendiente_Ref'

canc = con.createNode({'name':'Cancelada'},labels=['application','korriban']) 
dicValues['test']='Cancelar'
dicValues['weight']= 0.4
dicValues['description']='Cancelar Solicitud'
dicValues['shortname']='Cancelar'
con.relateNodeById( 41,canc.id,dicValues) #'Pendiente_Ref'
dicValues['test']='Reversar'
dicValues['weight']= 1
dicValues['description']='Reversar Solicitud'
dicValues['shortname']='Reversar'
con.relateNodeById( canc.id,41,dicValues) #'Pendiente_Ref'
'''


