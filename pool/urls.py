from django.urls import path
from . import views
urlpatterns = [
    path('polls/', views.poll_list, name='poll_list'),
    path('ajax/vote/', views.ajax_vote, name='ajax_vote'),
]