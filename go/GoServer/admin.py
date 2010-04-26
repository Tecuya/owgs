from go.GoServer.models import Game
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ['BoardSize']


admin.site.register(Game, GameAdmin)


