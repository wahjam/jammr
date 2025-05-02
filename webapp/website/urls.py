from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'website.views.home', name='home'),
    # url(r'^website/', include('website.foo.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('website.api.urls')),
    url(r'^', include('website.payments.urls')),
    url(r'^', include('website.recorded_jams.urls')),
    url(r'^', include('website.jammr.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
]
