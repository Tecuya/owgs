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
        
        # newgame = Game(StartDate = datetime.datetime.now() )
        # form = GameForm(request.POST, instance=newgame)        
        
        form = GameForm(request.POST)
        
        if form.is_valid():
            newgame = form.save()
            
            gp = GameParticipant(Game=newgame, Participant=request.user)
            gp.save()

            return HttpResponseRedirect('/games/edit/%d' % newgame.id)
        
            
    else:
        form = GameForm()

    return render_to_response('GoServer/GameCreate.html', {"GameCreateForm": form}, context_instance=RequestContext(request))   


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


def GameJoin(request, game_id):
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



def PlayerProfile(request):
    return render_to_response('GoServer/PlayerProfile.html', context_instance=RequestContext(request))

def Index(request):
    return render_to_response('GoServer/Index.html', context_instance=RequestContext(request))

