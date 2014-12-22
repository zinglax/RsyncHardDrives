import subprocess

from configobj import ConfigObj
config = ConfigObj('hard_drive_roles.ini')

def mount_hard_drive(): # TODO
    ''' programatically mounts hard drive'''
    pass

def check_readme_files(): # TODO
    ''' checks which files have and do not have a README.txt associated with them.'''
    pass

def synchronize_hard_drives(): # TODO
    ''' synchronizes hard drives using rsync'''
    pass
    
def set_drive_roles(): # TODO
    ''' determins the functionality of each drive whether it is the Primary, Secondary, or Offsite.  Updates a .ini file to reflect changes'''
    pass
    
def update_wiki(): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    pass

def send_email(): # TODO
    ''' Sends an email alerting the person that the backup process is complete'''
    