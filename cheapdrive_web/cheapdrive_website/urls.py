
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include,path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',
    include("entry.urls")),
    path('admin/', admin.site.urls),
    path('', include('refill.urls', namespace='refill')),
    #path("refill/",
    #include("refill.urls")),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


