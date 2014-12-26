from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, QueryDict
import synchronize

# Dictionary to add objects passed to the through to the HTML
script_args = {}
script_args['theme'] = "a"
    

def home(request):
  
  mounted_drives = synchronize.get_mounted_drives()[0]
  drive_roles = []
  for d in mounted_drives:
    drive_roles.append((d , synchronize.get_drive_role(d), synchronize.get_drive_group(d)))
  script_args["mounted_drives"] = drive_roles
  
  hard_drives = []
  for d in synchronize.hard_drives.keys():
    hard_drives.append((d, synchronize.get_drive_role(d), synchronize.get_drive_group(d)))
  script_args["hard_drives"] = hard_drives
  
  
  return render_to_response("sync/home.html", script_args)