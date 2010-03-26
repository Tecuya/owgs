#!/usr/bin/env python

# for decoding json messages
import json

# twisted
from twisted.internet import protocol, reactor
from twisted.protocols import basic

# django land
from django.core.management import setup_environ
from go import settings

setup_environ(settings)

from go.GoServer.models import Game


def debug(msg):
   print msg
   

class GoServerProtocol(basic.LineReceiver):
   
   def connectionMade(self):
      debug('Connection opened')
      
   def lineReceived(self, data):
      
      print 'something!';

      response = "nil"

      try:
         
         cmd = json.loads(data)

         debug( 'Cmd received: '+str(cmd) )

         # connect command ; index 1 is a sessionid
         if(cmd[0] == 'CONN'):
            response = self.factory.cmdConnect(cmd[1])
         
         elif( self.factory.sessionid == False ):
            response = self.factory.makeErrorForClient('No sessionid; you must CONN first.')

         # subscribe command ; index 1 is a channel name
         elif(cmd[0] == 'JOIN'):
            response = self.factory.cmdJoinChannel(cmd[1]) 
            
         # part command ; index 1 is a channel name
         elif(cmd[0] == 'PART'):
            response = self.factory.cmdPartChannel(cmd[1]) 
            
         # channel say ; index 1 is a channel name  index 2 is the message
         elif(cmd[0] == 'SAY'):
            response = self.factory.cmdSay(cmd[1], cmd[2])

      except Exception, e:
         debug( 'Cmd receive exception: %s' % e )
         response = self.factory.makeErrorForClient(e)

      self.transport.write(response + "\n")


class GoServerFactory(protocol.ServerFactory):
   protocol = GoServerProtocol

   sessionid = False

   def __init__(self):
      pass

   def cmdConnect(self, sessionid):
      self.sessionid = sessionid
      return 'awesome';
      
   def cmdJoinChannel(self, channel):
      
      debug('cmdJoinChannel: %s' % channel)

      debug(channel[:4])

      # first determine if we are talking about a game channel, and if so, handle it properly
      if(channel[:5] == '_game'):
         game_id = channel[5:]
         return str( Game.objects.get(pk = game_id)+"\n" )

   def cmdPartChannel(self, channel):

      if(channel[:4] == '_game'):
         game_id = channel[5:]
         
   def cmdSay(self, channel, message):
      pass

   def makeErrorForClient(self, errormsg):
      return json.dumps(['error',errormsg])





reactor.listenTCP(8002, GoServerFactory())
reactor.run()

