from django.conf.urls import url, include

urlpatterns = [
    url(r'^forum/', include('djangobb_forum.urls', namespace='djangobb')),
]
