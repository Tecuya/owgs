
# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

def GameList(request):
    from GoServer.models import GameForm, Game, GameParticipant

    return render_to_response('GoServer/GameList.html', 
                              {'GameList': Game.objects.order_by('StartDate')},
                              context_instance=RequestContext(request))

def GameCreate(request):
    from GoServer.models import GameForm, Game, GameParticipant
    
    # check if they are logged in and bail if they arent
    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    if request.method == 'POST':

        game = Game( Owner = request.user)
        form = GameForm(request.POST, instance=game)
        
        if form.is_valid():
            newgame = form.save()
            
            # gp = GameParticipant(Game=newgame, Participant=request.user, State='O')
            # gp.save()

            return HttpResponseRedirect('/games/view/%d' % newgame.id)
    else:
        form = GameForm()

    return render_to_response('GoServer/GameCreate.html', {"GameForm": form}, context_instance=RequestContext(request))   


def GameEdit(request, game_id):
    from GoServer.models import GameForm, Game, GameParticipant

    # check if they are logged in and bail if they arent
    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    # TODO *instead* of the check above, verify that the game belongs to the user we are logged in as
    # before allowing them to edit it!

    # load the existing game object
    game = Game.objects.get(pk = game_id)
    
    # update the game object if requested
    if request.method == 'POST':
        form = GameForm(request.POST, instance=game)                    
        if form.is_valid():
            game = form.save()
    
    form = GameForm(instance=game)

    return render_to_response('GoServer/GameEdit.html', {"GameEditForm": form, "Game": game}, context_instance=RequestContext(request))   


def GameView(request, game_id):
    from GoServer.models import Game, GameParticipant
    from django.contrib.auth.models import User

    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    game = Game.objects.get(pk = game_id)
    
    # determine if we are the owner of this game or not
    you_are_owner = (game.Owner == request.user)

    you_are = 'U'

    # TODO clean this up!  use more advanced model queries

    # load white/black participants, if there are any
    if GameParticipant.objects.filter(Game = game, State='W').count() == 1:
        gp_w = GameParticipant.objects.filter(Game = game, State='W')[0]
        user_w = User.objects.get(pk = gp_w.Participant.id)
        if gp_w.Participant == request.user:
            you_are = 'W'
    else:
        user_w = {}

    if GameParticipant.objects.filter(Game = game, State='B').count() == 1:
        gp_b = GameParticipant.objects.filter(Game = game, State='B')[0]
        user_b = User.objects.get(pk = gp_b.Participant.id)
        if gp_b.Participant == request.user:
            you_are = 'B'
    else:
        user_b = {}
        
    return render_to_response('GoServer/GameView.html', 
                              {"Game": game,
                               "YouAreColor": you_are,
                               "YouAreOwner": you_are_owner,
                               "UserBlack": user_b,
                               "UserWhite": user_w},
                              context_instance=RequestContext(request))   



def NetClientUnloadWrapper():
    pass

def PlayerProfile(request):
    return render_to_response('GoServer/PlayerProfile.html', context_instance=RequestContext(request))

def Index(request):
    return render_to_response('GoServer/Index.html', context_instance=RequestContext(request))

