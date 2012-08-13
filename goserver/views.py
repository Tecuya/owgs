
# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

def GameList(request):
    from goserver.models import Game, GameParticipant

    gamelist = []
    for game in Game.objects.filter(State__in = ['I','P']).order_by('-State').order_by('-CreateDate'):

        present_parts = len(GameParticipant.objects.filter( Game = game, Present=True ))
                            
        if present_parts == 0: 
            continue

        gamelist.append( {'id': game.id,
                          'params':unicode(game), 
                          'present_participants':unicode(present_parts) } )


    return render_to_response('goserver_gamelist.html', 
                              {'GameList': gamelist},
                              context_instance=RequestContext(request))

def GameArchive(request):
    from goserver.models import GameForm, Game, GameParticipant

    gamelist = []
    for game in Game.objects.filter(State = 'F').order_by('CreateDate'):
        gamelist.append( {'id': game.id,
                          'params': unicode(game), 
                          'present_participants': unicode(len(GameParticipant.objects.filter( Game = game, Present=True ))) } )

    return render_to_response('goserver_gamelist.html', 
                              {'GameList': gamelist},
                              context_instance=RequestContext(request))


def GameCreate(request):
    from goserver.models import GameForm, Game, GameParticipant
    
    # check if they are logged in and bail if they arent
    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    if request.method == 'POST':

        game = Game( Owner = request.user )
        form = GameForm(request.POST, instance=game)
        
        if form.is_valid():
            newgame = form.save()            
            return HttpResponseRedirect('/games/view/%d' % newgame.id)
    else:
        form = GameForm()

    return render_to_response('goserver_gamecreate.html', {"GameForm": form}, context_instance=RequestContext(request))   


def GameMakeSGF(request, game_id):
    from goserver.models import GameTree
    
    # check if they are logged in and bail if they arent
    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')
    
    sgf = GameTree( game_id ).dumpSGF()
    
    response = HttpResponse(sgf)
    response['Content-Type'] = 'application/x-go-sgf'
    response['Content-Disposition'] = 'attachment; filename=owgs-%d.sgf' % int(game_id)

    return response


def GameEdit(request, game_id):
    from goserver.models import GameForm, Game, GameParticipant

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

    return render_to_response('goserver_gameedit.html', {"GameEditForm": form, "Game": game}, context_instance=RequestContext(request))   


def Chat(request, chat_id):

    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    return render_to_response('goserver_chat.html', 
                              {"DebugMode": request.user.get_profile().DebugMode,
                               "ChatID": chat_id},                              
                              context_instance=RequestContext(request))


def GameView(request, game_id):
    from goserver.models import Game, GameParticipant, GameTree, UserProfile
    from django.contrib.auth.models import User
    
    game = Game.objects.get(pk = game_id)

    # spectator unless you end up being a player when loading participant
    you_are = 'S'

    you_are_owner = (game.Owner == request.user)

    # load white/black participants, if there are any
    if GameParticipant.objects.filter(Game = game, State='W').count() == 1:
        gp_w = GameParticipant.objects.filter(Game = game, State='W')[0]
        user_w = gp_w.Participant
    else:
        user_w = {}

    if GameParticipant.objects.filter(Game = game, State='B').count() == 1:
        gp_b = GameParticipant.objects.filter(Game = game, State='B')[0]
        user_b = gp_b.Participant
    else:
        user_b = {}

    if user_w == request.user:
        you_are = 'W'
    elif user_b == request.user:
        you_are = 'B'

    # sgf = GameTree( game.id ).dumpSGF().replace("\n","\\n")

    if request.user.is_anonymous():
        # defaulting to standard player mode in absence of user profile
        debug_mode = 0
    else:
        profile = request.user.get_profile()
        debug_mode = profile.DebugMode
    
    return render_to_response('goserver_gameview.html', 
                              {"Game": game,
                               "PreGame": (game.State == 'P'),
                               "Finished": (game.State == 'F'),
                               "DebugMode": debug_mode,
                               "YouAreColor": you_are,
                               "YouAreOwner": you_are_owner,
                               "UserBlack": user_b,
                               "UserWhite": user_w},
                              context_instance=RequestContext(request))   



def NetClientUnloadWrapper():
    pass

def PlayerProfile(request):

    from goserver.models import UserProfile, UserProfileForm

    try:
        prof = UserProfile.objects.get(user = request.user.id)
    except:
        prof = UserProfile( user = request.user )
        prof.save()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance = prof)
        
        if form.is_valid():
            form.save()
            
            return HttpResponseRedirect('/accounts/profile')
    else:
        form = UserProfileForm(instance = prof)

    return render_to_response('goserver_playerprofile.html', 
                              { 'UserProfileForm': form },
                              context_instance=RequestContext(request))

def Index(request):
    return render_to_response('goserver_index.html', context_instance=RequestContext(request))


def IntegratedInterface(request):
    if request.user.is_anonymous():
        DebugMode = 'false'
    elif request.user.get_profile().DebugMode:
        DebugMode = 'true'
    else:
        DebugMode = 'false'

    return render_to_response('goserver_interface.html', 
                              {'DebugMode': DebugMode,
                               'IsInterface': True},                              
                              context_instance=RequestContext(request))




