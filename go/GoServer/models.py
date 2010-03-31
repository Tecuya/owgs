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

    def __unicode__(self):
        return u'Size: %s | Time: %s | Komi: %s ' % (self.BoardSize, self.MainTime, self.Komi)

    
class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ('Owner', 'StartDate', 'PlayersAssigned')

class GameNode(models.Model):
    """ 
    This model represents an SGF node.  
    Nodes exist in a parent/child tree.
    When ParentNode is unset, this is the root node of the collection.
    """
    Game = models.ForeignKey(Game)

    # TODO will django allow me to have this unset (for root nodes)
    ParentNode = models.ForeignKey('self')

class GameProperty(models.Model):
    """
    This model represents an SGF property.
    Multiple properties can exist under any single node.
    """
    Node = models.ForeignKey(GameNode)
    Property = models.CharField('SGF Property Name')
    Value = models.TextField('SGF Property Value')

class GameParticipant(models.Model):
    import datetime

    Game = models.ForeignKey(Game)
    Participant = models.ForeignKey(User)

    JoinDate = models.DateTimeField('Participant Join Date', default=datetime.datetime.now)
    LeaveDate = models.DateTimeField('Participant Leave Date', default=datetime.datetime.now)    

    Originator = models.BooleanField('Game Originator')
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

