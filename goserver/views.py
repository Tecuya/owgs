
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render


def get_user_profile(user):

    try:
        return user.get_profile()
    except ObjectDoesNotExist:
        return None
    except AttributeError:
        return None

def get_user_debug(user):

    profile = get_user_profile(user)

    if profile is None:
        return False

    return profile.DebugMode



def game_list(request):
    from goserver.models import Game, GameParticipant

    gamelist = []
    for game in Game.objects.filter(State__in = ['I','P']).order_by('-State').order_by('-CreateDate'):

        present_parts = len(GameParticipant.objects.filter( Game = game, Present=True ))
                            
        if present_parts == 0: 
            continue

        gamelist.append( {'id': game.id,
                          'params':unicode(game), 
                          'present_participants':unicode(present_parts) } )

    return render(request,
                  'goserver_gamelist.html', 
                  {'GameList': gamelist})

def game_archive(request):
    from goserver.models import Game, GameParticipant

    gamelist = []
    for game in Game.objects.filter(State = 'F').order_by('CreateDate'):
        gamelist.append( {'id': game.id,
                          'params': unicode(game), 
                          'present_participants': unicode(len(GameParticipant.objects.filter( Game = game, Present=True ))) } )

    return render(request,
                  'goserver_gamelist.html', 
                  {'GameList': gamelist})

def game_create(request):
    from goserver.forms import GameForm
    from goserver.models import Game
    
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

    return render(request,
                  'goserver_gamecreate.html',
                  {"GameForm": form})

def game_make_sgf(request, game_id):
    from goserver.models import GameTree
    
    # check if they are logged in and bail if they arent
    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')
    
    sgf = GameTree( game_id ).dumpSGF()
    
    response = HttpResponse(sgf)
    response['Content-Type'] = 'application/x-go-sgf'
    response['Content-Disposition'] = 'attachment; filename=owgs-%d.sgf' % int(game_id)

    return response

def game_edit(request, game_id):
    from goserver.forms import GameForm
    from goserver.models import Game

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

    return render(request,
                  'goserver_gameedit.html',
                  {"game_editForm": form, "Game": game})   

def chat(request, chat_id):

    if request.user.is_anonymous():
        return HttpResponseRedirect('/accounts/login')

    return render(request,
                  'goserver_chat.html', 
                  {"DebugMode": get_user_debug(request.user),
                   "ChatID": chat_id})

def game_view(request, game_id):
    from goserver.models import Game, GameParticipant
    
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
    
    debug_mode = get_user_debug(request.user)
    
    return render(request,
                  'goserver_gameview.html', 
                  {"Game": game,
                   "PreGame": (game.State == 'P'),
                   "Finished": (game.State == 'F'),
                   "DebugMode": debug_mode,
                   "YouAreColor": you_are,
                   "YouAreOwner": you_are_owner,
                   "UserBlack": user_b,
                   "UserWhite": user_w})

def NetClientUnloadWrapper():
    pass

def player_profile(request):

    from goserver.models import UserProfile
    from goserver.forms import UserProfileForm

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

    return render(request,
                  'goserver_playerprofile.html', 
                  { 'UserProfileForm': form })

def Index(request):
    return render(request,
                  'goserver_index.html')

def integrated_interface(request):
    return render(request,
                  'goserver_interface.html', 
                  {'DebugMode': 'true' if get_user_debug(request.user) else 'false',
                   'IsInterface': True})

def json_login(request):
    """ 
    Provide generic login service with JSON response so it can be done
    in the background of the client
    """
    
    from django.contrib.auth import login, authenticate
    
    user = authenticate(username=request.POST['username'], 
                        password=request.POST['password'])


    if user is not None:
        if user.is_active:
            login(request, user)
            # Indicate success page.
            response = '1'
        else:
            # Return a 'disabled account' error message
            response = '-1'
    else:
        # Return an 'invalid login' error message.
        response = '0'
        
    return HttpResponse(
        response,
        mimetype='text/plain')
            
def render_template(request, template):
    return render(request, template)
