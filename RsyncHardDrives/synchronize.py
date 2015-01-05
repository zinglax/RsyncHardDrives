import subprocess
import smtplib
from configobj import ConfigObj
#import twill.commands as tc
import sys
import getpass
import os
import time
import TracWiki

# Gets Information from .ini file
config = ConfigObj('hard_drive_roles.ini')
hard_drives = config['hard_drive']
HardDriveSyncTool = config['paths']["HardDriveSyncTool"]
GateFusionProject = config['paths']['GateFusionProject']

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
    
    FNULL = open(os.devnull, 'w')
    
    # Checks each hard drive to see if its mounted
    for key in hard_drives:
        return_val = subprocess.call(command + key, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)        
        if return_val == 1: # empty return values for subprocess are 1
            unmounted_drives.append(key)
        else:
            mounted_drives.append(key)
    return mounted_drives, unmounted_drives

def get_drive_role(drive):
    return hard_drives[drive][0]

def get_role_for_group(group_letter, role):
    for drive in hard_drives:
        if hard_drives[drive][0] == role and hard_drives[drive][2] == group_letter:
            return drive
    
def get_drive_group(drive):
    return hard_drives[drive][2]
    
def check_readme_files(): # TODO
    ''' checks which files have and do not have a README.txt associated with them.'''
    pass

def check_rsync_progress():
    while True:
        try:
            with open("RSYNC.txt", 'rb') as fh:
                fh.seek(-1024, 2)
                last = fh.readlines()[-1].decode()        
                
                break
        except IOError:
            pass
    return last[last.find('%')-2:last.find('%')]

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

  

def synchronize_hard_drives(primary_drive, secondary_drive): 
    ''' synchronizes hard drives using rsync'''    
    
    # Check that drives are mounted 
    mounted = get_mounted_drives()[0]
    if not (primary_drive in mounted) or not (secondary_drive in mounted):
        print '######################################################'                        
        print "## ERROR: One of the drives is not mounted, exiting command"        
        print '######################################################'                        
        return "Drive not Mounted"
    
    # Checking that drives have proper roles
    if not(check_hard_drive_role(primary_drive, "primary")):
        print '######################################################'                        
        print "## Error: Primary drive does not have correct role"
        print '######################################################'                        
        return "Primary is Not Properly Labeled"
    if not(check_hard_drive_role(secondary_drive, "secondary")):
        print '######################################################'                        
        print "## Error: Secondary drive does not have correct role"
        print '######################################################'  
        return "Secondary is Not Properly Labeled"


    # Using rsync to synchronize drives and return output
    print "## STARTING SYNCHRONIZATION ##########################"
    print "## SEEING OUTPUT FROM RSYNC COMMAND ##################"
    rsync_command = "rsync -zvhr --delete --progress " + hard_drives[primary_drive][1] + "/ " + hard_drives[secondary_drive][1]   # + " > RSYNC.txt"
    return_val = subprocess.call(rsync_command, shell=True)
    
    if return_val == 0:
        print '######################################################'          
        print "## SYNCRONIZATION COMPLETED AND SUCCESSFUL ###########"
    else:    
        print '######################################################'  
        print '## ERROR: Synchronization did not complete successfuly'
        print '######################################################'  
        

        
    return return_val

                
    
def set_drive_roles_helper(group_letter):
    ''' determins the functionality of each drive whether it is the Primary, Secondary, or Offsite.  Updates a .ini file to reflect changes'''
    
    for key in hard_drives:
        if group_letter in key:
            role = "teststring"
            while (not role.isdigit()) or (role not in ['1','2','3']):
                print "## Set " + key + " to?"
                print "## 1. Primary" 
                print "## 2. Secondary"
                print "## 3. Offsite"
                role = raw_input("## ENTER A ROLE NUMBER (1, 2, OR 3): ")
                
                if (not role.isdigit()) or (role not in ['1','2','3']):
                    print '######################################################'                                
                    print "## ERROR: Enter 1, 2, or 3, for a drive role."
                    print '######################################################'            
                    
            
            if role == '1':
                hard_drives[key][0] = 'primary'
            elif role == '2':
                hard_drives[key][0] = 'secondary'
            else:
                hard_drives[key][0] = 'offsite'
    
        
    if not check_group_roles(group_letter):
        print '######################################################'            
        print "## ERROR: Two drives detected with same value. Try again."
        print '######################################################'            
        
        set_drive_roles_helper(group_letter)
        
        
    return hard_drives

def set_drive_roles(group_letter):
    if group_letter in {'a', "A"}:
        group_letter = 'A'
    else:
        group_letter = 'B'
    
    hard_drives = set_drive_roles_helper(group_letter)
    
    config['hard_drive'] = hard_drives
    config.write()
    
    print '######################################################'    
    print "## UPDATE COMPLETE ###################################"
    for key in hard_drives:
        if group_letter in key:
            print "## Drive: " + key + " is set to: " + hard_drives[key][0]

