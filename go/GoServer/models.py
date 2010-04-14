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
    Game = models.ForeignKey(Game)

    # muhuk #django/FreeNode sez:
    #  <muhuk> if I had a hierarcy, I wouldn't want blank=True, null=True on my FK. So I'd use a hack for the exception; the root node.
    # so consider that!  for now i'm being lazy and making this blank/null
    ParentNode = models.ForeignKey('self', null=True, blank=True)


class GameProperty(models.Model):
    """
    This model represents an SGF property.
    Multiple properties can exist under any single node.
    """
    Node = models.ForeignKey(GameNode)
    Property = models.CharField('SGF Property Name', max_length=10)
    Value = models.TextField('SGF Property Value')

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



# find all nodes with current parent, and all that node's peers
# if a node has children, recurse for given parent
# add each node to a list, and return to caller


class SGF:
    """ This class provides all our SGF functionality """

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

                
            

            
        

    
