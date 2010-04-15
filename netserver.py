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

from go.GoServer.models import Game, GameParticipant, GameProperty, GameNode, Board, GameTree
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

   # user this connection is related to
   user = False
   
   def debug(self, msg):
      print '%s %04d | %s' % (datetime.datetime.now(), self.transport.sessionno, msg)
      
   def connectionMade(self):
      # dictionary where we store the users state per game
      self.gamestate = {}

      self.debug('Connection opened')
   
   def connectionLost(self, reason):
                     
      for oldentry in self.factory.delFromConnectionDB(self):
 
         game = Game.objects.get(pk = oldentry[1])

         self.debug('Unregistering where game=%d and user=%s' % (game.id, self.user.username) )

         # for each game this user was associated with, determine if this was their last conn and perform a PART if it was

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
            GameParticipant.objects.filter( Game = game, Participant = self.user).update( Present = False )

            # let everyone in this game know
            for (connection, conn_game_id, user_id) in self.factory.connectionList:
               if conn_game_id == game.id:
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

      else:

         # load the game object
         game = self.factory.getGame( cmd[1] )

         # join game command ; index 1 is a game name
         if(cmd[0] == 'JOIN'):        

            # TODO insert a validation thing to make sure user has perm to join this game

            # assume user is new
            new_user = True

            # this should really never return more than one row....
            part_that_joined = GameParticipant.objects.filter(Game = game, Participant=self.user)[0]
            new_user = False
            part_that_joined.Present = True
            part_that_joined.save()
            
            self.gamestate[ game.id ] = part_that_joined.State

            # TODO .. can't figure out why this next line does not work the same as the preceeding 'for' block.. but it doesn't.. i dunno
            # new_user = ( GameParticipant.objects.filter(Game = self.game, Participant=self.user).update(Present = True) != 0 )

            # inform new user about all present participants besides himself (that'll happen latter when we broadcast this join to *everyone*)
            for part in GameParticipant.objects.filter(Game = game, Present=True):
               if part.Participant.id != self.user.id:
                  self.writeToTransport(["JOIN", game.id, part.Participant.id, part.Participant.username, part.State])

            # if the user was not already in the game participant list, we need to let everyone know that now they are!
            if new_user:

               # get the state which we will use in the new row
               if game.Owner.id == self.user.id:
                  newstate = 'O'
               else:
                  newstate = 'U'

               # now make a participant entry to tie this user to the game in the database
               part_that_joined = GameParticipant( Participant=self.user, Game=game, State=newstate, Present=True )
               part_that_joined.save()

            # register this connection as being associated with this game in the factory.             
            self.factory.addToConnectionDB(self, game.id, self.user.id)

            # now find all connections associated with this game and tell them about the newcomer 
            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               if conn_game_id == game.id:
                  self.writeToTransport(["JOIN", game.id, self.user.id, self.user.username, part_that_joined.State], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'CHAT'):
            message = cmd[2]

            for (connection,conn_game_id, conn_user_id) in self.factory.connectionList:
               if conn_game_id == game.id:
                  self.writeToTransport(["CHAT", game.id, self.user.username, message], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'MOVE'):
            coord = cmd[2]
            color = cmd[3]
            node_id = cmd[4]
            parent_node_id = cmd[5]
            comments = ""
            
            # TODO once we have a timer, hook this up to the proper value
            time_left = 0

            # Now store the move in the database
            
            if not self.factory.storeMove(game.id, coord, color, self.gamestate[ game.id ], node_id, parent_node_id, comments, time_left):
               # illegal move! give them the sync message which indicates they are out of sync
               response = ["SYNC", "Move rejected"]

            else:

               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  # send it to all players associated with the current game.. but not the user who made the move
                  # TODO the user that made the move should be included here too, and his move should *not* trigger eidogo to move until the server validates the move!! but for now...
                  if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(["MOVE", game.id, coord, color], transport = connection.transport)
                     
               response = CTS


         elif(cmd[0] == 'DEAD'):
            coord = cmd[2]

            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               # send it to all players associated with the current game.. but not the user who made the move
               # TODO the user that made the move should be included here too, and his move should *not* trigger eidogo to move until the server validates the move!! but for now...
               if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                  self.writeToTransport(["DEAD", game.id, coord], transport = connection.transport)

            response = CTS

         # ignore any BEGN that doesnt come from the game owner
         elif cmd[0] == 'BEGN' and game.Owner == self.user:

            # TODO prevent BEGN messages on games which are already PlayersAssigned = True

            accepted_user = int(cmd[2])

            if self.factory.user_game_offers.has_key( accepted_user ):
               (board_size, main_time, komi, color) = self.factory.user_game_offers[ accepted_user ]

               # Set the game to PlayersAssigned = true, set game variables as dictated by the offer
               game.PlayersAssigned = True
               game.BoardSize = board_size
               game.MainTime = main_time
               game.Komi = komi
               game.save()

               # Determine which player is to be changed to what color and change them
               if color == 'W':
                  other_color = 'B'
               else:
                  other_color = 'W'

               username = {}

               for part in GameParticipant.objects.filter( Game = game, Participant__in = [ game.Owner.id, accepted_user ] ):
                  if part.Participant.id == accepted_user:
                     part.State = color
                     part.save()
                     username[ color ] = part.Participant.username

                  elif part.Participant.id == game.Owner.id:
                     part.State = other_color
                     part.save()
                     username[ other_color ] = part.Participant.username

               # set up the game-info node
               gi_node = GameNode(Game = game)
               gi_node.save()

               # translate to SGF sizes
               translate_game_size = {'19x19': '19',
                                      '13x13': '13',
                                      '9x9': '9'}

               size = translate_game_size[ game.BoardSize ]

               print size,',',game.BoardSize

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
                  self.writeToTransport(["BEGN", game.id], transport = connection.transport)

               response = CTS

            else:

               self.writeToTransport(["ERROR", "Invalid BEGN parameter: %d has no registered offers" % int(cmd[2]) ])

               response = CTS


         elif cmd[0] == 'OFFR':

            # store the offer in the factory offer database for referencing later
            self.factory.user_game_offers[ int(self.user.id) ] = [ cmd[2], cmd[3], cmd[4], cmd[5] ]

            # Send a message to all participants notifying them about your offer
            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               self.writeToTransport(["OFFR", game.id, cmd[2], cmd[3], cmd[4], cmd[5], self.user.id, self.user.username], transport = connection.transport)

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

   def debug(self, msg):
      print '%s Fac | %s' % (datetime.datetime.now(), msg)
         
   def __init__(self):      
      # this maps connections to user IDs
      self.connectionList = []

      # this contains all the games which the server is currently tracking.
      self.games = {}      

      # this contains a board object for each game
      self.boards = {}

      # this is a dict storing the offers users make to play games
      # { user_id: [ board size, main time, komi, color ], .... } 
      self.user_game_offers = {}

   def addToConnectionDB(self, connection, game_id, user_id):
      self.connectionList.append( [connection, game_id, user_id] )

   def delFromConnectionDB(self, connection):
      """Delete an entry from the connection database.  Return the entry itself as it was before being deleted."""

      deletedList = []
      deleteKeys = []
      for i in range(0,len(self.connectionList)): 
         (db_connection,db_game_id,db_user_id) = self.connectionList[i]
         
         if connection.transport.sessionno == db_connection.transport.sessionno:
            deleteKeys.append(i)
            deletedList.append( self.connectionList[i] )

      for key in deleteKeys:
         del self.connectionList[key];

      return deletedList

                  
   def getGame(self, game_id):
      """ This func provides a game object.  it caches games to prevent needless reloading """
      
      if not self.games.has_key( game_id ):
         self.games[ game_id ] = Game.objects.get(pk = game_id)
         
      return self.games[ game_id ]
      
      
   def getBoard(self, game_id):
      """ This func provides a board object, loads from cache if necessary """
      
      if not self.boards.has_key( game_id ):
         self.boards[ game_id ] = Board( self.getGame( game_id ) )
         
      return self.boards[ game_id ]

      
   def storeMove(self, game_id, coord, color, playerColor, client_node_id, client_parent_node_id, comments, time_left):
      """
      Store a move and any related data in to the GameNode / GameProperty Tables
      """
      
      if playerColor != color:
         self.debug("Illegal move received: Connection with color %s attempted to play %s" % (playerColor, color))
         return False

      game = self.getGame( game_id ) 
      board = self.getBoard( game_id )

      ## First load the parent node from our DB

      # find the parent ID corresponding to the parent ID eidogo provided us with
      parentqs = GameNode.objects.filter(Game = game, ClientNodeId = client_parent_node_id)
      
      if len(parentqs):
         parent_node = parentqs[0]
      else:
         parent_node = GameNode.objects.filter(Game = game).order_by('-id')[0]

      # attempt to make the move on the board
      (legalMove, violation) = board.makeMove( parent_node, coord, color )
      if not legalMove:
         
         # that move is invalid, notify caller
         self.debug("Illegal move received: %s" % violation)
         return False

      # create the node
      if parent_node:
         node = GameNode(Game = game, ParentNode = parent_node, ClientNodeId = client_node_id )
      else:         
         # this shouldnt ever happen because before players have a chance to move we've created
         # the game-info node
         node = GameNode(Game = game)

      node.save()

      # create the property
      move_prop = GameProperty(Node = node, Property = color, Value = coord)
      move_prop.save()

      # success!
      return True



reactor.listenTCP(PORT, GoServerFactory())
reactor.run()

