#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import signal
import subprocess
import sys
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import random
import sqlite3
import urllib2
import datetime
import shutil
from dict2xml import dict2xml
from xml.dom import minidom
from traceback import print_exc
from time import gmtime, strftime
from xbmc import Monitor

_Addon_ = xbmcaddon.Addon()
_AddonPath_ = xbmc.translatePath(_Addon_.getAddonInfo("path"))
_UserData_ = xbmc.translatePath(_Addon_.getAddonInfo("profile"))

BASE_RESOURCE_PATH = os.path.join(_AddonPath_, "resources")
sys.path.append(os.path.join(BASE_RESOURCE_PATH, "lib"))

#import ptvsd
#ptvsd.enable_attach(secret = "pwd")
#ptvsd.wait_for_attach()

#Addon OSCam
OSCamBD = None
try:
	OSCam = xbmcaddon.Addon(id="service.softcam.oscam")
	OSCamData = xbmc.translatePath(OSCam.getAddonInfo("profile"))
	OSCamBD = sqlite3.connect(os.path.join(os.path.join(OSCamData, "database"), "Settings.db"))
except:
	pass

#TV
TVBD = None
TVBDFile = xbmc.translatePath('special://userdata/Database/TV29.db')
try:
	TVBD = sqlite3.connect(TVBDFile)
except:
	pass
	
from bottle import route, run, template, get, post, request, response
import BaseHTTPServer

#Addon OSCam Funções
@get('/oscam/readers')
def oscam_readers():
	if not OSCamBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "OSCam não instalado!" }})
	try:
		cursor = OSCamBD.cursor()
		cursor.execute("SELECT rowid, URL, Porta, Usuario, Senha, DESKey, Status FROM Readers")
		dados = []
		for rowid, URL, Porta, Usuario, Senha, DESKey, Status in cursor.fetchall():
		    dados.append({"ID" : rowid, "URL" : URL, "Porta" : Porta, "Usuario" : Usuario, "Senha" : Senha, "DESKey" : DESKey, "Status" : True if Status == "checked" else False});
		if len(dados) > 0:
		    return retornar({"retorno" : { "status" : True, "dados" : dados, "erro" : "" }})
		else:
		    return retornar({"retorno" : { "status" : False, "codigo" : 3, "erro" : "Nenhum reader cadastrado!" }})
	except Exception, e:
		return retornar({"retorno" : { "status" : False, "codigo" : 2, "erro" : e.message }})

@post('/oscam')
def oscam_atualizardados():
	if not OSCamBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "OSCam não instalado!" }})

#TV
@get('/tv/canais')
def tv_obtercanais():
	id = request.GET.get("id", -1)
	# Obtendo canais
	if not os.path.exists(TVBDFile):
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "BD de canais não encontrado!" }})
	if not TVBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 2, "erro" : "Não foi possivel se conectar no BD de canais." }})
	try:
		cursor = TVBD.cursor()
		if int(id) == -1:
			cursor.execute("select idChannel, iUniqueId, bIsRadio, bIsHidden, bIsUserSetIcon, bIsUserSetName, bIsLocked, sIconPath, sChannelName, bIsVirtual, bEPGEnabled, sEPGScraper, iLastWatched, iClientId, idEpg from channels order by sChannelName")
		elif int(id) > 1:
			return retornar({"retorno" : { "status" : False, "codigo" : 4, "erro" : "Valores aceitos '-1' Todos, '0' TV e '1' Rádio." }})
		else:
			cursor.execute("select idChannel, iUniqueId, bIsRadio, bIsHidden, bIsUserSetIcon, bIsUserSetName, bIsLocked, sIconPath, sChannelName, bIsVirtual, bEPGEnabled, sEPGScraper, iLastWatched, iClientId, idEpg from channels where bIsRadio = %i order by sChannelName" % int(id))
		dados = []
		for idChannel, iUniqueId, bIsRadio, bIsHidden, bIsUserSetIcon, bIsUserSetName, bIsLocked, sIconPath, sChannelName, bIsVirtual, bEPGEnabled, sEPGScraper, iLastWatched, iClientId, idEpg in cursor.fetchall():
		    dados.append({"idChannel" : idChannel, "iUniqueId" : iUniqueId, "bIsRadio" : bIsRadio, "bIsHidden" : bIsHidden, "bIsUserSetIcon" : bIsUserSetIcon, "bIsUserSetName" : bIsUserSetName, "bIsLocked" : bIsLocked, "sIconPath" : sIconPath, "sChannelName" : sChannelName, "bIsVirtual" : bIsVirtual, "bEPGEnabled" : bEPGEnabled, "sEPGScraper" : sEPGScraper, "iLastWatched" : iLastWatched, "iClientId" : iClientId, "idEpg" : idEpg})
		if len(dados) > 0:
		    return retornar({"retorno" : { "status" : True, "dados" : dados, "erro" : "" }})
		else:
		    return retornar({"retorno" : { "status" : False, "codigo" : 3, "erro" : "Nenhum canal cadastrado!" }})
	except Exception, e:
		return retornar({"retorno" : { "status" : False, "codigo" : 5, "erro" : e.message }})

