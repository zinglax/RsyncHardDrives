import subprocess
import smtplib
from configobj import ConfigObj
#import twill.commands as tc
import sys
import getpass
import os
import time
import TracWiki
import datetime

# Gets Information from .ini file
config = ConfigObj('hard_drive_roles.ini')
hard_drives = config['hard_drive']
HardDriveSyncTool = config['paths']["HardDriveSyncTool"]
GateFusionProject = config['paths']['GateFusionProject']
GateFusionProjectHard = config['paths']['GateFusionProjectHard']

# Alert email
to_email = "dylanzingler@gmail.com"
from_email = "dylanzingler@gmail.com"

# Wiki Interaction ***USES HARD URL***
TWC = TracWiki.Trac_Wiki_Communicator(username='dzingler',
                                      password='dzingler',
                                      url=GateFusionProjectHard)

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

def get_readme_description(dir_or_file):
    ''' Gets a description string from a readme file for a directory or a file'''
    readme_file = dir_or_file + "README.txt"
    
    try: 
        with open(readme_file) as readme:
            readme.seek(0)
            readme_lines = readme.readlines()
            for line in readme_lines:
                if "Description:" in line:
                    return line[len("Description:"):-1]
    except IOError:    
        return "No README.txt Found."

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

    # Checking Modification dates
    if not (hard_drives[primary_drive][3] >= hard_drives[secondary_drive][3]):
        print '######################################################'          
        print '## ERROR: The Secondary drive has a later modification date'
        print '## Data could be lost if synchronization continued. Exiting.'
        print '######################################################'  
        return "Modification dates are not correct"
        
    # Using rsync to synchronize drives and return output
    print "## STARTING SYNCHRONIZATION ##########################"
    print "## SEEING OUTPUT FROM RSYNC COMMAND ##################"
    rsync_command = "rsync -zvhr --delete --info=progress2 " + hard_drives[primary_drive][1] + "/ " + hard_drives[secondary_drive][1]   # + " > RSYNC.txt"
    return_val = subprocess.call(rsync_command, shell=True)
    
    if return_val == 0:
        print '######################################################'          
        print "## SYNCRONIZATION COMPLETED AND SUCCESSFUL ###########"
    else:    
        print '######################################################'  
        print '## ERROR: Synchronization did not complete successfuly'
        print '######################################################'  
        
    sync_time = time.time()
    hard_drives[primary_drive][3] = sync_time
    hard_drives[secondary_drive][3] = sync_time
    
    config['hard_drive'] = hard_drives
    config.write()    
        
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

def switch_primary_drive(group_letter):
    if group_letter in {'a', 'A'}:
        group_letter = "A"
        secondary = get_role_for_group('A', 'secondary')
        offsite = get_role_for_group('A', 'offsite')
        primary = get_role_for_group('A', 'primary')
    else:
        group_letter = "B"
        secondary = get_role_for_group('B', 'secondary')
        offsite = get_role_for_group('B', 'offsite')
        primary = get_role_for_group('B', 'primary')
        
    print '## CURRENT PRIMARY IS ' + primary
    print '## 1. Secondary: ' + secondary
    print '## 2. Offsite: ' + offsite
    
    choice = None
    while choice not in {'1', '2'}:
        choice = raw_input("## ENTER DRIVE NUMBER TO SWITCH WITH PRIMARY: ")
    
    if choice == '1':
        if  not hard_drives[primary][3] == hard_drives[secondary][3]:
            print '######################################################'
            print '## ERROR: Modification dates are not correct. '
            print '## Data could be lost if this change is made'
            print '## The primary is must be synchronized with secondary'
            print '## before this change can take place. Exiting command.'
            print '######################################################'
            return
        else:
            hard_drives[primary][0] = 'secondary'
            hard_drives[secondary][0] = 'primary'        
    else:
        if  not hard_drives[primary][3] == hard_drives[offsite][3]:
            print '######################################################'
            print '## ERROR: Modification dates are not correct.'
            print '## Data could be lost if this change is made'
            print '## Try switching the offsite to secondary then'
            print '## synchronizing, then switching primary again.'
            print '## Exiting command...'
            print '######################################################'
            return 
        else:
            hard_drives[primary][0] = 'offsite'
            hard_drives[offsite][0] = 'primary'      

    config['hard_drive'] = hard_drives
    config.write()    
    print '######################################################'    
    print '## UPDATE COMPLETED ##################################'
    print '## Primary: ' + get_role_for_group(group_letter, "primary")
    print '## Secondary: ' + get_role_for_group(group_letter, "secondary")
    print '## Offsite: ' + get_role_for_group(group_letter, "offsite")

