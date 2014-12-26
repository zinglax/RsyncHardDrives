from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    
    url(r'^$', 'sync.views.home', name='home'), 

    # Examples:
    # url(r'^$', 'RsyncHardDrives.views.home', name='home'),
    # url(r'^RsyncHardDrives/', include('RsyncHardDrives.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
