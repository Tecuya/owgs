#!/usr/bin/env python

import cjson

from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import sys

USER = 'gnugo'
PASS = '123'
HOST = 'localhost'
PORT = 8002

class OWGSClient(LineReceiver):
    def connectionMade(self):
        # login / sess
        self.sendLine(cjson.encode(["AUTH", USER, PASS]))
        
        # Create a new game

        # accept any offers

        # play the game

        # score?

        # loop

        # self.sendLine("Hello, world!")

    def lineReceived(self, line):
        print "receive:", line


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
