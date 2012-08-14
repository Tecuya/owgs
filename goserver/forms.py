from django.forms import ModelForm
from goserver.models import Game, UserProfile

class GameForm(ModelForm):
    class Meta:
        model = Game
        exclude = ('Owner', 'CreateDate', 'PlayersAssigned', 'ScoreDelta', 'WinType', 'Winner', 'FocusNode', 'Finished', 'State', 'PendingUndoNode',
                   'TimePeriodW', 'TimePeriodB', 'OvertimeCountW', 'OvertimeCountB', 'TimePeriodRemainW', 'TimePeriodRemainB', 'TurnColor', 'LastClock',
                   'IsOvertimeW', 'IsOvertimeB')

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user','activation_key','key_expires')

