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

from go.GoServer.models import Game, GameParticipant, GameProperty, GameNode
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser

from django.db.models import F, Max, Min, Count

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


   def debug(self, msg):
      print '%s %04d | %s' % (datetime.datetime.now(), self.transport.sessionno, msg)
      
   def connectionMade(self):
      self.debug('Connection opened')
   
   def connectionLost(self, reason):
                     
      self.debug('Unregistering where game=%d and user=%s' % (self.game.id, self.user.username) )

      # delete connection from connection list
      oldentry = self.factory.delFromConnectionDB(self, self.game.id)

      # determine if this was the last connection from this user
      users_other_conns = 0
      for (connection, conn_game_id, user_id) in self.factory.connectionList:
         if user_id == oldentry[2]:
            users_other_conns += 1
      
      self.debug('User has %d other connections on this game' % users_other_conns)

      # inform others that this user left if this was the last connection belonging to the user
      if users_other_conns == 0:

         # mark this user as not-present
         self.debug('Marking user game participant row Present=False')
         GameParticipant.objects.filter( Game = self.game, Participant = self.user).update( Present = False )
         
         # let everyone in this game know
         for (connection, conn_game_id, user_id) in self.factory.connectionList:
            if conn_game_id == self.game.id:
               self.writeToTransport(["PART", self.user.id, self.user.username], transport = connection.transport)


   def lineReceived(self, data):

      response = ["ERROR","Unspecified error"]


      cmd = json.loads(data)

      self.debug( '< '+str(cmd) )

      # connect command ; index 1 is a session_key
      if(cmd[0] == 'SESS'):
         self.session_key = cmd[1]

         # load up the session's user object
         session = Session.objects.get(session_key = self.session_key)
         uid = session.get_decoded().get('_auth_user_id')
         if uid == None:
            # TODO support anonymous users
            self.user = AnonymousUser()
         else:
            self.user = User.objects.get(pk=uid)

         response = CTS


      # we arent connected and we dont have a session? not allowed!
      elif( self.session_key == False ):
         response = ['ERROR','No session_key; you must SESS first.']


      # join game command ; index 1 is a game name
      elif(cmd[0] == 'JOIN'):        

         # load the game object
         # TODO use a shared copy in the factory cache
         self.game = Game.objects.get(pk = cmd[1])

         # TODO insert a validation thing to make sure user has perm to join this game

         # assume user is new
         new_user = True

         # this should really never return more than one row....
         for part_that_joined in GameParticipant.objects.filter(Game = self.game, Participant=self.user):
            new_user = False
            part_that_joined.Present = True
            part_that_joined.save()

         # TODO .. can't figure out why this next line does not work the same as the preceeding 'for' block.. but it doesn't.. i dunno
         # new_user = ( GameParticipant.objects.filter(Game = self.game, Participant=self.user).update(Present = True) != 0 )

         # inform new user about all present participants besides himself (that'll happen latter when we broadcast this join to *everyone*)
         for part in GameParticipant.objects.filter(Game = self.game, Present=True):
            if part.Participant.id != self.user.id:
               self.writeToTransport(["JOIN", part.Participant.id, part.Participant.username, part.State])

         # if the user was not already in the game participant list, we need to let everyone know that now they are!
         if new_user:

            # get the state which we will use in the new row
            if self.game.Owner.id == self.user.id:
               newstate = 'O'
            else:
               newstate = 'U'

            # now make a participant entry to tie this user to the game in the database
            part_that_joined = GameParticipant( Participant=self.user, Game=self.game, State=newstate, Present=True )
            part_that_joined.save()

         # register this connection as being associated with this game in the factory.             
         self.factory.addToConnectionDB(self, self.game.id, self.user.id)

         # now find all connections associated with this game and tell them about the newcomer 
         for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
            if conn_game_id == self.game.id:
               self.writeToTransport(["JOIN", self.user.id, self.user.username, part_that_joined.State], transport = connection.transport)

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


      elif(cmd[0] == 'DEAD'):
         coord = cmd[1]

         for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
            # send it to all players associated with the current game.. but not the user who made the move
            # TODO the user that made the move should be included here too, and his move should *not* trigger eidogo to move until the server validates the move!! but for now...
            if conn_game_id == self.game.id and self.transport.sessionno != connection.transport.sessionno:
               self.writeToTransport(["DEAD", coord], transport = connection.transport)

         response = CTS

      # ignore any BEGN that doesnt come from the game owner
      elif cmd[0] == 'BEGN' and self.game.Owner == self.user:

         # TODO prevent BEGN messages on games which are already PlayersAssigned = True

         accepted_user = int(cmd[1])

         if self.factory.user_game_offers.has_key( accepted_user ):
            (board_size, main_time, komi, color) = self.factory.user_game_offers[ accepted_user ]

            # Set the game to PlayersAssigned = true, set game variables as dictated by the offer
            self.game.PlayersAssigned = True
            self.game.BoardSize = board_size
            self.game.MainTime = main_time
            self.game.Komi = komi
            self.game.save()

            # Determine which player is to be changed to what color and change them
            if color == 'W':
               other_color = 'B'
            else:
               other_color = 'W'

            username = {}

            for part in GameParticipant.objects.filter( Game = self.game, Participant__in = [ self.game.Owner.id, accepted_user ] ):
               if part.Participant.id == accepted_user:
                  part.State = color
                  part.save()
                  username[ color ] = part.Participant.username

               elif part.Participant.id == self.game.Owner.id:
                  part.State = other_color
                  part.save()
                  username[ other_color ] = part.Participant.username
            
            # set up the game-info node
            gi_node = GameNode(Game = self.game)
            gi_node.save()

            # translate to SGF sizes
            translate_game_size = {'19x19': '19',
                                   '13x13': '13',
                                   '9x9': '9'}
            
            size = translate_game_size[ self.game.BoardSize ]

            print size,',',self.game.BoardSize

            # TODO support handicaps
            # TODO export our version to AP property
            for (prop, value) in [ ['GM', 1],
                                   ['FF', 4],
                                   ['AP', 'owgs:git'],
                                   ['SZ', size],
                                   ['HA', 0],
                                   ['KM', komi],
                                   ['PB', username['B']],
                                   ['PW', username['W']],
                                   ['CA', 'UTF-8'] ]:
               prop = GameProperty(Node = gi_node, Property = prop, Value = value)
               prop.save()
                                   
                                   
            # Send a message to all participants notifying them that the game has begun
            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               self.writeToTransport(["BEGN"], transport = connection.transport)

            response = CTS

         else:

            self.writeToTransport(["ERROR", "Invalid BEGN parameter: %d has no registered offers" % int(cmd[1]) ])

            response = CTS


      elif cmd[0] == 'OFFR':

         # store the offer in the factory offer database for referencing later
         self.factory.user_game_offers[ int(self.user.id) ] = [ cmd[1], cmd[2], cmd[3], cmd[4] ]

         # Send a message to all participants notifying them about your offer
         for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
            self.writeToTransport(["OFFR", cmd[1], cmd[2], cmd[3], cmd[4], self.user.id, self.user.username], transport = connection.transport)

         response = CTS

            

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

      # this is a dict storing the offers users make to play games
      # { user_id: [ board size, main time, komi, color ], .... } 
      self.user_game_offers = {}

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


   def storeMove(self, game_id, coord, color, parentNode, comments, time_left):
      """
      Store a move and any related data in to the GameNode / GameProperty Tables
      """
      
      # TODO cache these or something
      game = Game.objects.get(pk = game_id)

      # TODO get the true position in the game tree from eidogo.. right now we just assume
      # every move is the latest move and there is only the main line
      # parent_node = GameNode.objects.filter(Game = game).aggregate(Max('id'))['id__max']
      parent_node = GameNode.objects.filter(Game = game).order_by('-id')[0]

      # create the node
      if parent_node:
         node = GameNode(Game = game, ParentNode = parent_node )
      else:         
         # this shouldnt ever happen because before players have a chance to move we've created
         # the game-info node
         node = GameNode(Game = game)

      node.save()

      # create the property
      move_prop = GameProperty(Node = node, Property = color, Value = coord)
      move_prop.save()


reactor.listenTCP(PORT, GoServerFactory())
reactor.run()