def set_drive_role(drive, role):
    if (not role in {"primary", "secondary", "offsite"}) or (drive not in hard_drives.keys()):
        print "The drive or role you submitted was not recognized, no changes made"
    else:
        hard_drives[drive][0] = role
        config['hard_drive'] = hard_drives
        config.write()
    
def update_wiki(path, folder_name): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    
    # Gets files and directories for current path
    files = os.walk(path).next()[2]
    directories = os.walk(path).next()[1]
            
    body_string = "= " + folder_name + " =\n"

    # Create Files Table
    if not len(files) == 0:
        file_table_header = "|| NAME || SIZE || MODIFIED DATE || PATH || NOTES ||"
        file_table_format = "|| %s || %s || %s || %s || %s ||" 
        file_table = "=== Files ===\n" + file_table_header
        for f in files:
            info = os.stat(path + '/' + f)
            size = str(info.st_size) + " Bytes"
            modified_date = time.ctime(info.st_mtime)
            full_path = path + '/' + f
            file_table += '\n' + file_table_format % (f, size, modified_date, full_path, "Nothing yet")
            
        body_string += file_table
    else:
            body_string += "\n=== No Files in this Folder ==="    

    # Creates Directories Table
    if not len(directories) == 0:
        directory_table_header = "|| NAME || SIZE || MODIFIED DATE || PATH || NOTES ||"
        directory_table_format = "|| %s || %s || %s || %s || %s ||" 
        directory_table = "=== Directories ===\n" + directory_table_header
        for d in directories:
            info = os.stat(path + '/' + d)
            size = str(info.st_size) + " Bytes"
            modified_date = time.ctime(info.st_mtime)
            full_path = path + '/' + d
            directory_table += '\n' + file_table_format % (d, size, modified_date, full_path, "Nothing yet")
        
        body_string += "\n" + directory_table
    else:
        body_string += "\n=== No Directories in this Folder ==="
        
    ## Create Wikipage 
    # create_wiki_page(username, password, body_string, wiki_page_name, project_name)
    print body_string

    # Recurse Down to the next level of wiki pages
    for d in directories:
        update_wiki(path + '/' + d, d)

def walking_files(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            print(os.path.join(root, name))
        for name in dirs:
            print(os.path.join(root, name))    

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

def output_mounted_drives():
    print '######################################################'    
    print '## CURRENT DRIVES MOUNTED ############################'
        
    mounted = get_mounted_drives()[0]
    if len(mounted) == 0:
        print '## There are no drives currently mounted'
    else:
        for i, d in enumerate(mounted):
            print '## ' + str(i+1) + '. ' + d    

    print '######################################################'    
                

def output_prompt_commands():
    print '######################################################'
    print '## COMMANDS ##########################################'
    print '## 1. Change Drive Roles #############################'
    print '## 2. Refresh Mounted Drives #########################'
    print '## 3. Synchronize Hard Drvies ########################'
    command = raw_input("## ENTER A COMMAND NUMBER: ")    
    print '######################################################'
    return command

if __name__=="__main__":
    
    print '######################################################'
    print '### WELCOME TO THE HARD DRIVE SYNCHRONIZATION TOOL ###'
        
    output_mounted_drives()
    
    command = output_prompt_commands()
    
    
    # Command Loop
    while True:
        
        # COMMAND 1
        if command == str(1):
            group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
            
            while group_letter not in {"A", "a","B","b"}:
                print '######################################################'
                print "## ERROR: PLEASE ENTER A OR B..."
                print '######################################################'                     
                
                group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
            set_drive_roles(group_letter)
            
        # COMMAND 2
        elif command == str(2):
            output_mounted_drives()
            
        # COMMAND 3    
        elif command == str(3):
            primaries = {}
            count = 0
            # Select a Primary Drive to Synchronize
            print "## PRIMARY DRIVES ####################################"
            for i, drive in enumerate(hard_drives):
                if hard_drives[drive][0] == 'primary':
                    count = count + 1
                    print "## " + str(count) + ". " + drive
                    primaries[str(count)] = drive
            
            primary = None
            while primary not in primaries.keys():
                primary = raw_input("## ENTER A PRIMARY DRIVE NUMBER: ")
            
            primary = primaries[primary]
            
            group_letter = hard_drives[primary][2]
            secondary = get_role_for_group(group_letter, 'secondary')        
            
            print '######################################################'                
            print '## Trying to Synchronize Data on'
            print '## Primary Drive: ' + primary
            print '## To existing data on'
            print '## Secondary Drive: ' + secondary
            
            synchronize_hard_drives(primary, secondary)
            
            
            # Check if the secondary has been synced later than the primary (or maybe more data on secondary than primary)
             
             
        else:
            print '######################################################'   
            print '## ERROR: Command not recognized. Try again'
        command = output_prompt_commands()
        