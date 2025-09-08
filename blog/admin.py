from django.contrib import admin
from .models import BlogCategory, BlogTags, MyBlog, BlogComment
# Register your models here.
admin.site.register(BlogCategory)
admin.site.register(BlogTags)
admin.site.register(MyBlog)
admin.site.register(BlogComment)