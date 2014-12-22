import subprocess

from configobj import ConfigObj

# Gets Information from .ini file
config = ConfigObj('hard_drive_roles.ini')
hard_drives = config['hard_drive']


def mount_hard_drive(): # TODO
    ''' programatically mounts hard drive'''
    # For now just make sure that drives are mounted
    pass

def get_mounted_drives():
    ''' checks which drives are mounted'''
    
    command = "mount | grep "
    mounted_drives = []
    unmounted_drives = []
    
    # Checks each hard drive to see if its mounted
    for key in hard_drives:
        return_val = subprocess.call(command + key, shell=True)        
        if return_val == 1: # empty return values for subprocess are 1
            unmounted_drives.append(key)
        else:
            mounted_drives.append(key)
    return mounted_drives, unmounted_drives

def check_readme_files(): # TODO
    ''' checks which files have and do not have a README.txt associated with them.'''
    pass

def synchronize_hard_drives(): # TODO
    ''' synchronizes hard drives using rsync'''
    primary_drive = "GrpADrv1"
    secondary_drive = "GrpADrv2"
    
    # Check that drives are mounted 
    mounted = get_mounted_drives()[0]
    if not (primary_drive in mounted) or not (secondary_drive in mounted):
        print "One of the drives you are trying to synchornize is not mounted"
        return

    rsync_command = "rsync -zvhr --delete " + hard_drives[primary_drive][1] + "/ " + hard_drives[secondary_drive][1]
    
    return_val = subprocess.call(rsync_command, shell=True)
    
    return return_val

    
    
def set_drive_roles(): # TODO
    ''' determins the functionality of each drive whether it is the Primary, Secondary, or Offsite.  Updates a .ini file to reflect changes'''
    pass
    
def update_wiki(): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    pass

def send_email(): # TODO
    ''' Sends an email alerting the person that the backup process is complete'''
    pass


if __name__=="__main__":
    
    print synchronize_hard_drives()
    
    
    