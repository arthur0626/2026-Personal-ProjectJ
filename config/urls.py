from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.auth_urls', 'auth'), namespace='auth')),
    path('accounts/social/', include('allauth.urls')),
    path('', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('coding/', include('coding.urls')),
    path('activity/', include('activity.urls')),
    # Serves uploads only when DEBUG; production storage is decided in Milestone 11.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
