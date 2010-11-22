#!/usr/bin/env python

import cjson

import pexpect

from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys
import time

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

def coordSGF2GTP(sgfcoord):
    if sgfcoord == 'tt':
        return 'PASS'

    if sgfcoord[0] < 'i':
        gtpcoord = sgfcoord[0].upper()
    else:
        gtpcoord = chr(ord(sgfcoord[0]) + 1)

    gtpcoord += str( ord(sgfcoord[1]) - 96 )

    return gtpcoord

def coordGTP2SGF(gtpcoord):
    if gtpcoord == 'PASS':
        return 'tt'

    if gtpcoord[0] < 'I':
        sgfcoord = gtpcoord[0].lower()
    else:
        sgfcoord = chr(ord(gtpcoord[0]) - 1).lower()

    sgfcoord += chr( 96 + int(gtpcoord[1:]) )

    return sgfcoord

class OWGSClient(LineReceiver):

    def __init__(self):        
        self.game_id = 0
        self.game_started = False
        self.gtp_proc = False
        
    def newGame(self):
        # Create a new game
        self.sendCommand(["GAME", G_TYPE, G_SIZE, G_KOMI, 0, G_MAINTIME, G_OTTYPE, G_OTPERIOD, G_OTCOUNT])

        
    def connectionMade(self):
        # login / sess
        self.sendCommand(["AUTH", USER, PASS])
        
        # new game!
        self.newGame()

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
                        
            self.gtp_proc = GTP_Process( self.my_color, opponent_color )
            self.gtp_proc.initGame( size = {'19x19': 19, '13x13': 13, '9x9': 9}[ board_size ], 
                                    komi = komi )

            if self.my_color == 'B':
                self.gtp_proc.myMove()
                
        elif data[0] == 'MOVE':
            (command, move_game_id, sgfcoord, parent_node) = data

            if move_game_id != self.game_id:
                print "received a move for a game that we arent tracking.. hrm"
                return

            self.gtp_proc.opponentMove( coordSGF2GTP( sgfcoord ) )

            gtpmove = self.gtp_proc.myMove()

            mycoord = coordGTP2SGF( gtpmove )

            self.sendCommand( ["MOVE", self.game_id, mycoord, self.my_color, parent_node, ""] )


            # if the gtp_proc calculated its final score, then we transmit it to the server
            if self.gtp_proc and self.gtp_proc.final_score:
                scor = self.gtp_proc.final_score
                scor.insert(0, self.game_id)
                scor.insert(0, 'SCOR')
                self.sendCommand( scor )
                self.gtp_proc.final_score = False

        elif data[0] == 'RSLT':

            # kthx
            self.sendCommand(['CMNT', self.game_id, "Thanks for playing %s" % USER])

            # bai
            self.sendCommand(['PART', self.game_id])

            # close child
            self.gtp_proc.closeChild()

            # reset object
            self.__init__()

            # new game!
            self.newGame()


class GTP_Process:

    def __init__(self, my_color, opponent_color):
        self.command_number = 0
        self.my_color = my_color
        self.opponent_color = opponent_color        
        self.move_list = []
        self.final_score = False
        self.gtp_process = pexpect.spawn( GTP_PROG )

    def closeChild(self):
        self.gtp_process.close()

    def initGame(self, size, komi):
        self.boardsize = size
        self.komi = komi
        self.execCommand("boardsize %d" % size)
        self.execCommand("komi %s" % str(komi) )

    def opponentMove(self, coord):        
        self.execCommand("play %s %s" % (self.makeColorName(self.opponent_color), coord) )        
        self.processMove(coord)

    def myMove(self):        
        coord = self.execCommand("genmove " + self.makeColorName(self.my_color))
        self.processMove(coord)
        return coord

    def processMove(self, coord):
        self.move_list.append(coord)
        if ( len(self.move_list) > 2 and 
             self.move_list[-1] == 'PASS' and 
             self.move_list[-2] == 'PASS' ):
    
            territory_w_gtp = self.execCommand("final_status_list white_territory").split()
            territory_b_gtp = self.execCommand("final_status_list black_territory").split() 
        
            dead_list = self.execCommand("final_status_list dead").split()
            
            prisoners_b = 0
            prisoners_w = 0
            for gtpcoord_in in dead_list:
                
                # remove junk
                gtpcoord = gtpcoord_in.strip()

                # added this because i was getting empty entries for some reason.
                if len(gtpcoord) == 0:
                    continue
                
                stonecolor = self.execCommand("color "+gtpcoord)

                print "dead stone ",gtpcoord," is ",stonecolor

                if(stonecolor == "white"):
                    territory_b_gtp.append( gtpcoord )
                    prisoners_w += 1                    
                else:
                    territory_w_gtp.append( gtpcoord )
                    prisoners_b += 1
            
            captures_w = int( self.execCommand("captures white") )
            captures_b = int( self.execCommand("captures black") )
                
            territory_w = [ coordGTP2SGF(x) for x in territory_w_gtp ]
            territory_b = [ coordGTP2SGF(x) for x in territory_b_gtp ]
            
            score_w = prisoners_b + captures_w + len(territory_w) + float(self.komi)
            score_b = prisoners_w + captures_b + len(territory_b) 
            
            self.final_score = [ territory_w, captures_w, prisoners_b, score_w, territory_b, captures_b, prisoners_w, score_b ]
        

    def makeColorName(self, color):
        if color == 'W':
            return 'white'
        else:
            return 'black'

    def execCommand(self, cmd):
        # increment gtp command number
        self.command_number += 1
        
        # write command to child
        writeme = "%d %s" % (self.command_number, cmd)
        print 'WRITE',writeme
        self.gtp_process.sendline(writeme)

        # read response from child
        exp = '=%d (.*)\r\n' % self.command_number
        self.gtp_process.expect(exp)

        print 'READ',self.gtp_process.match.groups()

        # return it
        return self.gtp_process.match.groups()[0].rstrip()
    
                
class OWGSClientFactory(ReconnectingClientFactory):

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed:', reason.getErrorMessage()
        time.sleep(5)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
         
    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        time.sleep(5)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    protocol = OWGSClient

def main():
    factory = OWGSClientFactory()
    reactor.connectTCP(HOST, PORT, factory)
    reactor.run()

if __name__ == '__main__':
    main()
