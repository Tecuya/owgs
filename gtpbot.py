#!/usr/bin/env python

import cjson

import pexpect

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys

# this is the prog & args to run to get our subprocess
GTP_PROG = '/usr/games/gnugo --mode gtp'

# owgs connection parameters
USER = 'gnugo'
PASS = '123'
HOST = 'localhost'
PORT = 8002

# initial game parameters
G_TYPE = 'F'
G_SIZE = '19x19'
G_KOMI = '6.5'
G_MAINTIME = 900
G_OTTYPE = 'B'
G_OTPERIOD = 30
G_OTCOUNT = 5

class OWGSClient(LineReceiver):

    def __init__(self):        
        self.game_id = 0
        self.game_started = False
        self.gtp_proc = False
        
    def connectionMade(self):
        # login / sess
        self.sendCommand(["AUTH", USER, PASS])
        
        # Create a new game
        self.sendCommand(["GAME", G_TYPE, G_SIZE, G_KOMI, G_MAINTIME, G_OTTYPE, G_OTPERIOD, G_OTCOUNT])

        # from here on everything is event-driven

    def sendCommand(self, cmd):
        print ">", cmd
        LineReceiver.sendLine( self, cjson.encode(cmd) )
        
    def lineReceived(self, line):
        print "<", line
        data = cjson.decode(line)
        
        if data[0] == 'GAME':
            self.game_id = data[1]

            self.sendCommand( ["JOIN", self.game_id] )

        elif data[0] == 'OFFR':
            # TODO have a set of parameters which this bot will accept?
            (command, game_id, board_size, main_time, komi, opponent_color, user_id, username) = data
            
            if opponent_color == 'W':
                self.my_color = 'B'
            else:
                self.my_color = 'W'

            if game_id != self.game_id:
                print "received an offer for a game that we arent tracking.. hrm"
                return

            self.sendCommand( ["BEGN", game_id, user_id] )
            
            self.game_started = True
            
            size_dict = {'19x19': 19, '13x13': 13, '9x9': 9}
            
            self.gtp_proc = GTP_Process( self.my_color, opponent_color )
            self.gtp_proc.createBoard( size_dict[ board_size ] )
                
            if self.my_color == 'B':
                self.gtp_proc.myMove()
                
        elif data[0] == 'MOVE':
            (command, move_game_id, sgfcoord, parent_node) = data

            if move_game_id != self.game_id:
                print "received a move for a game that we arent tracking.. hrm"
                return

            self.gtp_proc.opponentMove( self.coordSGF2GTP( sgfcoord ) )

            gtpmove = self.gtp_proc.myMove()

            mycoord = self.coordGTP2SGF( gtpmove )

            self.sendCommand( ["MOVE", self.game_id, mycoord, self.my_color, parent_node, ""] )
            
    def coordSGF2GTP(self, sgfcoord):
        if sgfcoord == 'tt':
            return 'PASS'

        if sgfcoord[0] < 'i':
            gtpcoord = sgfcoord[0].upper()
        else:
            gtpcoord = chr(ord(sgfcoord[0]) + 1)

        gtpcoord += str( ord(sgfcoord[1]) - 96 )
        
        return gtpcoord

    def coordGTP2SGF(self, gtpcoord):
        if gtpcoord == 'PASS':
            return 'tt'

        if gtpcoord[0] < 'I':
            sgfcoord = gtpcoord[0].lower()
        else:
            sgfcoord = chr(ord(gtpcoord[0]) - 1).lower()
        
        sgfcoord += chr( 96 + int(gtpcoord[1:]) )

        return sgfcoord

class GTP_Process:

    def __init__(self, my_color, opponent_color):
        self.command_number = 0

        self.my_color = my_color
        self.opponent_color = opponent_color

        self.gtp_process = pexpect.spawn( GTP_PROG )


    def createBoard(self, size):
        self.writeCommand("boardsize %d" % size)

    def opponentMove(self, coord):        
        self.writeCommand("play %s %s" % (self.makeColorName(self.opponent_color), coord) )        
        
    def myMove(self):        
        self.writeCommand("genmove " + self.makeColorName(self.my_color))
        exp = '=%d (.*)' % self.command_number
        self.gtp_process.expect(exp)
        return self.gtp_process.match.groups()[0].rstrip()

    def makeColorName(self, color):
        if color == 'W':
            return 'white'
        else:
            return 'black'

    def writeCommand(self, cmd):
        self.command_number += 1
        writeme = "%d %s" % (self.command_number, cmd)
        self.gtp_process.sendline(writeme)

                
class OWGSClientFactory(ClientFactory):
    protocol = OWGSClient

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()

def main():
    factory = OWGSClientFactory()
    reactor.connectTCP(HOST, PORT, factory)
    reactor.run()

if __name__ == '__main__':
    main()
