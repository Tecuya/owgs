from django.conf.urls.defaults import url, patterns, include

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    
    url(r'^$', 'goserver.views.integrated_interface', name='site-homepage'),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':'/home/sean/code/go/django_code/static'}),
    url(r'^games/new', 'goserver.views.game_create', name='game-create'),
    url(r'^games/edit/(?P<game_id>\d+)', 'goserver.views.game_edit', name='game-edit'),
    url(r'^games/view/(?P<game_id>\d+)', 'goserver.views.game_view', name='game-view'),
    url(r'^games/sgf/(?P<game_id>\d+)', 'goserver.views.game_make_sgf', name='game-makesgf'),
    url(r'^games/active', 'goserver.views.game_list', name='game-list'),
    url(r'^games/archive', 'goserver.views.game_archive', name='game-archive'),
    url(r'^iiface', 'goserver.views.integrated_interface', name='iiface'),
    url(r'^chat/(?P<chat_id>\d+)', 'goserver.views.chat', name='chat'),
    url(r'^js_login$', 'goserver.views.json_login'),
    url(r'^t/(?P<template>.*)$', 'goserver.views.render_template'),
    
    (r'^accounts/', include('registration.backends.default.urls')),
    
    url(r'^accounts/profile', 'goserver.views.player_profile', name='player-profile'),
        
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    )
