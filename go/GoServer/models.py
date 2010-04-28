from django.db import models
from django.forms import ModelForm

# so we can have user foreign keys
from django.contrib.auth.models import User

class GameNode(models.Model):
    """ 
    This model represents an SGF node.  
    Nodes exist in a parent/child tree.
    When ParentNode is unset, this is the root node of the collection.
    """

    # muhuk #django/FreeNode sez:
    #  <muhuk> if I had a hierarcy, I wouldn't want blank=True, null=True on my FK. So I'd use a hack for the exception; the root node.
    # so consider that!  for now i'm being lazy and making this blank/null
    ParentNode = models.ForeignKey('self', null=True, blank=True)

    Game = models.ForeignKey('Game')


class GameProperty(models.Model):
    """
    This model represents an SGF property.
    Multiple properties can exist under any single node.
    """
    Node = models.ForeignKey(GameNode)
    Property = models.CharField('SGF Property Name', max_length=10)
    Value = models.TextField('SGF Property Value')

    def __unicode__(self):
        return '%s %s' % (self.Property, self.Value)


class Chat(models.Model):
    
    Name = models.CharField('Channel Name', max_length=255)

class Game(models.Model):
    import datetime
    
    # the owner of the game
    Owner = models.ForeignKey(User)

    # Date at which this game record was created
    CreateDate = models.DateTimeField('Game Start Date', default=datetime.datetime.now)


    ########### Player Preferences ###########
    # type
    Type = models.CharField('Game Type', max_length=1, choices=(('F', 'Free'),
                                                                ('R', 'Ranked'),
                                                                ('T', 'Teaching')), default='F')
    
    # board size
    BoardSize = models.CharField(max_length=10, choices=(('19x19','19 x 19'),
                                                         ('13x13','13 x 13'),
                                                         ('9x9','9 x 9')), default='19x19')

    # Komi for this game
    Komi = models.DecimalField('Komi', max_digits=4, decimal_places=1)

    # Indicates whether or not W / B players are determined
    AllowUndo = models.BooleanField('Allow Undo')
    

    ########### Time #############
    # Main time period length
    MainTime = models.IntegerField('Main Time')    
    
    # overtime type
    OvertimeType = models.CharField('Overtime Type', max_length=1, choices=(('N', 'No Overtime'),
                                                                            ('B', 'Byo-Yomi'),
                                                                            ('C', 'Canadian')), default='N')
    
    # the length of an overtime period
    OvertimePeriod = models.IntegerField('Overtime Period Length')
    # in N, meaningless, in B, the number of byo-yomi periods. in C, the number of stones 
    OvertimeCount = models.IntegerField('Overtime Count')

    # determine whether or not player is in overtime
    IsOvertimeW = models.BooleanField('W Is Overtime')
    IsOvertimeB = models.BooleanField('B Is Overtime')

    ## Track the overtime period count for white/black
    # in N, meaningless
    # in B, the number of byo-yomi periods remaining
    # in C, the number of stones remaining to be played before the time period renews
    OvertimeCountW = models.IntegerField('W Overtime Count', default=0)
    OvertimeCountB = models.IntegerField('B Overtime Count', default=0)

    # track the time remaining in the current time period for white & black
    TimePeriodRemainW = models.DecimalField('W Period Time Remaining', max_digits=15, decimal_places=3, default='0.0')
    TimePeriodRemainB = models.DecimalField('B Period Time Remaining', max_digits=15, decimal_places=3, default='0.0')
    
    # whose turn is it
    TurnColor = models.CharField('Overtime Type', max_length=1, choices=(('W', 'White'),
                                                                         ('B', 'Black')), default='B')

    # exactly when did the turn start
    LastClock = models.DecimalField('Most Recent Clock Update', max_digits=15, decimal_places=3, default='0.0')


    ############## State Tracking ###############
    # indicates the game state
    State = models.CharField('Game State', max_length=1, choices=(('P', 'Pre-Game'),
                                                                  ('I', 'In Progress'),
                                                                  ('F', 'Finished')), default='P')

    # Winning color
    Winner = models.CharField('Winning Color', max_length=1, choices=(('W', 'White'),
                                                                      ('B', 'Black'),
                                                                      ('U', 'Unset')), default='U')

    # Type of win
    WinType = models.CharField('Win Type', max_length=1, choices=(('S', 'Score'),
                                                                  ('R', 'Resignation'),
                                                                  ('F', 'Forfeit'),
                                                                  ('T', 'Time'),
                                                                  ('U', 'Unset')), default='U')
    
    # the difference between W & B's score
    ScoreDelta = models.DecimalField('Score Delta', max_digits=5, decimal_places=1)
    
    # stores the node which is currently focused in this game
    FocusNode = models.IntegerField('Focus Node Id', blank=True, null=True)

    # keeps track of when undos are pending
    PendingUndoNode = models.IntegerField('Pending Undo Node Id', blank=True, null=True)

    
    def __unicode__(self):
        player_list = []

        for part in GameParticipant.objects.filter(Game = self, State__in = ['W','B','O']):
            player_list.append(part.Participant.username)

        return u'State: %s | Type: %s | Size: %s | Time: %s | Komi: %s | Players: %s' % (self.State, self.Type, self.BoardSize, self.MainTime, self.Komi, ' vs '.join(player_list))

    
