import subprocess
import smtplib
from configobj import ConfigObj
import twill.commands as tc
import sys
import getpass

# Gets Information from .ini file
config = ConfigObj('hard_drive_roles.ini')
hard_drives = config['hard_drive']

# Alert email
to_email = "dylanzingler@gmail.com"
from_email = "dylanzingler@gmail.com"

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

def synchronize_hard_drives(): 
    ''' synchronizes hard drives using rsync'''
    primary_drive = "GrpADrv1"
    secondary_drive = "GrpADrv2"
    
    # Check that drives are mounted 
    mounted = get_mounted_drives()[0]
    if not (primary_drive in mounted) or not (secondary_drive in mounted):
        print "One of the drives you are trying to synchornize is not mounted (Exiting...)"        
        return
    
    # Checking that drives have proper roles
    if not(check_hard_drive_role(primary_drive, "primary")):
        print "The primary drive is not properly labeled in the .ini (Exiting...)"
    if not(check_hard_drive_role(secondary_drive, "secondary")):
        print "The secondary drive is not properly labeled in the .ini (Exiting...)"


    # Using rsync to synchronize drives and return output
    rsync_command = "rsync -zvhr --delete " + hard_drives[primary_drive][1] + "/ " + hard_drives[secondary_drive][1]    
    return_val = subprocess.call(rsync_command, shell=True)
    
    return return_val

def check_hard_drive_role(drive, role):
    ''' checks whether the given hard drives are listed as a given role'''
    return hard_drives[drive][0] == role
    
def check_group_roles(group_letter):
    ''' Ensure that there is a primary, secondary and an offsite for each group. group letter must be either A or B'''
    
    all_roles = set(['primary', 'secondary', 'offsite'])
    
    found_roles = []
    for key in hard_drives:
        if group_letter in key:
            found_roles.append(hard_drives[key][0])
    return all_roles == set(found_roles)
                
    
def set_drive_roles(group_letter):
    ''' determins the functionality of each drive whether it is the Primary, Secondary, or Offsite.  Updates a .ini file to reflect changes'''
    
    for key in hard_drives:
        if group_letter in key:
            role = "teststring"
            while (not role.isdigit()) or (role not in ['1','2','3']):
                role = raw_input("Set " + key + " to? Primary = 1, Secondary = 2, Offsite = 3. \nEnter Number: ")
                
                if (not role.isdigit()) or (role not in ['1','2','3']):
                    print "Please Enter 1, 2, or 3, for corrisponding drive role."
            
            if role == '1':
                hard_drives[key][0] = 'primary'
            elif role == '2':
                hard_drives[key][0] = 'secondary'
            else:
                hard_drives[key][0] = 'offsite'
    
        
    if not check_group_roles(group_letter):
        print "Two or more of the drives were set to the same value. Try again."
        set_drive_roles(group_letter)
    
    config['hard_drive'] = hard_drives
    config.write()
    
    print "Update Complete"
    for key in hard_drives:
        if group_letter in key:
            print "Drive: " + key + " is set to: " + hard_drives[key][0]
    
    
def update_wiki(): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    pass


#----------------------------------------------------------------------
def get_user_info():
    """
    This funciton gets the username and password of the user and returns
    them 
    """
    username = str(raw_input("Enter Trac Username: "))
    password = str(getpass.getpass("Enter Trac Password: "))
    #password = str(raw_input("Enter Trac Password: "))
    return username, password

#----------------------------------------------------------------------
def wiki_login(username, password):
    """
    logs in to the wiki given the arguments username and password.
    """    
    tc.add_auth('Trac', Gatelink_project_path, 
                '%s' % username, '%s' % password)
    tc.go(Gatelink_project_path + '/login')

#----------------------------------------------------------------------
def create_wiki_page(username, password, body_string, wiki_page_name):
    """
    Creates a wiki page with the content specified by the paramater
    'data_string' with the name specified by 'wiki_page_name'
    """

    wiki_login(username, password)
    
    #should specify where page should be located
    home = Gatelink_project_path + '/wiki'
    edit = '?action=edit'
    slash = '/'
    newpage = home + slash + wiki_page_name + edit    

    #specifies the page main page that you want the list of customers on   
    tc.go(newpage)
    
    #writes to and submits data to the wikipage that was created
    tc.showforms()
    tc.fv('2','text', body_string)
    tc.submit('11')  

def send_email(): # TODO
    import smtplib
    
    gmail_user = "dylanzingler@gmail.com"
    gmail_pwd = ""
    FROM = 'dylanzingler@gmail.com'
    TO = ['dylanzingler@gmail.com'] #must be a list
    SUBJECT = "Testing sending using gmail"
    TEXT = "Testing sending mail using gmail servers"
    
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        #server = smtplib.SMTP(SERVER) 
        server = smtplib.SMTP("smtp.gmail.com", 465) #or port 465 doesn't seem to work!
        #server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        #server.quit()
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"



if __name__=="__main__":
    
    send_email()
    
    