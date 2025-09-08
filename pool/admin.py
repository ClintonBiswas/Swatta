from django.contrib import admin
from .models import Poll, PollOption, PollView, Vote

# Register your models here.
admin.site.register(PollOption)
admin.site.register(PollView)
admin.site.register(Vote)
@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'poll_type', 'is_active', 'created_at')
    search_fields = ('question',)
    prepopulated_fields = {'slug': ('question',)}
    readonly_fields = ('created_at',)