class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ('Owner', 'CreateDate', 'PlayersAssigned', 'ScoreDelta', 'WinType', 'Winner', 'FocusNode', 'Finished', 'State', 'PendingUndoNode',
                   'TimePeriodW', 'TimePeriodB', 'OvertimeCountW', 'OvertimeCountB', 'TimePeriodRemainW', 'TimePeriodRemainB', 'TurnColor', 'LastClock',
                   'IsOvertimeW', 'IsOvertimeB')

        
class GameParticipant(models.Model):
    import datetime

    Game = models.ForeignKey(Game)
    Participant = models.ForeignKey(User)

    JoinDate = models.DateTimeField('Participant Join Date', default=datetime.datetime.now)

    LeaveDate = models.DateTimeField('Participant Leave Date', default=datetime.datetime.now)    

    Originator = models.BooleanField('Game Originator')

    Present = models.BooleanField('Present')

    Winner = models.BooleanField('Winner')

    State = models.CharField('State', max_length=1, choices=(('W', 'White'),
                                                             ('B', 'Black'),
                                                             ('O', 'Owner'),
                                                             ('S', 'Spectator'),
                                                             ('U', 'Unset')), default='U')
    
    # indicates whether this user is allowed to edit the game board
    Editor = models.BooleanField('Editor', default=False)

    def __unicode__(self):
        return '%s (%s)' % (self.Participant.username, self.State)


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40)
    key_expires = models.DateTimeField()



class GameTree:
    """ This class provides all our SGF and game tree traversal functionality """

    def __init__(self, game_id):
        self.game_id = game_id

    def dumpSGF(self):

        nodeList = self.getNodes()

        def makeCollection(items):
            # TODO this is ugly as sin, should be cleaned
            outSGF = u''

            itemsIsNode = False

            for item in items:                
                # if this is a property
                if len(item) == 2 and type(item[0]) == unicode:
                    itemsIsNode = True
                    # then we should just be rendering this as a property list.. bail!
                    break
                else:
                    # if it is apparent that the item is not just a prop list, then we () it
                    if len(item) and len(item[0]) and type(item[0][0]) != unicode:
                        outSGF += u'(%s)' % makeCollection(item)
                    else:
                        outSGF += makeCollection(item)
            
            if itemsIsNode:
                outSGF += ';'
                for item in items:
                    outSGF += u'%s[%s]' % (item[0], item[1])
            
            return outSGF
                    
        ret = u'(%s)' % makeCollection(nodeList)
        return ret

        
    def getNodes(self, parentNode = 0):

        # our return value list
        ret = []

        # define a func to get node list for this parentnode; this way we can use is_null or node num
        if parentNode == 0:
            nodes = GameNode.objects.filter(Game = self.game_id, ParentNode__isnull = True).order_by('id')
        else:
            nodes = GameNode.objects.filter(Game = self.game_id, ParentNode = parentNode).order_by('id')
            
        childcount = len(nodes.all())

        for node in nodes:

            noderet = []

            propList = []
            hasSN = False
            for prop in node.gameproperty_set.all():

                if prop.Property == "SN":
                    hasSN = True

                propList.append( [prop.Property, prop.Value] )


            # provided its not already there, artificially add the SN property for eidogo / server node syncing
            if not hasSN:
                propList.append( ["SN", node.id] )

            # add all this nodes properties to the ret list
            noderet.append(propList)

            # add all the children nodes properties to the ret list
            noderet.extend( self.getNodes( node.id ) )

            if childcount > 1:
                ret.append(noderet)
            else:
                ret = noderet

        return ret

    
    def getFullNodePath(self, findNode):
        """ Returns a list of all nodes in order which are ancestors of findnode """

        nodeList = []

        # get the node props, add it to our list, then move node's parents, continue until we hit the end
        while findNode:

            # load the nodes properties
            properties = GameProperty.objects.filter( Node = findNode, Property__in = ['W', 'B', 'AB', 'AW']).all()

            # append this node to the list
            nodeList.append( [ findNode, properties ] )
            
            findNode = findNode.ParentNode
            
        # reverse the list so its in order of moves played
        nodeList.reverse()
        return nodeList

                
