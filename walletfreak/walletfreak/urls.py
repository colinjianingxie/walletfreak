"""
URL configuration for walletfreak project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from custom_admin import views as custom_admin_views

urlpatterns = [
    path('admin/logout/', custom_admin_views.admin_logout_view, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('cards.urls')),
    path('accounts/', include('accounts.urls')),
    path('logout/', accounts_views.logout_redirect, name='logout'),
    path('profile/', accounts_views.profile, name='profile'),

    path('wallet/', include('dashboard.urls')),
    path('blog/', include('blog.urls')),
    path('custom-admin/', include('custom_admin.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
