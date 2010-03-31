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

# port to listen on
PORT = 8002
   

class GoServerProtocol(basic.LineReceiver):
   
   # session key of connected user
   session_key = False

   # game this connection is related to
   game = False

   # user this connection is related to
   user = False

   # indicates if this connection had been cleanly unloaded
   already_unloaded = False

   def debug(self, msg):
      print '%s %04d | %s' % (datetime.datetime.now(), self.transport.sessionno, msg)
      
   def connectionMade(self):
      self.debug('Connection opened')
   
   def connectionLost(self, reason, client_initiated=False):

      # client_initiated means this was from a PART command
      if client_initiated:

         self.debug('Client-initiated connection close: '+str(reason))

      # not client initiated means the connection just dropped
      else:

         # if we already handled it (there was already a clean PART) then we are done
         if self.already_unloaded:
            self.debug('Connection was already cleanly unloaded.')
            return

         # if we have't already handled it then.. we better handle it!
         else:
            self.debug('Connection was NOT cleanly unloaded.')
                     
      self.debug('Unregistering where game=%d and user=%s' % (self.game.id, self.user.username) )

      # delete connection from connection list
      oldentry = self.factory.delFromConnectionDB(self, self.game.id)

      # determine if this was the last connection from this user
      lastconnection = True
      for (connection, conn_game_id, user_id) in self.factory.connectionList:
         if user_id == oldentry[2]:
            lastconnection = False
            break

      # inform all clients that this user left if this was the last connection belonging to the user
      if lastconnection:
         # unregister this user from the game
         for gp in GameParticipant.objects.filter( Game = self.game, Participant = self.user ):
            gp.delete()
            gp.save()

         self.debug('This was the last connection for this user notifying all users associated to game')
         for (connection, conn_game_id, user_id) in self.factory.connectionList:
            if conn_game_id == self.game.id:
               self.writeToTransport(["PART", self.user.id, self.user.username], transport = connection.transport)

      # ok, we are unloaded
      self.already_unloaded = True
      

   def lineReceived(self, data):

      response = ["ERROR","Unspecified error"]

      # TODO clean up giant try block
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

            # load the game object
            # TODO use a shared copy in the factory
            self.game = Game.objects.get(pk = cmd[1])

            # determine if this user is the owner or what
            if self.game.id == self.user.id:
               newstate = 'O'
            else:
               newstate = 'U'

            # TODO insert a validation thing to make sure user has perm to join this game
            is_dupe_user = False
               
            # tell the newcomer all the people who are already in this game
            for part in GameParticipant.objects.filter(Game = self.game):
               # TODO should probably use a JOIN here.. however you do that with django :O
               this_user = User.objects.get(pk = part.Participant.id)

               # if this *is* the current user, then they are in the game twice?  make a note of that..
               is_dupe_user = is_dupe_user or (part.Participant.id == self.user.id)

               self.writeToTransport(["JOIN", this_user.id, this_user.username])
               
            # register this connection as being associated with this game in the factory.             
            self.factory.addToConnectionDB(self, self.game.id, self.user.id)
            
            # if the user was not already in the game participant list, we need to let everyone know that now they are!
            if not is_dupe_user:

               # now make a participant entry to tie this user to the game in the database
               newparticipant = GameParticipant( Participant=self.user, Game=self.game, State=newstate )
               newparticipant.save()


               # now find all connections associated with this game and tell them about the newcomer 
               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  if conn_game_id == self.game.id:
                     self.writeToTransport(["JOIN", self.user.id, self.user.username], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'CHAT'):
            message = cmd[1]
            
            for (connection,conn_game_id, conn_user_id) in self.factory.connectionList:
               if conn_game_id == self.game.id:
                  self.writeToTransport(["CHAT", self.user.username, message], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'MOVE'):
            coord = cmd[1]
            color = cmd[2]
            parent_node = cmd[3]
            comments = cmd[4]
            
            # TODO once we have a timer, hook this up to the proper value
            time_left = 0

            # TODO validate the move, if its invalid alert the players that they need 
            # to reload their boards to resync with the server.  The idea is that eidogo, once
            # properly modified, will NEVER allow an illegal move.  If it does we assume the 
            # player is somehow desynced (which shouldn't happen either)
            
            # Now store the move in the database
            self.factory.storeMove(self.game.id, coord, color, parent_node, comments, time_left)
            

            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               # send it to all players associated with the current game.. but not the user who made the move
               # TODO the user that made the move should be included here too, and his move should *not* trigger eidogo to move until the server validates the move!! but for now...
               if conn_game_id == self.game.id and self.transport.sessionno != connection.transport.sessionno:
                  self.writeToTransport(["MOVE", coord, color], transport = connection.transport)

            response = CTS


         # part command ; index 1 is a channel name
         elif(cmd[0] == 'PART'):
            self.already_unloaded = True
            self.connectionLost()
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

      if transport.sessionno != self.transport.sessionno:
         pre_char = transport.sessionno
      else:
         pre_char = '-'

      self.debug('%s> %s' % (pre_char, out_json))

      transport.write(out_json + "\r\n")
      

class GoServerFactory(protocol.ServerFactory):
   protocol = GoServerProtocol
         
   def __init__(self):      
      # this maps connections to user IDs
      self.connectionList = []

      # this contains all the games which the server is currently tracking.
      self.games = {}

      # TODO register an every-XX-second call for us to perform a ping
      # self.lc = task.LoopingCall(self.announce)
      # self.lc.start(30)

   def addToConnectionDB(self, connection, game_id, user_id):
      self.connectionList.append( [connection, game_id, user_id] )

   def delFromConnectionDB(self, connection, game_id):
      """Delete an entry from the connection database.  Return the entry itself as it was before being deleted."""
      for i in range(0,len(self.connectionList)): 
         (db_connection,db_game_id,db_user_id) = self.connectionList[i]
         
         if connection.transport.sessionno == db_connection.transport.sessionno:
            oldentry = self.connectionList[i]
            del self.connectionList[i];
            return oldentry

   def storeMove(game_id, coord, color, parentNode, comments, time_left):
      """
      Store a move and any related data in to the GameNode / GameProperty Tables
      """
      pass


reactor.listenTCP(PORT, GoServerFactory())
reactor.run()