class Board:
    """ This class represents a go board. It is modelled after eidogo's game model as it closely integrates with it.  It is used to perform move validation / rule checking on client-generated moves. """
    
    def __init__(self, game):

        self.WHITE = 1
        self.EMPTY = 0
        self.BLACK = -1

        self.colorMap = {'W': self.WHITE,
                        'AW': self.WHITE,
                        'B': self.BLACK,
                        'AB': self.BLACK}

        self.game = game
        
        # initially we say white went last; so black can go next
        self.lastColor = self.WHITE

        self.board = []

        self.koImmune = False

        self.size = int(self.game.BoardSize.split('x')[0])

        # produce a blank board
        for i in range(0, (self.size ** 2)):
            self.board.append( self.EMPTY )
            
        
    def makeMove( self, parent_node, coord, color ):

        # bring board in sync with parent_node
        if not self.syncBoardToNode( parent_node ):
            return [False, "Failed syncing board to node %d" % parent_node.id]

        # perform rule check on coord & color
        return self.ruleCheck( coord, self.colorMap[ color ] )

    def sgfPointToXY( self, sgfPoint ):        
        x = ord(sgfPoint[0]) - 97
        y = ord(sgfPoint[1]) - 97
        return [x,y]
        
    def syncBoardToNode( self, syncnode ):        
        
        # TODO implement some manner of caching here so its not necessary to always
        # do a complete lookup of the game history!  This is going to get slllooow..

        nodes = GameTree( self.game.id ).getFullNodePath( syncnode )

        if len(nodes) == 0:
            return False
                
        self.clearBoard()

        for (node,properties) in nodes:
            for prop in properties:
                
                color = self.colorMap[ prop.Property ]
                self.lastColor = color

                if prop.Value == "tt":
                    continue
                else:
                    (x,y) = self.sgfPointToXY( prop.Value )
                    self.setPoint(x, y, color)
                    
                    caps = self.findMoveCaptures( x, y, color )
                    for (rx, ry) in caps:
                        self.setPoint( rx, ry, self.EMPTY)

                    # if we only captured one stone, this move's is marked koImmune
                    if len(caps) == 1:
                        self.koImmune = [x, y]

        return True

    
    def findMoveCaptures(self, x, y, color):
        """ This method determines if a move makes captures and if it does it returns the list of captured points """

        # see if we captured something
        checkPoints = []
        if x > 0: 
            checkPoints.append( [x-1, y] )
        if y > 0:
            checkPoints.append( [x, y-1] )
        if x < self.size - 1:
            checkPoints.append( [x+1, y] )
        if y < self.size - 1:
            checkPoints.append( [x, y+1] )

        # if we did capture stuff we'll keep a list here
        removeStones = []

        for (cx, cy) in checkPoints:

            # dont check empty space
            if self.getPoint( cx, cy ) == self.EMPTY:
                continue

            # find the group
            groupPoints = self.findGroupPoints( cx, cy )

            # see if we killed its liberties
            groupLibs = 0
            for (gx, gy) in groupPoints:
                groupLibs += len(self.getStoneLiberties( gx, gy ))

            # remove the group if it was captured
            if groupLibs == 0:
                for (gx, gy) in groupPoints:
                    removeStones.append( [gx, gy] )

        return removeStones

    def ruleCheck( self, coord, color):
        
        # it's just a pass? that's always allowed
        if coord == "tt":
            return [True, ""]

        if(color == self.lastColor):
            return [False, "Color out of order %d == %d" % (color, self.lastColor)]

        # get the x,y
        (x,y) = self.sgfPointToXY( coord )

        # out of bounds coordinates
        if x<0 or x>self.size-1 or y<0 or y>self.size-1:
            return [False, "Invalid move: out of bounds (%d, %d)" % (x, y)]
        
        # playing on already-occupied space
        if(self.getPoint(x,y) != self.EMPTY):
            return [False, "Invalid move: occupied space (%d, %d, %d)" % (x, y, self.getPoint(x,y))]

        ##########
        # suicide check        
        self.setPoint(x, y, color) # temporarily set the point so we can check it

        # find the new group
        groupPoints = self.findGroupPoints( x, y )

        # count the groups liberties
        groupLibs = 0
        for (gx, gy) in groupPoints:
            groupLibs += len(self.getStoneLiberties( gx, gy ))

        # this will be reused in the ko check
        thisMoveCaptures = self.findMoveCaptures( x, y, color)

        # if it appears the placed stone removes all this groups liberties, see if we are capturing
        if groupLibs == 0 and len(thisMoveCaptures) == 0:
            self.setPoint(x, y, self.EMPTY) # restore the point
            return [False, "Invalid move: move is suicide (%d, %d, %d)" % (x, y, color)]
        
        ############## ko check
        if (self.koImmune and 
            len(self.findGroupPoints( self.koImmune[0], self.koImmune[1])) == 1 and
            len(self.getStoneLiberties( self.koImmune[0], self.koImmune[1])) == 0):
            
            self.setPoint(x, y, self.EMPTY) # restore the point
            return [False, "Invalid move: move violates the ko rule"]
                
        # restore the point
        self.setPoint(x, y, self.EMPTY) 
        return [True, ""]

    def getPoint( self, x, y ):
        return self.board[ y * self.size + x ]

    def setPoint( self, x, y, color ):
        self.board[ y * self.size + x ] = color

    def clearBoard( self ):
        for i in range(0, len(self.board)):
            self.board[i] = self.EMPTY
            
    def findGroupPoints( self, x, y, groupPoints = False ):
        
        color = self.getPoint( x, y )
        
        if not groupPoints:
            groupPoints = []
            
        groupPoints.append( [x,y] )
        
        checkPoints = []
        if x > 0: 
            checkPoints.append( [x-1, y] )
        if y > 0:
            checkPoints.append( [x, y-1] )
        if x < self.size - 1:
            checkPoints.append( [x+1, y] )
        if y < self.size - 1:
            checkPoints.append( [x, y+1] )

        for (x,y) in checkPoints:
            
            # if this points already been checked, skip it
            ptInGp = False

            for (gx, gy) in groupPoints:
                if x == gx and y == gy:
                    ptInGp = True
                    break
            
            if not ptInGp and color == self.getPoint( x, y ):
                groupPoints.extend( self.findGroupPoints( x, y, groupPoints ) )
        
        return groupPoints
    
    def getStoneLiberties(self, x, y):
        
        checkPoints = []
        if x > 0: 
            checkPoints.append( [x-1, y] )
        if y > 0:
            checkPoints.append( [x, y-1] )
        if x < self.size - 1:
            checkPoints.append( [x+1, y] )
        if y < self.size - 1:
            checkPoints.append( [x, y+1] )

        returnList = []

        for (cx, cy) in checkPoints:
            if self.getPoint( cx, cy ) == self.EMPTY:
                returnList.append( [cx, cy] )
        
        return returnList


class GameCursor:
    """ This class represents a cursor for traversing sgf nodes. It is modelled after eidogo's game model as it closely integrates with it. """
    
    def __init__(self, node):
        self.node = node

    def hasNext(self):
        pass
