from django.db import models
from django.forms import ModelForm

# so we can have user foreign keys
from django.contrib.auth.models import User

class Game(models.Model):
    import datetime
     
    Owner = models.ForeignKey(User)
    StartDate = models.DateTimeField('Game Start Date', default=datetime.datetime.now)
    BoardSize = models.CharField(max_length=10, choices=(('19x19','19 x 19'),
                                                         ('13x13','13 x 13'),
                                                         ('9x9','9 x 9')), default='19x19')
    MainTime = models.TimeField('Main Time')    
    Komi = models.DecimalField('Komi', max_digits=4, decimal_places=1)
    
    PlayersAssigned = models.BooleanField('Players Assigned')

    Winner = models.CharField('Winning Color', max_length=1, choices=(('W', 'White'),
                                                                      ('B', 'Black'),
                                                                      ('U', 'Unset')), default='U')

    WinType = models.CharField('Win Type', max_length=1, choices=(('S', 'Score'),
                                                                  ('R', 'Resignation'),
                                                                  ('F', 'Forfeit'),
                                                                  ('U', 'Unset')), default='U')
    
    ScoreDelta = models.DecimalField('Score Delta', max_digits=5, decimal_places=1)
    
    def __unicode__(self):
        player_list = []

        for part in GameParticipant.objects.filter(Game = self, State__in = ['W','B','O']):
            player_list.append(part.Participant.username)

        return u'%s | Size: %s | Time: %s | Komi: %s ' % (' vs '.join(player_list), self.BoardSize, self.MainTime, self.Komi)

    
class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ('Owner', 'StartDate', 'PlayersAssigned', 'ScoreDelta', 'WinType', 'Winner')

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

    Game = models.ForeignKey(Game)

    ClientNodeId = models.IntegerField(null=True, blank=True)


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
            nodes = GameNode.objects.filter(Game = self.game_id, ParentNode__isnull = True)
        else:
            nodes = GameNode.objects.filter(Game = self.game_id, ParentNode = parentNode)
            
        childcount = len(nodes.all())

        for node in nodes:

            noderet = []

            propList = []
            for prop in node.gameproperty_set.all():
                propList.append( [prop.Property, prop.Value] )

            # add all this nodes properties to the ret list
            noderet.append(propList)

            # add all the children nodes properties to the ret list
            noderet.extend( self.getNodes( node.id ) )

            if childcount > 1:
                ret.append(noderet)
            else:
                ret = noderet

        return ret

    
    def getFullNodePath(self, parent_node_id, nodeList):
        """ Returns a list of all nodes in order which are ancestors of node named by node_id """
        
        # get the node
        if not parent_node_id:
            node = False
        else:
            node = GameNode.objects.get( pk = parent_node_id )

        # if we didnt get a node, we are done
        if not node or not node.ParentNode:
            
            # reverse the list so it is in first-to-last move order (we built it in reverse)
            nodeList.reverse()
            return nodeList

        else:         
            
            # load the nodes properties
            properties = GameProperty.objects.filter( Node = node, Property__in = ['W', 'B', 'AB', 'AW']).all()

            # add it to our list
            nodeList.append( [ node, properties ] )
            
            # get the parent node
            return self.getFullNodePath( node.ParentNode.id, nodeList )
                
class Board:
    """ This class represents a go board. It is modelled after eidogo's game model as it closely integrates with it.  It is used to perform move validation / rule checking on client-generated moves. """
    
    def __init__(self, game):

        self.WHITE = 1
        self.EMPTY = 0
        self.BLACK = -1

        self.game = game
        
        self.board = []

        self.size = int(self.game.BoardSize.split('x')[0])

        # produce a blank board
        for i in range(0, (self.size ** 2)):
            self.board.append( self.EMPTY )
            
        
    def makeMove( self, parent_node, coord, color ):

        # bring board in sync with parent_node
        self.syncBoardToNode( parent_node.id )

        # perform rule check on coord & color
        return self.ruleCheck( coord, color )

    def sgfPointToXY( self, sgfPoint ):        
        x = ord(sgfPoint[0]) - 97
        y = ord(sgfPoint[1]) - 97
        return [x,y]
        
    def syncBoardToNode( self, parent_node ):        
        # TODO implement some manner of caching here so its not necessary to always
        # do a complete lookup of the game history!
        nodes = GameTree( self.game.id ).getFullNodePath( parent_node, [] )

        propColorMap = {'W': self.WHITE,
                        'AW': self.WHITE,
                        'B': self.BLACK,
                        'AB': self.BLACK}
        
        for (node,properties) in nodes:
            for prop in properties:
                color = propColorMap[ prop.Property ]
                (x,y) = self.sgfPointToXY( prop.Value )
                self.setPoint(x, y, color)
                self.lastColor = color
                
    def ruleCheck( self, coord, color):

        # out of order turn
        if(color == self.lastColor):
            return [False, "Color out of order"]

        # get the x,y
        (x,y) = self.sgfPointToXY( coord )

        # out of bounds coordinates
        if x<0 or x>self.size-1 or y<0 or y>self.size-1:
            return [False, "Invalid move: out of bounds"]

        # playing on already-occupied space
        if(self.getPoint(x,y) != self.EMPTY):
            return [False, "Invalid move: occupied space"]
        
        return [True, ""]

    def getPoint( self, x, y ):
        return self.board[ y * self.size + x ]

    def setPoint( self, x, y, color ):
        self.board[ y * self.size + x ] = color
        
