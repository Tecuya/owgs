from goserver.models import Game, GameNode, GameProperty, Chat, ChatParticipant, GameParticipant, UserProfile
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ['BoardSize']


admin.site.register(Game, GameAdmin)

for m in (GameNode, GameProperty, Chat, ChatParticipant, GameParticipant, UserProfile):
    admin.site.register(m, admin.ModelAdmin)


