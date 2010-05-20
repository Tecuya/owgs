from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

                       url(r'^$', 'go.GoServer.views.Index', name='site-homepage'),
                       url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':'/home/sean/code/go/django_code/static'}),
                       url(r'^games/new', 'go.GoServer.views.GameCreate', name='game-create'),
                       url(r'^games/edit/(?P<game_id>\d+)', 'go.GoServer.views.GameEdit', name='game-edit'),
                       url(r'^games/view/(?P<game_id>\d+)', 'go.GoServer.views.GameView', name='game-view'),
                       url(r'^games/sgf/(?P<game_id>\d+)', 'go.GoServer.views.GameMakeSGF', name='game-makesgf'),
                       url(r'^games/active', 'go.GoServer.views.GameList', name='game-list'),
                       url(r'^games/archive', 'go.GoServer.views.GameArchive', name='game-archive'),
                       url(r'^iiface', 'go.GoServer.views.IntegratedInterface', name='iiface'),
                       url(r'^chat', 'go.GoServer.views.Chat', name='chat'),

                       (r'^accounts/', include('registration.urls')),

                       url(r'^accounts/profile', 'go.GoServer.views.PlayerProfile', name='player-profile'),

                       # (r'^accounts/login
                       # (r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       
                       # Example:
                           # (r'^go/', include('go.foo.urls')),
                       
                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
                       # to INSTALLED_APPS to enable admin documentation:
                           (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       
                       # Uncomment the next line to enable the admin:
                           (r'^admin/', include(admin.site.urls)),
)
