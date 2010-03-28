#!/usr/bin/env python

import datetime

# for decoding json messages
import json

# twisted
from twisted.internet import protocol, reactor
from twisted.protocols import basic

# django land
from django.core.management import setup_environ
from go import settings

setup_environ(settings)

from go.GoServer.models import Game, GameParticipant
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

# our CTS command
CTS = ['CTS']

   

class GoServerProtocol(basic.LineReceiver):
   
   session_key = False

   user = False

   def debug(self, msg):
      print '%s %d %s' % (datetime.datetime.now(), self.transport.sessionno, msg)
      
   def connectionMade(self):
      self.debug('Connection opened')
   
   def connectionLost(self, reason):
      self.debug('Connection lost: '+str(reason))

   def lineReceived(self, data):

      response = "nil"

      try:
         
         cmd = json.loads(data)

         self.debug( '< '+str(cmd) )

         # connect command ; index 1 is a session_key
         if(cmd[0] == 'SESS'):
            self.session_key = cmd[1]

            # load up the session's user object
            session = Session.objects.get(session_key = self.session_key)
            uid = session.get_decoded().get('_auth_user_id')
            self.user = User.objects.get(pk=uid)
            response = CTS


         # we arent connected and we dont have a session? not allowed!
         elif( self.session_key == False ):
            response = ['ERROR','No session_key; you must SESS first.']


         # join game command ; index 1 is a game name
         elif(cmd[0] == 'JOIN'):        

            game_id = cmd[1]

            # load the game object
            game = Game.objects.get(pk = game_id)

            # determine if this user is the owner or what
            if game.id == self.user.id:
               newstate = 'O'
            else:
               newstate = 'U'

            # TODO insert a validation thing to make sure user has perm to join this game

            # make a participant entry to tie this user to the game in the database
            newparticipant = GameParticipant( Participant=self.user, Game=game, State=newstate )
            newparticipant.save()
            
            # register this connection as being associated with this game in the factory.             
            self.factory.addToConnectionDB(self, game_id)

            # now find all connections associated with this game and tell them about the newcomer
            for (conn_game_id,connection) in self.factory.connectionList:
               if conn_game_id == game_id:
                  self.writeToTransport(["JOIN", self.user.id, self.user.username], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'CHAT'):
            game_id = cmd[1]
            message = cmd[2]
            
            # TODO insert a validation thing to make sure user has perm to chat this game

            # now find all connections associated with this game and tell them about the newcomer
            for (conn_game_id,connection) in self.factory.connectionList:
               if conn_game_id == game_id:
                  self.writeToTransport(["CHAT", self.user.username, message], transport = connection.transport)
            response = CTS


         # part command ; index 1 is a channel name
         elif(cmd[0] == 'PART'):
            response = CTS

            
         # channel say ; index 1 is a channel name  index 2 is the message
         elif(cmd[0] == 'SAY'):
            response = CTS


      except Exception, e:
         self.debug( 'Cmd receive exception: %s' % e )
         response = ['ERROR', e]

      self.writeToTransport(response, self.transport)

   def writeToTransport(self, response, transport = False):

      if not transport:
         transport = self.transport

      out_json = json.dumps(response)

      self.debug('> '+out_json)

      transport.write(out_json + "\r\n")


class GoServerFactory(protocol.ServerFactory):
   protocol = GoServerProtocol
      

   
   def __init__(self):      
      # this maps connections to user IDs
      self.connectionList = []

   def addToConnectionDB(self, connection, game_id):
      self.connectionList.append( [game_id, connection] )





reactor.listenTCP(8002, GoServerFactory())
reactor.run()

