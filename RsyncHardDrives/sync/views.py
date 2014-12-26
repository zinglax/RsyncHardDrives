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
  
  # Listing what drives are mounted
  mounted_drives = synchronize.get_mounted_drives()[0]
  drive_roles = []
  for d in mounted_drives:
    drive_roles.append((d , synchronize.get_drive_role(d), synchronize.get_drive_group(d)))
  script_args["mounted_drives"] = drive_roles
  
  # Listing what drives are being kept in synchronization
  hard_drives = []
  for d in synchronize.hard_drives.keys():
    hard_drives.append((d, synchronize.get_drive_role(d), synchronize.get_drive_group(d)))
  script_args["hard_drives"] = hard_drives

  # A role change for Group A was submitted
  if 'A-Primary' in request.GET and 'A-Secondary' in request.GET and 'A-Offsite' in request.GET:
    primary = request.GET["A-Primary"]
    secondary = request.GET["A-Secondary"]
    offsite = request.GET["A-Offsite"]    
    all_roles = set(['GrpADrv1', 'GrpADrv2', 'GrpADrv3'])
    submitted_roles = [primary, secondary, offsite]
    
    # Check if there is a different drive for each role
    if set(submitted_roles) == all_roles:
      
      # Change drives in .ini file
      synchronize.set_drive_role(primary, 'primary')
      synchronize.set_drive_role(secondary, 'secondary')
      synchronize.set_drive_role(offsite, 'offsite')
                  
      # Redirect back home
      #return render_to_response("sync/home.html", script_args)
      return HttpResponseRedirect('/good_role_change/')
  
    else:
      error_args = script_args.copy()
      error_args["a_role_error"] = "A-Error"
      return render_to_response("sync/home.html", error_args)
  
  # A role change for Group B was submitted
  if 'B-Primary' in request.GET and 'B-Secondary' in request.GET and 'B-Offsite' in request.GET:
    primary = request.GET["B-Primary"]
    secondary = request.GET["B-Secondary"]
    offsite = request.GET["B-Offsite"]    
    all_roles = set(['GrpADrv1', 'GrpADrv2', 'GrpADrv3'])
    submitted_roles = [primary, secondary, offsite]
    
    # Check if there is a different drive for each role
    if set(submitted_roles) == all_roles:
      
      # Change drives in .ini file
      synchronize.set_drive_role(primary, 'primary')
      synchronize.set_drive_role(secondary, 'secondary')
      synchronize.set_drive_role(offsite, 'offsite')
                  
      # Redirect back home
      #return render_to_response("sync/home.html", script_args)
      return HttpResponseRedirect('/good_role_change/')
  
    else:
      error_args = script_args.copy()
      error_args["b_role_error"] = "B-Error"
      return render_to_response("sync/home.html", error_args)
  
  
  return render_to_response("sync/home.html", script_args)