@get('/tv/canais/grupos')
def tv_obtergrupos():
	# Obtendo canais
	if not os.path.exists(TVBDFile):
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "BD de canais não encontrado!" }})
	if not TVBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 2, "erro" : "Não foi possivel se conectar no BD de canais." }})
	try:
		cursor = TVBD.cursor()
		cursor.execute("select idGroup, bIsRadio, iGroupType, sName, iLastWatched, bIsHidden, iPosition from channelgroups order by idGroup")
		dados = []
		for idGroup, bIsRadio, iGroupType, sName, iLastWatched, bIsHidden, iPosition in cursor.fetchall():
		    dados.append({"idGroup" : idGroup, "bIsRadio" : bIsRadio, "iGroupType" : iGroupType, "sName" : sName, "iLastWatched" : iLastWatched, "bIsHidden" : bIsHidden, "iPosition" : iPosition})
		if len(dados) > 0:
		    return retornar({"retorno" : { "status" : True, "dados" : dados, "erro" : "" }})
		else:
		    return retornar({"retorno" : { "status" : False, "codigo" : 3, "erro" : "Nenhum grupo cadastrado!" }})
	except Exception, e:
		return retornar({"retorno" : { "status" : False, "codigo" : 4, "erro" : e.message }})
		
@get('/tv/canais/map')
def tv_mp_canaisgrupos():
	# Obtendo canais
	if not os.path.exists(TVBDFile):
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "BD de canais não encontrado!" }})
	if not TVBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 2, "erro" : "Não foi possivel se conectar no BD de canais." }})
	try:
		cursor = TVBD.cursor()
		cursor.execute("select idChannel, idGroup, iChannelNumber, iSubChannelNumber from map_channelgroups_channels order by idGroup")
		dados = []
		for idChannel, idGroup, iChannelNumber, iSubChannelNumber in cursor.fetchall():
		    dados.append({"idChannel" : idChannel, "idGroup" : idGroup, "iChannelNumber" : iChannelNumber, "iSubChannelNumber" : iSubChannelNumber})
		if len(dados) > 0:
		    return retornar({"retorno" : { "status" : True, "dados" : dados, "erro" : "" }})
		else:
		    return retornar({"retorno" : { "status" : False, "codigo" : 3, "erro" : "Nenhum mapeamento de grupos e canais encontrado!" }})
	except Exception, e:
		return retornar({"retorno" : { "status" : False, "codigo" : 4, "erro" : e.message }})

@post('/tv')
def tv_atualizardados():
	if not os.path.exists(TVBDFile):
		return retornar({"retorno" : { "status" : False, "codigo" : 1, "erro" : "BD de canais não encontrado!" }})
	if not TVBD:
		return retornar({"retorno" : { "status" : False, "codigo" : 2, "erro" : "Não foi possivel se conectar no BD de canais." }})

def retornar(dados):
    if not request.GET.get("tipo", "json") == "xml":
        response.content_type = 'application/json'
        return dados
    else:
        response.content_type = 'application/xml'
        return dict2xml(dados).ToString()

if __name__ == "__main__":
	reload(sys)
	sys.setdefaultencoding("utf-8")
	setattr(BaseHTTPServer.HTTPServer, 'allow_reuse_address', 1)
	run(host='', port=int(_Addon_.getSetting(id="WEB_PORT")), quit=True)