def update_wiki(wiki_drive):
    
    HardDriveSyncTool_HomePage = '''= Hard Drive Synchronization Tool =

This page documents the hard drive synchronization tool which is used for backing-up/synchronizing hard drives (mainly the two 2TB hard drives for the project stored locally and the third offsite). 

------------------------------

== [wiki:HardDriveSyncTool/GrpA Group A] == 


== [wiki:HardDriveSyncTool/GrpB Group B] == 


--------------------------------------
== Drives Table ==
Information taken from the configuration file [[BR]]
%s
---------------------------------------

== Documentation =='''
    
    # Table of drive information from .ini file
    drive_table = "||= '''NAME''' =||= '''ROLE''' =||= '''PATH''' =||= '''GROUP''' =||= '''LAST SYNCHRONIZED DATE''' =||\n"
    drive_table_format = '|| %s || %s || %s || %s || %s ||'
    for drive in hard_drives:
        drive_table += drive_table_format % (drive,
                                             hard_drives[drive][0],
                                             hard_drives[drive][1],
                                             hard_drives[drive][2],
                                             datetime.datetime.fromtimestamp(float(hard_drives[drive][3]))) + '\n'
    drive_table += '\n Last Modified: ' + str(datetime.datetime.now())
    
    HardDriveSyncTool_HomePage = HardDriveSyncTool_HomePage % (drive_table)
    
    # Creating Home Page With TracWiki Class
    TWC.create_page('HardDriveSyncTool', page_text=HardDriveSyncTool_HomePage)
    
    
    # Creating all of the Directory pages for selected drive
    mounted = get_mounted_drives()[0]
    if wiki_drive in mounted:
        if hard_drives[wiki_drive][2] == "A":
            folder_name = "GrpA"
        else:
            folder_name = "GrpB"
        
        path = hard_drives[wiki_drive][1]
        update_wiki_helper(path, folder_name)
    
def update_wiki_helper(path, folder_name): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    
    # Gets files and directories for current path
    files = os.walk(path).next()[2]
    directories = os.walk(path).next()[1]    
    
    # Removes hidden or '~' edited files and directories
    for f in files[:]:
        if '.' == f[0] or '~' == f[-1]:
            files.remove(f)                    
    for d in directories[:]:
        if '.' == d[0] or '~' == d[-1]:
            directories.remove(d)        
            
            
    # Removes README.txt Files
    for f in files[:]:
        try:
            if 'README.txt' == f[-10:]:
                files.remove(f)
        except IndexError:
            continue
    #for d in directories[:]:
        #try:
            #if 'README.txt' == d[-10]:
                #directories.remove(d)
        #except IndexError:
            #continue        
    
    body_string = "= " + folder_name + " =\n"

    # Creates the Wiki Page Name
    for drive in hard_drives:
        if hard_drives[drive][1] in path:
            if hard_drives[drive][2] == "A":
                page_name = path.replace(hard_drives[drive][1], "HardDriveSyncTool/GrpA")
            else:
                page_name = path.replace(hard_drives[drive][1], "HardDriveSyncTool/GrpB")

    # Create Files Table
    if not len(files) == 0:
        file_table_header = "||= '''NAME''' =||= '''SIZE ''' =||= ''' MODIFIED DATE ''' =||= ''' PATH ''' =||= ''' NOTES''' =||"
        file_table_format = "|| %s || %s || %s || %s || %s ||" 
        file_table = "=== Files ===\n" + file_table_header
        for f in files:
            info = os.stat(path + '/' + f)
            size = str(info.st_size) + " Bytes"
            modified_date = time.ctime(info.st_mtime)
            full_path = path + '/' + f
            file_table += '\n' + file_table_format % (f, 
                                                      size, 
                                                      modified_date, 
                                                      full_path, 
                                                      get_readme_description(full_path)
                                                      )
            
        body_string += file_table
    else:
            body_string += "\n=== No Files in this Folder ==="    

    # Creates Directories Table
    if not len(directories) == 0:
        directory_table_header = "||= '''NAME''' =||= '''SIZE ''' =||= ''' MODIFIED DATE ''' =||= ''' PATH ''' =||= ''' NOTES''' =||"
        directory_table_format = "||[wiki:%s %s]|| %s || %s || %s || %s ||" 
        directory_table = "=== Directories ===\n" + directory_table_header
        for d in directories:
            info = os.stat(path + '/' + d)
            size = str(info.st_size) + " Bytes"
            modified_date = time.ctime(info.st_mtime)
            full_path = path + '/' + d
            directory_table += '\n' + directory_table_format % (page_name + '/' + d,
                                                                d, 
                                                                size, 
                                                                modified_date, 
                                                                full_path, 
                                                                get_readme_description(full_path)
                                                                )
        
        body_string += "\n" + directory_table
    else:
        body_string += "\n=== No Directories in this Folder ==="
        
    ## Create Wikipage 
    # create_wiki_page(username, password, body_string, wiki_page_name, project_name)
    
                
    TWC.create_page(page_name, body_string)
    
    #print body_string

    # Recurse Down to the next level of wiki pages
    for d in directories:
        update_wiki_helper(path + '/' + d, d)

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

