from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('', include('django.contrib.auth.urls')),
    path('', include('product.urls')),
    path('', include('blog.urls')),
    path('poll/', include('pool.urls')),
    path('tinymce/', include('tinymce.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
