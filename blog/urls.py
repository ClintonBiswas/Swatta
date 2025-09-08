from django.urls import path
from blog import views

app_name = 'blog'
urlpatterns = [
    path('blogs/', views.blog_home, name='blogs'),
    path('blog-details/<slug:slug>/', views.blog_details, name='blog-details'),
    path('<slug:slug>/comment/', views.add_comment, name='add-comment'),
    path('<slug:slug>/comment/<int:comment_id>/reply/', views.add_reply, name='add-reply'),
]
