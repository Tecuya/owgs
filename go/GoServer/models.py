from django.db import models
from django.forms import ModelForm

# so we can have user foreign keys
from django.contrib.auth.models import User

class Game(models.Model):
    import datetime
     
    StartDate = models.DateTimeField('Game Start Date', default=datetime.datetime.now)

    BoardSize = models.CharField(max_length=10, choices=(('19x19','19 x 19'),
                                                         ('13x13','13 x 13'),
                                                         ('9x9','9 x 9')), default='19x19')

    MainTime = models.TimeField('Main Time')
    
    Komi = models.DecimalField('Komi', max_digits=4, decimal_places=1)
    
    PlayersAssigned = models.BooleanField('Players Assigned')

    def __unicode__(self):
        return u'Size: %s Time: %s Komi: %s ' % (self.BoardSize, self.MainTime, self.Komi)

class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ('StartDate', 'PlayersAssigned')



class GameParticipant(models.Model):
    import datetime

    Game = models.ForeignKey(Game)
    Participant = models.ForeignKey(User)
    JoinDate = models.DateTimeField('Participant Join Date', default=datetime.datetime.now)
    LeaveDate = models.DateTimeField('Participant Leave Date', default=datetime.datetime.now)    
    Originator = models.BooleanField('Game Originator')
    Winner = models.BooleanField('Winner')
    Color = models.CharField('Color', max_length=1, choices=(('W', 'White'),('B', 'Black'),('S', 'Spectator')))
    
    def __unicode__(self):
        return 'GameParticipant Object'

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40)
    key_expires = models.DateTimeField()

