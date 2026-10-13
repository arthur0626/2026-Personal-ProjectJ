from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.auth_urls', 'auth'), namespace='auth')),
    path('accounts/social/', include('allauth.urls')),
    path('', include('accounts.urls')),
    path('blog/', include('blog.urls')),
]
