#!/usr/bin/env python

# python included modules
import datetime, time, math, cjson, sys

# twisted
from twisted.internet import protocol, reactor
from twisted.protocols import basic

# django land
from django.core.management import setup_environ
from go import settings

setup_environ(settings)

from django.db.models import F, Max, Min, Count
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser
from go.GoServer.models import Game, GameParticipant, GameProperty, GameNode, Board, GameTree, Chat, ChatParticipant


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

      self.debug('connectionLost fired')

      # remove from any chats we are in
      for oldentry in self.factory.delFromChatConnectionDB(self):
         
         # load the chat object
         chat = self.factory.getChat( oldentry[1] )

         # determine if this was the last connection from this user
         users_other_conns = 0
         for (connection, conn_chat_id, user_id) in self.factory.chatConnectionList:
            if user_id == oldentry[2]:
               users_other_conns += 1

         self.debug('User other conns %d' % users_other_conns)

         if users_other_conns == 0:

            ChatParticipant.objects.filter( Chat = chat, Participant = self.user).update( Present = False )

            # let everyone in this game know
            for (connection, conn_chat_id, user_id) in self.factory.chatConnectionList:
               if conn_chat_id == chat.id:
                  self.writeToTransport(["PCHT", chat.id, self.user.id, self.user.username], transport = connection.transport)
         

      for oldentry in self.factory.delFromGameConnectionDB(self):

         game = self.factory.getGame( oldentry[1] )

         self.debug('Unregistering where game=%d and user=%s' % (game.id, self.user.username) )

         # for each game this user was associated with, determine if this was their last conn and perform a PART if it was

         # determine if this was the last connection from this user
         users_other_conns = 0
         for (connection, conn_game_id, user_id) in self.factory.gameConnectionList:
            if user_id == oldentry[2]:
               users_other_conns += 1

         self.debug('User has %d other connections on this game' % users_other_conns)

         # inform others that this user left if this was the last connection belonging to the user
         if users_other_conns == 0:            
            self.removeUserFromGame( game )


   def lineReceived(self, data):

      response = ["ERROR","Unspecified error"]


      cmd = cjson.decode(data)

      self.debug( '< '+str(cmd) )

      # connect command ; index 1 is a session_key
      if(cmd[0] == 'SESS'):
         # load up the session's user object
         session = Session.objects.get(session_key = cmd[1])
         uid = session.get_decoded().get('_auth_user_id')
         if uid == None:
            # TODO support anonymous users
            self.user = AnonymousUser()
         else:
            self.user = User.objects.get(pk=uid)

         response = CTS

      # AUTH command; allow a user to log in over the network rather than using a web session
      elif(cmd[0] == 'AUTH'):
         
         user = cmd[1]
         password = cmd[2]
         
         uqs = User.objects.filter(username = user)

         # TODO have a more robust method of deterring brute-force attacks
         time.sleep(1)
         
         if(len(uqs) == 0):
            self.writeToTransport(["AUTH", 0])
         else:
            user = uqs[0]
            if not user.check_password(cmd[2]):
               self.writeToTransport(["AUTH", 0])
            else:
               self.user = user
               self.writeToTransport(["AUTH", 1])
         
         response = CTS
         
      # we arent connected and we dont have a session? not allowed!
      elif( self.user == False ):
         response = ['ERROR','No user attached to this connection; you must SESS or AUTH first.']

      else:

         if cmd[0] in ('JCHT','CHAT','PCHT'):

            # load the chat object if this is a chat command
            chat = self.factory.getChat( cmd[1] )

         elif cmd[0] in ('GAME'):
            
            pass

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
            self.factory.addToGameConnectionDB(self, game.id, self.user.id)

            # now find all connections associated with this game and tell them about the newcomer 
            for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
               if conn_game_id == game.id:
                  self.writeToTransport(["JOIN", game.id, self.user.id, self.user.username, part_that_joined.State], transport = connection.transport)

            # if the game is in progress we need to do a timer update to inform the joiner of the time...
            # TODO we *could* reduce traffic by forcing timerUpdate to only update the timer of this client...
            if game.State == 'I':               
               self.commitTimeVars( game, self.timerUpdate(game) )

            response = CTS
                        
            
         elif(cmd[0] == 'CMNT'):
            message = cmd[2]

            for (connection,conn_game_id, conn_user_id) in self.factory.gameConnectionList:
               if conn_game_id == game.id:
                  self.writeToTransport(["CMNT", game.id, self.user.username, message], transport = connection.transport)

            response = CTS


         elif(cmd[0] == 'MOVE'):
            coord = cmd[2]
            color = cmd[3]
            sn = cmd[4]            
            comments = cmd[5]

            timerRet = self.timerUpdate(game, True)
            if timerRet[0]:

               # the game ended, we can commit our timer vars
               self.commitTimeVars( game, timerRet )

            else:

               # We know they didn't lose on time now.. so see if we can legally make the move (and make it)
               new_node_id = self.factory.storeMove(game.id, coord, color, self.gamepartstate[ game.id ], sn, comments)

               if not new_node_id:

                  # illegal move! give them the sync message which indicates they are out of sync.. dont record the time change
                  response = ["SYNC", game.id, "Move rejected"]

               else:
                  
                  # the move is valid so commit our calculated time variables
                  self.commitTimeVars( game, timerRet )
                  
                  if color == 'W':
                     other_color = 'B'
                  else:
                     other_color = 'W'

                  # change the timer to the other player
                  game.TurnColor = other_color

                  # save the focusNode
                  game.FocusNode = int(new_node_id)

                  # save changes to the game
                  game.save()

                  for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
                     # send it to all players associated with the current game.. but not the user who made the move
                     if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                        self.writeToTransport(["MOVE", game.id, coord, new_node_id], transport = connection.transport)

                  # notify the client of the node ID for the node
                  self.writeToTransport(["NODE", game.id, new_node_id], self.transport)
               
            response = CTS

         elif(cmd[0] == 'TIME'):
            
            # client requests we update the timer.  we only honor if game is 'I'n progress
            if game.State == 'I':
            
               # update the timer for whoevers turn it is
               self.commitTimeVars( game, self.timerUpdate(game) )

            response = CTS

         elif(cmd[0] == 'DEAD'):

            # TODO validate

            coord = cmd[2]

            for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
               # send it to all players associated with the current game.. but not the user who made the move
               if conn_game_id == game.id and  self.transport.sessionno != connection.transport.sessionno:
                  self.writeToTransport(["DEAD", game.id, coord], transport = connection.transport)

            response = CTS

         # ignore any BEGN that doesnt come from the game owner, or is for a game that is not in progress
         elif cmd[0] == 'BEGN' and game.Owner == self.user and game.State == 'P':

            accepted_user = int(cmd[2])

            if self.factory.user_game_offers.has_key( accepted_user ):
               (board_size, main_time, komi, color) = self.factory.user_game_offers[ accepted_user ]

               # Set the game to in-progress, set game variables as dictated by the offer
               game.State = 'I'
               game.BoardSize = board_size
               game.MainTime = main_time
               game.Komi = komi

               # set up initial overtime periods
               game.OvertimeCountW = game.OvertimeCount
               game.OvertimeCountB = game.OvertimeCount

               # set up the main time period
               game.TimePeriodRemainW = game.MainTime
               game.TimePeriodRemainB = game.MainTime

               # always blacks turn
               game.TurnColor = 'B'

               # game starting now!
               game.LastClock = str(time.time())
               game.save()

               # Determine which player is to be changed to what color and change them
               if color == 'W':
                  other_color = 'B'
               else:
                  other_color = 'W'

               # store our game state so we are aware what color/state we are in this game later
               self.gamepartstate[ game.id ] = other_color

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
               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
                  if conn_game_id == game.id:
                     self.writeToTransport(["BEGN", game.id], transport = connection.transport)

            else:
               self.writeToTransport(["ERROR", "Invalid BEGN parameter: %d has no registered offers" % int(cmd[2]) ])

            response = CTS


         elif cmd[0] == 'OFFR':

            # store the offer in the factory offer database for referencing later
            self.factory.user_game_offers[ int(self.user.id) ] = [ cmd[2], cmd[3], cmd[4], cmd[5] ]

            # Send a message to all participants notifying them about your offer
            for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
               if conn_game_id == game.id:
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

               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:

                  # dont send to the connection that made the move
                  if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(cmd, transport = connection.transport)

               response = CTS

            else:
               
               response = ["SYNC", game.id, "Navigation commands not allowed"]
               
         elif cmd[0] == 'UNDO':
            
            # TODO we should do somethign to prevent cheating others out of time by meaningless undos in scoring situations ... i.e. W passes with a lot of time left, B passes with 2 seconds left, W hits undo, does the same move, B has to move (tick tock), then W hits undo again until B runs out of time

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
               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
                  if conn_game_id == game.id:
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
                  for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
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
               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
                  if conn_game_id == game.id:
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

               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
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

            self.broadcastResult(game.id, other_color, 'R', False)
            
            response = CTS

         elif cmd[0] == 'SCOR':
            
            # get client color
            client_is_color = self.gamepartstate[ game.id ]

            if client_is_color == 'W':
               other_color = 'B'
            else:
               other_color = 'W'

            # if the scoring dict doesnt have our game then add it
            if not self.factory.user_game_scoring.has_key( game.id ):
               self.factory.user_game_scoring[game.id] = {'W': False, 'B': False}

            # store the results from the player in the factory 
            score = {
               'color': client_is_color, 
               'territory_w': cmd[2],
               'captures_w': cmd[3],
               'prisoners_b': cmd[4],
               'score_w': cmd[5],
               'territory_b': cmd[6],
               'captures_b': cmd[7],
               'prisoners_w': cmd[8],
               'score_b': cmd[9]}
                              
            item = self.factory.user_game_scoring[ game.id ][ other_color ]
            if not ( item and 
                     len(item['territory_w']) == len(score['territory_w']) and 
                     item['captures_w'] == score['captures_w'] and 
                     item['prisoners_b'] == score['prisoners_b'] and
                     item['score_w'] == score['score_w'] and
                     len(item['territory_b']) == len(score['territory_b']) and 
                     item['captures_b'] == score['captures_b'] and
                     item['prisoners_w'] == score['prisoners_w'] and
                     item['score_b'] == score['score_b'] ):
               
               # broadcast the score to other connected clients
               for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
                  if conn_game_id == game.id and self.transport.sessionno != connection.transport.sessionno:
                     self.writeToTransport(cmd, transport = connection.transport)
                     
               # set the score as this players submitted score
               self.factory.user_game_scoring[game.id][ client_is_color ] = score
            
            else:

               # calculate results and store them in the game, transmit results to clients
               
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

               # transmit result
               self.broadcastResult(game.id, winner_color, 'S', result)
            
            response = CTS

         elif cmd[0] == 'PART':            
            self.removeUserFromGame( game )
            response = CTS

         elif cmd[0] == 'PCHT':

            # let everyone know
            for (connection, conn_chat_id, user_id) in self.factory.chatConnectionList:
               if conn_chat_id == chat.id:
                  self.writeToTransport(["PCHT", chat.id, self.user.id, self.user.username], transport = connection.transport)
            
            response = CTS

         elif cmd[0] == 'JCHT':

            already_present = False
            for (conn, conn_chat_id, conn_user_id) in self.factory.chatConnectionList:
               if chat.id == conn_chat_id and self.user.id == conn_user_id:
                  already_present = True
                  break
            
            a = self.factory.chatConnectionList

            for part in ChatParticipant.objects.filter(Chat = chat, Present = True):
               if part.Participant.id != self.user.id:
                  self.writeToTransport(["JCHT", chat.id, part.Participant.id, part.Participant.username])


            if not already_present:
               self.debug('User joined chat who is not present')

               self.factory.addToChatConnectionDB(self, chat.id, self.user.id)

               for (conn, conn_chat_id, conn_user_id) in self.factory.chatConnectionList:
                  if conn_chat_id == chat.id:
                     self.writeToTransport(["JCHT", chat.id, self.user.id, self.user.username], transport = conn.transport)
            
               existing_rows = ChatParticipant.objects.filter(Chat = chat, Participant=self.user)
               if(len(existing_rows) > 0):
                  existing_rows.update( Present = True )
               else:
                  # now make a participant entry to tie this user to the game in the database
                  part_that_joined = ChatParticipant( Participant=self.user, Chat=chat, Present=True )
                  part_that_joined.save()

            response = CTS


         elif(cmd[0] == 'CHAT'):
            message = cmd[2]

            for (connection,conn_chat_id, conn_user_id) in self.factory.chatConnectionList:
               if conn_chat_id == chat.id:
                  self.writeToTransport(["CHAT", chat.id, self.user.username, message], transport = connection.transport)

            response = CTS

         elif(cmd[0] == 'GAME'):
            # create a new game
            
            game = Game( Owner = self.user, 
                         Type = cmd[1], BoardSize = cmd[2], Komi = cmd[3], 
                         MainTime = cmd[4], OvertimeType = cmd[5], 
                         OvertimePeriod = cmd[6], OvertimeCount = cmd[7] )
            game.save()

            self.writeToTransport(["GAME", game.id])
            
            response = CTS
            
            
      # write whatever response we came up with above
      self.writeToTransport(response, self.transport)

      # if we are telling them they are out of sync, d/c them
      if response[0] == 'SYNC':
         self.transport.loseConnection()

   def broadcastResult(self, game_id, winner_color, win_type, win_param):
      self.debug('Game %d won by %s %s %s' % (game_id, winner_color, win_type, win_param))
      for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
         if conn_game_id == game_id:
            self.writeToTransport(["RSLT", game_id, winner_color, win_type, win_param], transport = connection.transport)

   def timerUpdate(self, game, is_move = False):
      """ Prospective update of the timer .. return the results, but nothing is committed to the game """

      color = game.TurnColor
      
      if color == 'W':
         overtime_count = game.OvertimeCountW
         period_remain = float(game.TimePeriodRemainW)
         is_overtime = game.IsOvertimeW
         other_color = 'B'               

      else:
         overtime_count = game.OvertimeCountB
         period_remain = float(game.TimePeriodRemainB)
         is_overtime = game.IsOvertimeB
         other_color = 'W'            

      # set the new vars to the current state so we dont have to bother later
      new_period_remain = period_remain
      new_is_overtime = is_overtime
      new_overtime_count = overtime_count

      # determine how much time has elapsed
      now_timestamp = time.time()
      time_taken_since_clock = now_timestamp - float(game.LastClock)
      game.LastClock = str(now_timestamp)

      time_loss = False

      # figure out if that exhausted their current time period
      if (period_remain - time_taken_since_clock) < 0:

         exceeded_period_by = time_taken_since_clock - period_remain

         self.debug("%s exceeded period time by %f" % (color, exceeded_period_by))

         if game.OvertimeType == 'N': 
            # there's no overtime and player exceeded the time period?  loser!
            time_loss = 'Main timer exceeded'

         elif game.OvertimeType == 'B':
            # byo-yomi.  determine how many time periods they exceeded by
            periods_exceeded = int( math.floor( exceeded_period_by / game.OvertimePeriod ) ) 

            if is_overtime:
               # we were already on overtime, so we need to add 1 to periods_exceeded to represent the period we just exceeded
               periods_exceeded += 1

            # if they exceeded all their overtime periods they had left, they lose
            if periods_exceeded >= overtime_count-1:
               time_loss = 'Byo yomi periods exceeded.'
            else:
               self.debug("Exceeded %d byo yomi periods" % periods_exceeded)
               new_overtime_count = overtime_count - periods_exceeded
               new_period_remain = game.OvertimePeriod
               new_is_overtime = True

         elif game.OvertimeType == 'C':

            if is_overtime == False:
               # player just moved to overtime?
               new_is_overtime = True
               new_period_remain = game.OvertimePeriod - exceeded_period_by
               if is_move:
                  new_overtime_count = game.OvertimeCount - 1
               else:
                  new_overtime_count = game.OvertimeCount 

            else:
               # player exceeded overtime?? loser!
               time_loss = 'Canadian overtime period exceeded with %d stones remaining to be played' % period_remain

      else:

         if is_overtime:
            # handle overtime

            # ..yeah its overtime
            new_is_overtime = True

            if game.OvertimeType == 'C':

               if overtime_count > 1:
                  if is_move:
                     new_overtime_count = overtime_count - 1
                     
                  new_period_remain = period_remain - time_taken_since_clock
               else:
                  # they fulfilled the stone requirement to reset the overtime period
                  new_overtime_count = game.OvertimeCount
                  new_period_remain = game.OvertimePeriod

            elif game.OvertimeType == 'B':
               self.debug("Byo yomi period reset")
               # byo yomi gets the period reset 
               new_period_remain = game.OvertimePeriod
               
            else:
               # they are on the main timer.. just send them off to negative
               new_period_remain = period_remain - time_taken_since_clock

         else:

            self.debug('Regular time subtraction.. time taken since last clock is : %s' % str(time_taken_since_clock))
            # regular time, and the move did not exhaust their time period.  simple!
            new_period_remain = period_remain - time_taken_since_clock
            
      return [time_loss, color, other_color, new_period_remain, new_overtime_count, new_is_overtime]


   def removeUserFromGame(self, game):

      # mark this user as not-present
      self.debug('Marking user game participant row Present=False')
      GameParticipant.objects.filter( Game = game, Participant = self.user).update( Present = False )

      # let everyone in this game know
      for (connection, conn_game_id, user_id) in self.factory.gameConnectionList:
         if conn_game_id == game.id:
            self.writeToTransport(["PART", game.id, self.user.id, self.user.username], transport = connection.transport)


   def commitTimeVars(self, game, data):
      (time_loss, color, other_color, new_period_remain, new_overtime_count, new_is_overtime) = data

      if time_loss:

         # set game stats
         game.State = 'F'
         game.Winner = other_color
         game.WinType = 'T'
         game.save()

         rootnode = GameNode.objects.get( Game = game, ParentNode__isnull = True )               
         reprop = GameProperty( Node = rootnode, Property = 'RE', Value=other_color+'+T' )
         reprop.save()

         self.broadcastResult( game.id, other_color, 'T', False )

         return False

      else:

         # set the newly calculated time variables
         if color == 'W':
            game.TimePeriodRemainW = str(new_period_remain)
            game.OvertimeCountW = new_overtime_count
            game.IsOvertimeW = new_is_overtime
            game.save()

         else:
            game.TimePeriodRemainB = str(new_period_remain)
            game.OvertimeCountB = new_overtime_count
            game.IsOvertimeB = new_is_overtime
            game.save()

            
         for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
            if conn_game_id == game.id:
               self.writeToTransport(["TIME", game.id, game.IsOvertimeW, game.IsOvertimeB, game.OvertimeCountW, 
                                      game.OvertimeCountB, int(float(game.TimePeriodRemainW)), int(float(game.TimePeriodRemainB))], transport = connection.transport)


         return True

   def writeToTransport(self, response, transport = False):

      if not transport:
         transport = self.transport

      out_json = cjson.encode(response)

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
      # this maps connections to games & user IDs
      self.gameConnectionList = []

      # this maps connections to chat channels & user IDs
      self.chatConnectionList = []

      # this contains all the games which the server is currently tracking.
      self.games = {}      

      # this contains a board object for each game
      self.boards = {}

      # this contains a cache of chat objects                                              
      self.chats = {}

      # this is a dict storing the offers users make to play games
      # { user_id: [ board size, main time, komi, color ], .... } 
      # TODO this needs a game id... huh
      self.user_game_offers = {}

      # this holds scores submitted by users for comparison/validation with their opponent's submitted scores
      self.user_game_scoring = {}

   def addToChatConnectionDB(self, connection, chat_id, user_id):
      self.chatConnectionList.append( [connection, chat_id, user_id] )

   def addToGameConnectionDB(self, connection, game_id, user_id):
      self.gameConnectionList.append( [connection, game_id, user_id] )

   def delFromGameConnectionDB(self, connection):
      """Delete an entry from the connection database.  Return the entry itself as it was before being deleted."""

      deletedList = []
      deleteKeys = []
      for i in range(0,len(self.gameConnectionList)): 
         (db_connection,db_game_id,db_user_id) = self.gameConnectionList[i]
         
         if connection.transport.sessionno == db_connection.transport.sessionno:
            deleteKeys.append(i)
            deletedList.append( self.gameConnectionList[i] )

      for key in deleteKeys:
         del self.gameConnectionList[key];

      return deletedList


   def delFromChatConnectionDB(self, connection):
      """Delete an entry from the connection database.  Return the entry itself as it was before being deleted."""

      deletedList = []
      deleteKeys = []
      for i in range(0,len(self.chatConnectionList)): 
         (db_connection,db_chat_id,db_user_id) = self.chatConnectionList[i]
         
         if connection.transport.sessionno == db_connection.transport.sessionno:
            deleteKeys.append(i)
            deletedList.append( self.chatConnectionList[i] )

      for key in deleteKeys:
         del self.chatConnectionList[key];

      return deletedList


   # TODO decide if we really want this, this is not used anywhere
   def getConnectionForUserState(self, game_id, state):
      
      for (connection, conn_game_id, conn_user_id) in self.factory.gameConnectionList:
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
      

                  
   def getChat(self, chat_id, refresh = False):
      """ This func provides a chat object.  it caches chats to prevent needless reloading """
      
      if refresh or not self.chats.has_key( chat_id ):
         self.chats[ chat_id ] = Chat.objects.get(pk = chat_id)
         
      return self.chats[ chat_id ]
      
      
   def getBoard(self, game_id):
      """ This func provides a board object, loads from cache if necessary """
      
      if not self.boards.has_key( game_id ):
         self.boards[ game_id ] = Board( self.getGame( game_id ) )
         
      return self.boards[ game_id ]

      
   def storeMove(self, game_id, coord, color, playerColor, server_node_id, comments):
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

      # move property
      move_prop = GameProperty(Node = node, Property = color, Value = coord)
      move_prop.save()

      # time property
      prop = GameProperty(Node = node, Property = 'BL', Value = game.TimePeriodRemainB)
      prop.save()

      prop = GameProperty(Node = node, Property = 'WL', Value = game.TimePeriodRemainW)
      prop.save()

      if game.IsOvertimeW:
         prop = GameProperty(Node = node, Property = 'OW', Value = game.OvertimeCountW)
         prop.save()

      if game.IsOvertimeB:
         prop = GameProperty(Node = node, Property = 'OB', Value = game.OvertimeCountB)
         prop.save()
               
      # success!
      return node.id



reactor.listenTCP(PORT, GoServerFactory())
reactor.run()

   

