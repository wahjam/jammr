from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from django.contrib import admin

urlpatterns = [
        # Redirect password change page to jammr.net top-level site, this is used by DjangoBB
        url(r'^accounts/password_change/$', RedirectView.as_view(url='https://jammr.net/accounts/password_change/', permanent=True), name='auth_password_change'),
        url(r'^accounts/login/$', auth_views.LoginView.as_view(), name='user_signin'),
        url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), name='user_signout'),

        url(r'^admin/', include(admin.site.urls)),
        url(r'^pm/', include('django_messages.urls')),
        url(r'^', include('djangobb_forum.urls', namespace='djangobb')),
]
