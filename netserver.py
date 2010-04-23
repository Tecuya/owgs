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
      self.gamepartstate = {}

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
            existing_rows = GameParticipant.objects.filter(Game = game, Participant=self.user)
            if(len(existing_rows) > 0):
               new_user = False
               part_that_joined = existing_rows[0]
               part_that_joined.Present = True
               part_that_joined.save()
            
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

            # store our game state so we are aware what color/state we are in this game later
            self.gamepartstate[ game.id ] = part_that_joined.State

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
            sn = cmd[4]            
            comments = cmd[5]
            
            # TODO once we have a timer, hook this up to the proper value
            time_left = 0

            # Now store the move in the database            
            new_node_id = self.factory.storeMove(game.id, coord, color, self.gamepartstate[ game.id ], sn, comments, time_left)


            if not new_node_id:

               # illegal move! give them the sync message which indicates they are out of sync
               response = ["SYNC", game.id, "Move rejected"]

            else:

               # save the focusNode
               game.FocusNode = int(new_node_id)
               game.save()
               
               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  # send it to all players associated with the current game.. but not the user who made the move
                  if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(["MOVE", game.id, coord, new_node_id], transport = connection.transport)
                     

               # notify the client of the node ID for the node
               self.writeToTransport(["NODE", game.id, new_node_id], self.transport)
               
               response = CTS


         elif(cmd[0] == 'DEAD'):
            coord = cmd[2]

            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               # send it to all players associated with the current game.. but not the user who made the move
               if self.transport.sessionno != connection.transport.sessionno:
                  self.writeToTransport(["DEAD", game.id, coord], transport = connection.transport)

            response = CTS

         # ignore any BEGN that doesnt come from the game owner
         elif cmd[0] == 'BEGN' and game.Owner == self.user:

            # TODO prevent BEGN messages on games which are already PlayersAssigned = True

            accepted_user = int(cmd[2])

            if self.factory.user_game_offers.has_key( accepted_user ):
               (board_size, main_time, komi, color) = self.factory.user_game_offers[ accepted_user ]

               # Set the game to in-progress, set game variables as dictated by the offer
               game.State = 'I'
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
               # TODO more properties.. DT.. others?
               for (prop, value) in [ ['GM', 1],
                                      ['FF', 4],
                                      ['AP', 'owgs:git'],
                                      ['SZ', size],
                                      ['HA', 0],
                                      ['KM', komi],
                                      ['PB', username['B']],
                                      ['PW', username['W']],
                                      ['CA', 'UTF-8'],
                                      ['SN', gi_node.id]]:
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

         elif cmd[0] == 'NAVI':

            # only allow navigation commands when game type is teaching or game state is finished
            if game.Type == 'T' or game.State == 'F':
            
               # prepare the command to send to clients
               cmd = ["NAVI", game.id, cmd[2]]

               # same the focusNode
               game.FocusNode = int(cmd[2])
               game.save()

               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  
                  # not the right game? skip!
                  if conn_game_id != game.id:
                     continue

                  # dont send to the connection that made the move
                  if self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(cmd, transport = connection.transport)

               response = CTS

            else:
               
               response = ["SYNC", game.id, "Navigation commands not allowed"]
               
         elif cmd[0] == 'UNDO':

            # get the focused node
            focus_node = GameNode.objects.get(pk = game.FocusNode)

            # get the clients color
            client_is_color = self.gamepartstate[ game.id ]

            # get the props from the last two moves
            fn_props = GameProperty.objects.filter( Node = focus_node, Property__in = ['W','B'])
            pn_props = GameProperty.objects.filter( Node = focus_node.ParentNode,  Property__in = ['W','B'])
            
            undoForPass = 0

            # if the game has ended (two passes occurred)
            if len(fn_props) and len(pn_props) and fn_props[0].Value == 'tt' and pn_props[0].Value == 'tt':
               
               # then undo the pass that the undo-clicking player made
               if fn_props[0].Property == client_is_color:
                  undoForPass = focus_node.ParentNode.id
               else:
                  undoForPass = focus_node.ParentNode.ParentNode.id

            # if the undo was determined to be a pass, perform the undo 
            if undoForPass:
               
               # give a NAVI to all clients to navigate back to the node we did an undo to
               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  self.writeToTransport(["NAVI", game.id, undoForPass], transport = connection.transport)
               
               game.FocusNode = undoForPass
               game.PendingUndoNode = 0
               game.save()
               
               response = CTS

            elif game.AllowUndo:

               invalid = True
               
               self.debug("Received undo request while focus node is " + str(focus_node.id))
               
               if focus_node:
                  if len( GameProperty.objects.filter( Node = focus_node, Property = client_is_color ) ):
                     game.PendingUndoNode = focus_node.ParentNode.id
                     game.save()
                     invalid = False
                  else:
                     if focus_node.ParentNode:
                        if len( GameProperty.objects.filter( Node = focus_node.ParentNode, Property = client_is_color ) ):
                          game.PendingUndoNode = focus_node.ParentNode.ParentNode.id
                          game.save()
                          invalid = False
                  
               if not invalid:                  
                  self.debug("Undo validated ; resolves to node " + str(game.PendingUndoNode))
                  for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                     # send it to all players associated with the current game.. but not the user who made the request
                     if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                        self.writeToTransport(["UNDO", game.id, self.gamepartstate[ game.id]], transport = connection.transport)
               else:
                  self.debug("Undo request failed for game focus node " + str(game.FocusNode))

               # send a CTS back to requesting player
               response = CTS

            else:
               # if you undo on a game that doesnt allow it you are desynced.
               response = ["SYNC", game.id, "Undo disallowed"]               


         elif cmd[0] == 'OKUN':
            
            if game.PendingUndoNode:
               
               # give a NAVI to all clients to navigate back to the node we did an undo to
               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  self.writeToTransport(["NAVI", game.id, game.PendingUndoNode], transport = connection.transport)
               
               game.FocusNode = game.PendingUndoNode
               game.PendingUndoNode = 0
               game.save()

               response = CTS            
            else:
               response = ["SYNC", game.id, "Undo accepted when there is no pending undo."]               
               
         
         elif cmd[0] == 'NOUN':
            
            if game.PendingUndoNode:

               game.PendingUndoNode = 0

               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  # send it to all players associated with the current game.. but not the user who made the request
                  if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(["NOUN", game.id], transport = connection.transport)

               response = CTS

            else:
               response = ["SYNC", game.id, "Rejected undo when no undo is pending"]

         elif cmd[0] == 'RSGN':            
            # player resigns

            client_is_color = self.gamepartstate[ game.id ]
            
            if client_is_color == 'W':
               other_color = 'B'
            else:
               other_color = 'W'
            
            # set game stats
            game.State = 'F'
            game.Winner = other_color
            game.WinType = 'R'
            game.save()

            # find the root node and set a RE property with the resignation info
            rootnode = GameNode.objects.get( Game = game, ParentNode__isnull = True )

            reprop = GameProperty( Node = rootnode, Property = 'RE', Value=other_color+'+R' )
            reprop.save()

            for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
               self.writeToTransport(["RSLT", game.id, other_color, 'R', False], transport = connection.transport)
            
            response = CTS

         elif cmd[0] == 'SCOR':
            
            # get client color
            client_is_color = self.gamepartstate[ game.id ]

            if client_is_color == 'W':
               other_color = 'B'
            else:
               other_color = 'W'

            # store the results from the player in the factory 
            score = {'color': client_is_color, 
                        'territory_w': cmd[2],
                        'captures_w': cmd[3],
                        'prisoners_b': cmd[4],
                        'score_w': cmd[5],
                        'territory_b': cmd[6],
                        'captures_b': cmd[7],
                        'prisoners_w': cmd[8],
                        'score_b': cmd[9]}

            # if the scoring dict doesnt have our game then add it
            if not self.factory.user_game_scoring.has_key( game.id ):
               self.factory.user_game_scoring[game.id] = []

            # if the other player has also had his results stored in the factory, compare the
            # results and make sure they match            
            accepted_entry = False
            for item in self.factory.user_game_scoring[ game.id ]:
               if (item['color'] == other_color and
                   len(item['territory_w']) == len(score['territory_w']) and
                   item['captures_w'] == score['captures_w'] and 
                   item['prisoners_b'] == score['prisoners_b'] and
                   item['score_w'] == score['score_w'] and
                   len(item['territory_b']) == len(score['territory_b']) and
                   item['captures_b'] == score['captures_b'] and
                   item['prisoners_w'] == score['prisoners_w'] and
                   item['score_b'] == score['score_b']):

                  accepted_entry = score
                  break
            
            if not accepted_entry:
               self.factory.user_game_scoring[game.id].append( score )
               
            else:

               # calculate results and store them in the game
               
               if score['score_w'] > score['score_b']:
                  winner_color = 'W'
                  delta = str(score['score_w'] - score['score_b'])
                  result = 'W+' + delta
               else:
                  winner_color = 'B'
                  delta = str(score['score_b'] - score['score_w'])
                  result = 'B+' + delta
                                 
               game.State = 'F'
               game.WinType = 'S'
               game.ScoreDelta = delta
               game.Winner = winner_color
               game.save()

               strvar = (len(score['territory_w']),
                         score['captures_w'],
                         score['prisoners_b'],
                         str(game.Komi),
                         str(score['score_w']),
                         len(score['territory_b']),
                         score['captures_b'],
                         score['prisoners_w'],
                         str(score['score_b']),
                         result) 

               # prepare the last node which contains all the territory markers and stuff
               comment_text = "Game finished.\n\n" + \
                   "White: %d territory, %d captures, %d prisoners, %s komi\n" + \
                   "White Total: %s\n\n" + \
                   "Black: %d territory, %d captures, %d prisoners\n" + \
                   "Black Total: %s\n\n" + \
                   "Result: %s\n" 

               comment = comment_text % strvar

               
        
               focus_node = GameNode.objects.get(pk = game.FocusNode)
               territorynode = GameNode( Game = game, ParentNode = focus_node )
               territorynode.save()

               cprop = GameProperty( Node = territorynode, Property = 'C', Value=comment )
               cprop.save()

               # TODO ewww.. make our model / SGF creator smart enough to do something about this..
               for co in score['territory_w']:
                  twprop = GameProperty( Node = territorynode, Property = 'TW', Value = co)
                  twprop.save()

               for co in score['territory_b']:
                  twprop = GameProperty( Node = territorynode, Property = 'TB', Value = co)
                  twprop.save()

               # find the root node and set a RE property with the score
               rootnode = GameNode.objects.get( Game = game, ParentNode__isnull = True )
               reprop = GameProperty( Node = rootnode, Property = 'RE', Value=result )
               reprop.save()
               
               # transmit results to everyone
               for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
                  self.writeToTransport(["RSLT", game.id, winner_color, 'S', result], transport = connection.transport)
            
            response = CTS


      # write whatever response we came up with above
      self.writeToTransport(response, self.transport)

      # if we are telling them they are out of sync, d/c them
      if response[0] == 'SYNC':
         self.transport.loseConnection()

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
      # TODO this needs a game id... huh
      self.user_game_offers = {}

      # this holds scores submitted by users for comparison/validation with their opponent's submitted scores
      self.user_game_scoring = {}

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


   def getConnectionForUserState(self, game_id, state):

      for (connection, conn_game_id, conn_user_id) in self.factory.connectionList:
         # this is the right game at least?
         if conn_game_id == game_id:            
            user = User.objects.get(pk = conn_user_id)
            part = GameParticipant.objects.get(Participant = user, Game = self.getGame( game_id ))
            if part.State == state:
               return connection

      return False

                  
   def getGame(self, game_id, refresh = False):
      """ This func provides a game object.  it caches games to prevent needless reloading """
      
      if refresh or not self.games.has_key( game_id ):
         self.games[ game_id ] = Game.objects.get(pk = game_id)
         
      return self.games[ game_id ]
      
      
   def getBoard(self, game_id):
      """ This func provides a board object, loads from cache if necessary """
      
      if not self.boards.has_key( game_id ):
         self.boards[ game_id ] = Board( self.getGame( game_id ) )
         
      return self.boards[ game_id ]

      
   def storeMove(self, game_id, coord, color, playerColor, server_node_id, comments, time_left):
      """
      Store a move and any related data in to the GameNode / GameProperty Tables
      """

      if playerColor != color:
         self.debug("Illegal move received: Connection with color %s attempted to play %s" % (playerColor, color))
         return False

      game = self.getGame( game_id ) 
      board = self.getBoard( game_id )

      ## First load the parent node from our DBx

      # find the parent ID corresponding to the parent ID eidogo provided us with
      try:
         parent_node = GameNode.objects.get( pk = server_node_id, Game = game )
      except:
         self.debug("Illegal move received: SN %s is invalid" % str(server_node_id) )
         return False

      # attempt to make the move on the board
      (legalMove, violation) = board.makeMove( parent_node, coord, color )
      if not legalMove:
         
         # that move is invalid, notify caller
         self.debug("Illegal move received: %s" % violation)
         return False

      # create the new node
      node = GameNode(Game = game, ParentNode = parent_node)
      node.save()

      # create the property
      move_prop = GameProperty(Node = node, Property = color, Value = coord)
      move_prop.save()
      
      # success!
      return node.id



reactor.listenTCP(PORT, GoServerFactory())
reactor.run()

   

