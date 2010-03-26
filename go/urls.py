from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

                       url(r'^$', 'go.GoServer.views.Index', name='site-homepage'),
                       url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':'/home/sean/code/go/django_code/static'}),
                       url(r'^games/new', 'go.GoServer.views.GameCreate', name='game-create'),
                       url(r'^games/edit/(?P<game_id>\d+)', 'go.GoServer.views.GameEdit', name='game-edit'),
                       url(r'^games/join/(?P<game_id>\d+)', 'go.GoServer.views.GameJoin', name='game-join'),
                       url(r'^games', 'go.GoServer.views.GameList', name='game-list'),
                       
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
