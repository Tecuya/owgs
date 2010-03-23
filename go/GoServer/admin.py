from go.GoServer.models import Game
from django.contrib import admin

class GameAdmin(admin.ModelAdmin):
    fields = ['StartDate','BoardSize']
    list_filter = ['StartDate']


admin.site.register(Game, GameAdmin)

# admin.site.register(Game)