def switch_secondary_offsite(group_letter):
    if group_letter in {'a', 'A'}:
        secondary = get_role_for_group('A', 'secondary')
        offsite = get_role_for_group('A', 'offsite')
    else:
        secondary = get_role_for_group('B', 'secondary')
        offsite = get_role_for_group('B', 'offsite')
    
    hard_drives[secondary][0] = 'offsite'
    hard_drives[offsite][0] = 'secondary'
    
    config['hard_drive'] = hard_drives
    config.write()    
    print '######################################################'
    print '## UPDATE COMPLETED ##################################'
    print '## SECONDARY IS NOW: ' + offsite
    print '## OFFSITE IS NOW: ' + secondary
        
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
    print '## 4. Update Wiki Pages ##############################'
    print '## 5. Switch Secondary and Offsite ###################'
    print '## 6. Switch Primary Drive ###########################'
    print '## 7. Display Drive Info #############################'
    command = raw_input("## ENTER A COMMAND NUMBER: ")    
    print '######################################################'
    return command

def command_change_drive_roles():
    group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
                
    while group_letter not in {"A", "a","B","b"}:
        print '######################################################'
        print "## ERROR: PLEASE ENTER A OR B..."
        print '######################################################'                     
        
        group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
    set_drive_roles(group_letter) 
    
def command_refresh_mounted_drives():
    output_mounted_drives()
    
def command_synchronize_hard_drives():    
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

def command_update_wiki_pages():
    primaries = {}
    count = 0            
    print '######################################################' 
    print "## PRIMARY DRIVES ####################################"
    for i, drive in enumerate(hard_drives):
        if hard_drives[drive][0] == 'primary':
            count = count + 1
            print "## " + str(count) + ". " + drive
            primaries[str(count)] = drive
    
    primary = None
    while primary not in primaries.keys():
        primary = raw_input("## ENTER A PRIMARY DRIVE NUMBER FOR WIKI UPDATE: ")
    
    primary = primaries[primary]      
    
    update_wiki(primary)    

def command_switch_secondary_and_offsite():
    group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")                    
    while group_letter not in {"A", "a","B","b"}:
        print '######################################################'
        print "## ERROR: PLEASE ENTER A OR B..."
        print '######################################################'                                     
        group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")                    
    switch_secondary_offsite(group_letter)    

def command_switch_primary_drive():
    group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
                            
    while group_letter not in {"A", "a","B","b"}:
        print '######################################################'
        print "## ERROR: PLEASE ENTER A OR B..."
        print '######################################################'                     
        
        group_letter = raw_input("## ENTER A GROUP LETTER (A OR B): ")
    
    switch_primary_drive(group_letter)    
    

def command_display_drives():
    print '######################################################'    
    print '## INFORMATION STORED IN SYNCHRONIZATION TOOL ########'
    
    for d in hard_drives:
        print '######################################################'            
        print '## DRIVE: '+ d 
        print '## ROLE: ' + hard_drives[d][0]
        print '## MOUNT POINT: ' + hard_drives[d][1]
        print '## GROUP: ' + hard_drives[d][2]
        print '## LAST SYNCHRONIZED: ' + str(datetime.datetime.fromtimestamp(float(hard_drives[d][3])))
    

if __name__=="__main__":
    
    print '######################################################'
    print '### WELCOME TO THE HARD DRIVE SYNCHRONIZATION TOOL ###'
        
    output_mounted_drives()
    
    command = output_prompt_commands()    
    
    # Command Loop
    while True:
        
        # COMMAND 1
        if command == str(1):
            command_change_drive_roles()
            
        # COMMAND 2
        elif command == str(2):
            command_refresh_mounted_drives()
            
        # COMMAND 3    
        elif command == str(3):
            command_synchronize_hard_drives()
                         
        # COMMAND 4
        elif command == str(4):
            command_update_wiki_pages()
              
        # COMMAND 5          
        elif command == str(5):
            command_switch_secondary_and_offsite()
        
        # COMMAND 6     
        elif command == str(6):
            command_switch_primary_drive()
                    
        # COMMAND 7
        elif command == str(7):
            command_display_drives()
        else:
            print '######################################################'   
            print '## ERROR: Command not recognized. Try again'
        command = output_prompt_commands()
        