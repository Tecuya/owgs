from django.conf.urls.defaults import url, patterns, include

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

                       url(r'^$', 'goserver.views.IntegratedInterface', name='site-homepage'),
                       url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':'/home/sean/code/go/django_code/static'}),
                       url(r'^games/new', 'goserver.views.GameCreate', name='game-create'),
                       url(r'^games/edit/(?P<game_id>\d+)', 'goserver.views.GameEdit', name='game-edit'),
                       url(r'^games/view/(?P<game_id>\d+)', 'goserver.views.GameView', name='game-view'),
                       url(r'^games/sgf/(?P<game_id>\d+)', 'goserver.views.GameMakeSGF', name='game-makesgf'),
                       url(r'^games/active', 'goserver.views.GameList', name='game-list'),
                       url(r'^games/archive', 'goserver.views.GameArchive', name='game-archive'),
                       url(r'^iiface', 'goserver.views.IntegratedInterface', name='iiface'),
                       url(r'^chat/(?P<chat_id>\d+)', 'goserver.views.Chat', name='chat'),

                       (r'^accounts/', include('registration.backends.default.urls')),
                       
                       url(r'^accounts/profile', 'goserver.views.PlayerProfile', name='player-profile'),
                       
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
