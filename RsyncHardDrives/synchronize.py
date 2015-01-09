import subprocess,sys, getpass, os, time, datetime, smtplib, re
import TracWiki
from configobj import ConfigObj
from email.mime.text import MIMEText

# Gets Information from .ini file
config = ConfigObj('hard_drive_roles.ini')
hard_drives = config['hard_drive']
LargeFileContentManagementSystem = config['paths']["LargeFileContentManagementSystem"]
GateFusionProject = config['paths']['GateFusionProject']
GateFusionProjectHard = config['paths']['GateFusionProjectHard']

# Alert email
to_email = config['email']['to_email']
from_email = config['email']['from_email']

# Wiki Interaction 
try: 
    TWC = TracWiki.Trac_Wiki_Communicator(url=GateFusionProject)
except IndexError:
    print 'failed to login. Exiting Program'
    time.sleep(2.5)
    sys.exit()
 
    
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
    ''' Ensure that there is a primary, local_backup and an offsite_backup for each group. group letter must be either A or B'''
    
    all_roles = set(['primary', 'local_backup', 'offsite_backup'])
    
    found_roles = []
    for key in hard_drives:
        if group_letter in key:
            found_roles.append(hard_drives[key][0])
    return all_roles == set(found_roles)

def synchronize_hard_drives(primary_drive, local_backup_drive): 
    ''' synchronizes hard drives using rsync'''    
    
    # Check that drives are mounted 
    mounted = get_mounted_drives()[0]
    if not (primary_drive in mounted) or not (local_backup_drive in mounted):
        print '                                                      '                        
        print "   ERROR: One of the drives is not mounted, exiting command"        
        print '                                                      '                        
        return "Drive not Mounted"
    
    # Checking that drives have proper roles
    if not(check_hard_drive_role(primary_drive, "primary")):
        print '                                                      '                        
        print "   Error: Primary drive does not have correct role"
        print '                                                      '                        
        return "Primary is Not Properly Labeled"
    if not(check_hard_drive_role(local_backup_drive, "local_backup")):
        print '                                                      '                        
        print "   Error: Local Backup drive does not have correct role"
        print '                                                      '  
        return "Local Backup is Not Properly Labeled"

    # Checking Modification dates
    if not (hard_drives[primary_drive][3] >= hard_drives[local_backup_drive][3]):
        print '                                                      '          
        print '   ERROR: The Local Backup drive has a later modification date'
        print '   Data could be lost if synchronization continued. Exiting.'
        print '                                                      '  
        return "Modification dates are not correct"
        
    # Using rsync to synchronize drives and return output
    print "   STARTING SYNCHRONIZATION                           "
    print "   SEEING OUTPUT FROM RSYNC COMMAND                   "
    rsync_command = "rsync -zvhr --delete --info=progress2 " + hard_drives[primary_drive][1] + "/ " + hard_drives[local_backup_drive][1]   # + " > RSYNC.txt"
    return_val = subprocess.call(rsync_command, shell=True)
    
    if return_val == 0:
        print '                                                      '          
        print "   SYNCRONIZATION COMPLETED AND SUCCESSFUL           #"
    else:    
        print '                                                      '  
        print '   ERROR: Synchronization did not complete successfuly'
        print '                                                      '  
        
    sync_time = time.time()
    hard_drives[primary_drive][3] = sync_time
    hard_drives[local_backup_drive][3] = sync_time
    
    config['hard_drive'] = hard_drives
    config.write()    
        
    return return_val
   
def switch_primary_drive(group_letter):
    if group_letter in {'a', 'A'}:
        group_letter = "A"
        local_backup = get_role_for_group('A', 'local_backup')
        offsite_backup = get_role_for_group('A', 'offsite_backup')
        primary = get_role_for_group('A', 'primary')
    else:
        group_letter = "B"
        local_backup = get_role_for_group('B', 'local_backup')
        offsite_backup = get_role_for_group('B', 'offsite_backup')
        primary = get_role_for_group('B', 'primary')
        
    print '   CURRENT PRIMARY IS ' + primary
    print '   1. Local Backup: ' + local_backup
    print '   2. Offsite Backup: ' + offsite_backup
        
    choice = input_command("   ENTER DRIVE NUMBER TO SWITCH WITH PRIMARY: ", {'1', '2'})    
    
    if not choice == 'exit':
        if choice == '1':
            if  not hard_drives[primary][3] == hard_drives[local_backup][3]:
                print '                                                      '
                print '   ERROR: Modification dates are not correct. '
                print '   Data could be lost if this change is made'
                print '   The primary is must be synchronized with local_backup'
                print '   before this change can take place. Exiting command.'
                print '                                                      '
                return
            else:
                hard_drives[primary][0] = 'local_backup'
                hard_drives[local_backup][0] = 'primary'        
        elif choice == '2':
            if  not hard_drives[primary][3] == hard_drives[offsite_backup][3]:
                print '                                                      '
                print '   ERROR: Modification dates are not correct.'
                print '   Data could be lost if this change is made'
                print '   Try switching the offsite_backup to local_backup then'
                print '   synchronizing, then switching primary again.'
                print '   Exiting command...'
                print '                                                      '
                return 
            else:
                hard_drives[primary][0] = 'offsite_backup'
                hard_drives[offsite_backup][0] = 'primary'      
    
        config['hard_drive'] = hard_drives
        config.write()    
        print '                                                      '    
        print '   UPDATE COMPLETED                                   '
        print '   Primary: ' + get_role_for_group(group_letter, "primary")
        print '   Local Backup: ' + get_role_for_group(group_letter, "local_backup")
        print '   Offsite Backup: ' + get_role_for_group(group_letter, "offsite_backup")
    else:
        print '   Command Exiting'

def update_wiki(wiki_drive):
    
    LargeFileContentManagementSystem_HomePage = '''= Large File Content Management System =

This page documents the Large File Content Management System which is used for backing-up/synchronizing hard drives (mainly the two 2TB hard drives for the project stored locally and the third offsite_backup). 

------------------------------

== [wiki:LargeFileContentManagementSystem/GrpA Group A] == 


== [wiki:LargeFileContentManagementSystem/GrpB Group B] == 


--------------------------------------
== Drives Table ==
Information taken from the configuration file [[BR]]
%s
---------------------------------------
[[Image(https://raw.githubusercontent.com/zinglax/RsyncHardDrives/master/RsyncHardDrives/LFCMS.png)]]

== Documentation ==
The Large File Management System (LFMS) is a tool that keeps large files backed up on a group of 3 different drives.  Within a group, there are 3 different 'Roles' that a drive can have; 1. Primary, 2. Local Backup, 3. Offsite Backup.  The purpose of the Primary drive is to have the latest files/information intended to be stored/backed-up with the system. The Primary drive is the only drive that should ever be written to.  This drive is one that will copy its data to the other drives in the system.  The Local Backup drive is on site and intended to be a complete backup of the primary (after synchronization takes place).  Reading or copying files off of this drive will not interfere with the LFMS life cycle.  Writing to this drive will result in that new data being overwritten/deleted with information from the Primary drive. DO NOT WRITE DATA TO THE LOCAL BACKUP OR OFFSITE BACKUP, DATA WILL BE LOST. The Offsite Backup functions like the Local Backup in the sense that they will both be copies of what is on the Primary drive. The Offsite backup and Local Backup will be swapped out for each other periodically in order to keep the data in sync.  The roles of the drives must be changed at this point in order to run the synchronization.  Only the drive whose role is Local Backup can be synchronized with the Primary.

'''
    
    
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
    
    LargeFileContentManagementSystem_HomePage = LargeFileContentManagementSystem_HomePage % (drive_table)
    
    # Creating Home Page With TracWiki Class
    TWC.create_page('LargeFileContentManagementSystem', page_text=LargeFileContentManagementSystem_HomePage)
        
    # Creating all of the Directory pages for selected drive
    mounted = get_mounted_drives()[0]
    if wiki_drive in mounted:
        if hard_drives[wiki_drive][2] == "A":
            folder_name = "GrpA"
        else:
            folder_name = "GrpB"
        
        path = hard_drives[wiki_drive][1]
        update_wiki_helper(path, folder_name)
    else:
        print '   Primary drive used for Wiki Update is not mounted.'
        print '   Only updated Home Page. Try mounting and reupdating.'
    
def update_wiki_helper(path, folder_name): # TODO
    ''' Updates the wiki page with each of the drives information and file info'''
    
    # Gets files and directories for current path
    files = os.walk(path).next()[2]
    directories = os.walk(path).next()[1] 
    
    for p in hard_drives.keys():
        if hard_drives[p][1] in path:
            drive_path = path[path.find(hard_drives[p][1])+len(hard_drives[p][1]):]
            drive_path = 'Grp' + hard_drives[p][2] + drive_path
            break
        
    
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
  
    body_string = "= " + folder_name + " =\n"

    # Creates the Wiki Page Name
    for drive in hard_drives:
        if hard_drives[drive][1] in path:
            if hard_drives[drive][2] == "A":
                page_name = path.replace(hard_drives[drive][1], "LargeFileContentManagementSystem/GrpA")
            else:
                page_name = path.replace(hard_drives[drive][1], "LargeFileContentManagementSystem/GrpB")

    # Create Files Table
    if not len(files) == 0:
        file_table_header = "||= '''NAME''' =||= '''SIZE ''' =||= ''' MODIFIED DATE ''' =||= ''' PATH ''' =||= ''' NOTES''' =||"
        file_table_format = "|| %s || %s || %s || %s || %s ||" 
        file_table = "=== Files ===\n" + file_table_header
        for f in files:
            info = os.stat(path + '/' + f)
            size = str(info.st_size) + " Bytes"
            modified_date = time.ctime(info.st_mtime)
            full_path = drive_path + '/' + f
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
            full_path = drive_path + '/' + d
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
                
    TWC.create_page(page_name, body_string)

    # Recurse Down to the next level of wiki pages
    for d in directories:
        update_wiki_helper(path + '/' + d, d)

def walking_files(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            print(os.path.join(root, name))
        for name in dirs:
            print(os.path.join(root, name))    

def send_email(to_email, from_email, msg): 
    
    # Create a text/plain message
    msg = MIMEText(msg)    
    msg['Subject'] = 'Large File Content Management System'
    msg['From'] = from_email
    msg['To'] = to_email
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('cismailrelay.arinc.com')
    s.sendmail(from_email, [to_email], msg.as_string())
    s.quit()    
    return "Email Sent"

def switch_local_backup_offsite_backup(group_letter):
    if group_letter in {'a', 'A'}:
        local_backup = get_role_for_group('A', 'local_backup')
        offsite_backup = get_role_for_group('A', 'offsite_backup')
    else:
        local_backup = get_role_for_group('B', 'local_backup')
        offsite_backup = get_role_for_group('B', 'offsite_backup')
    
    hard_drives[local_backup][0] = 'offsite_backup'
    hard_drives[offsite_backup][0] = 'local_backup'
    
    config['hard_drive'] = hard_drives
    config.write()    
    print '                                                      '
    print '   UPDATE COMPLETED                                   '
    print '   LOCAL BACKUP IS NOW: ' + offsite_backup
    print '   OFFSITE BACKUP IS NOW: ' + local_backup
        
def output_mounted_drives():
    print '                                                      '    
    print '   CURRENT DRIVES MOUNTED                             '
        
    mounted = get_mounted_drives()[0]
    if len(mounted) == 0:
        print '   There are no drives currently mounted'
    else:
        for i, d in enumerate(mounted):
            print '   ' + str(i+1) + '. ' + d    

    print '                                                      '    
                

def output_prompt_commands():
    
    print '                                                      '
    print '   COMMANDS                                           '
    print '   1. Refresh Mounted Drives                         '
    print '   2. Synchronize Hard Drvies                         '
    print '   3. Update Wiki Pages                               '
    print '   4. Switch Local Backup and Offsite Backup         '
    print '   5. Switch Primary Drive                           '
    print '   6. Display Drive Info                             '
    print '   H or Help for help/info '
    print '   S or Settigns for Settings'
    print '   Ctrl-c To exit the program'
    command = input_command("   ENTER A COMMAND NUMBER: ", [str(x) for x in range(1,7)] + ["h", 'H', 'Help', 'help'] + ['s', 'S', 'Settings', 'settings'])
    print '                                                      '
    return command
  
def command_refresh_mounted_drives():
    output_mounted_drives()
    
def command_synchronize_hard_drives():    
    primaries = {}
    count = 0
    # Select a Primary Drive to Synchronize
    print "   PRIMARY DRIVES                                     "
    for i, drive in enumerate(hard_drives):
        if hard_drives[drive][0] == 'primary':
            count = count + 1
            print "   " + str(count) + ". " + drive
            primaries[str(count)] = drive    
    
    # Input Primary Drive
    primary = input_command("   ENTER A PRIMARY DRIVE NUMBER FOR WIKI UPDATE: ", primaries.keys())    
    if not primary == 'exit':    
        primary = primaries[primary]        
        group_letter = hard_drives[primary][2]
        local_backup = get_role_for_group(group_letter, 'local_backup')            
        print '                                                      '                
        print '   Trying to Synchronize Data on'
        print '   Primary Drive: ' + primary
        print '   To existing data on'
        print '   Local Backup Drive: ' + local_backup        
        synchronize_hard_drives(primary, local_backup) 
        
        
        msg = """Synchronization of the primary drive %s and local backup drive %s is now COMPLETED.
        thanks for using the Large File Content Management System""" % (primary, local_backup)
        
        send_email(to_email,from_email, msg)
        
    else:
        print "   Exiting Command"

def command_update_wiki_pages():
    primaries = {}
    count = 0            
    print '                                                      ' 
    print "   PRIMARY DRIVES                                     "
    for i, drive in enumerate(hard_drives):
        if hard_drives[drive][0] == 'primary':
            count = count + 1
            print "   " + str(count) + ". " + drive
            primaries[str(count)] = drive    

    primary = input_command("   ENTER A PRIMARY DRIVE NUMBER FOR WIKI UPDATE: ", primaries.keys())
    
    if not primary == 'exit':    
        primary = primaries[primary]          
        update_wiki(primary)   
    else:
        print "   Exiting Command"

def command_switch_local_backup_and_offsite_backup():
    group_letter = input_command("   ENTER A GROUP LETTER (A OR B): ", {"A", "a","B","b"})    
    if  not group_letter == 'exit':
        switch_local_backup_offsite_backup(group_letter)    
    else:
        print "   Exiting Command"

def command_switch_primary_drive():
    
    group_letter = input_command("   ENTER A GROUP LETTER (A OR B): ", {"A", "a","B","b"})    
    if  not group_letter == 'exit':
        switch_primary_drive(group_letter)    
    else:
        print "   Exiting Command"

def command_display_drives():
    print '                                                      '    
    print '   INFORMATION STORED IN SYNCHRONIZATION TOOL         '
    
    for d in hard_drives:
        print '                                                      '            
        print '   DRIVE: '+ d 
        print '   ROLE: ' + hard_drives[d][0]
        print '   MOUNT POINT: ' + hard_drives[d][1]
        print '   GROUP: ' + hard_drives[d][2]
        print '   LAST SYNCHRONIZED: ' + str(datetime.datetime.fromtimestamp(float(hard_drives[d][3])))

def command_help():
    print " HELP FOR LARGE FILE CONTENT MANAGEMENT SYSTEM"
    print 'COMMANDS:'
    print '1. Refresh Mounted Drives: refreshes/checks again which drives are currently mounted and outputs them. '
    print '2. Synchronize Hard Drvies: synchronize data from a groups primary drive to their secondary drive, will send email to designated email address when finished.  A drive listed as Primary and another as Local Backup in the same group must be mounted.  The Primary drive must have the latest modification date for this operation to carry out.'
    print '3. Update Wiki Pages: Updates wiki pages with a primary drives information. Creates pages under wiki/LargeFileContentManagementSystem/. A primary drive must be mounted to carryout this operation'
    print '4. Switch Local Backup and Offsite Backup: This switches which drive is the Local Backup and Offsite Backup.  This operation will always carry out if selected. '
    print '5. Switch Primary Drive: Switching the primary drive to either the Local Backup or Offsite Backup. The new Primary drive must have at least the latest modification date.  If operation does not take place, a synchronization and switching of drives might have to occur first before the Primary can be swapped out. This is to ensure that no data will be lost during the synchronization process.'
    print '6. Display Drive Info: Shows that each of the drives in the system is currently listed as.  Reads the configuration file for this information.'
    print 'Ctrl-c exits the program. Help can be displayed by typing h, H, help, or Help.'
    print 'While in the middle of a command you can quit the command by typing either e, E, exit, Exit, Q, q, quit, or Quit'
    print 'The Large File Content Management System was designed by Dylan Zingler, dzingler@arinc.com January 2015.'

def command_settings():
    print """
1. Email Settings

q to quit command
    """
    
    command = input_command(" Please Select A Number To Configure: ", {'1'})
    
    if command == 'exit':
        return
    else:
        # Email Configuration
        if command == str(1):
            print "Configuring Email.  An email is sent after synchronization by LFCMS"
            to = raw_input("Enter An Email Address To Send To: ")            
            while not re.match(r"[^@]+@[^@]+\.[^@]+", to):
                if to in {'e', 'Exit', 'E', 'Q', 'q', 'quit', 'Quit', 'exit'}:
                    print "Quitting Settings"
                    return   
                print "  Error Email Entered Is not Formatted correctly. Be sure to include @ sign"                
                to = raw_input("Enter An Email Address To Send To: ")
            from_ = raw_input("Enter An Email Address To Send From (Must Be an Arinc Email Address): ")
            while not (re.match(r"[^@]+@[^@]+\.[^@]+", to) and from_[-len('@arinc.com'):] == '@arinc.com'):
                if from_ in {'e', 'Exit', 'E', 'Q', 'q', 'quit', 'Quit', 'exit'}:
                    print "Quitting Settings"
                    return           
                print "  Error Email Entered Is not Formatted correctly. Be sure to include @ sign and that it is an arinc email address (@arinc.com)"                
                from_ = raw_input("Enter An Email Address To Send From (Must Be an Arinc Email Address): ")
                
             
            config['email']['to_email'] = to
            config['email']['from_email'] = from_
            config.write()    
            print "Changed To Email Address to: " + to + ' and From Email Address to: ' + from_
            
        command_settings()
        

def input_command(prompt, accepted_values):
    ''' Method for taking in input from user'''
    exit_values = {'e', 'Exit', 'E', 'Q', 'q', 'quit', 'Quit', 'exit'}
    
    value = raw_input(prompt)        
    while value not in accepted_values and value not in exit_values:
        print '                                                      '        
        print "ERROR: INPUT NOT ACCEPTED."
        print '                                                      '        
        value = raw_input(prompt) 
        
    if value in accepted_values:
        return value
    elif value in exit_values:
        return 'exit'

if __name__=="__main__":
    
    print '                                                      '
    print '  # WELCOME TO THE LARGE FILE CONTENT MANAGEMENT SYSTEM #'    
    output_mounted_drives()    
    command = output_prompt_commands()    
    
    # Command Loop
    while True:        
        if command == str(1):
            print "   SELECTED: Refresh Mounted Drives Command"
            command_refresh_mounted_drives()            
        elif command == str(2):
            print "   SELECTED: Synchronize Hard Drvies Command"
            command_synchronize_hard_drives()            
        elif command == str(3):
            print "   SELECTED: Update Wiki Pages Command"
            command_update_wiki_pages()                         
        elif command == str(4):
            print "   SELECTED: Switch Local Backup and Offsite Backup Command"
            command_switch_local_backup_and_offsite_backup()              
        elif command == str(5):
            print "   SELECTED: Switch Primary Drive Command"
            command_switch_primary_drive()        
        elif command == str(6):
            print "   SELECTED: Display Drive Info Command"            
            command_display_drives()
        elif command in {"h", 'H', 'Help', 'help'}:
            print "   SELECTED: Help"
            command_help()
        elif command in {'s', 'S', 'Settings', 'settings'}:
            print "   SELECTED: Settings"                        
            command_settings()
        else:
            print '                                                      '   
            print '   ERROR: Command not recognized. Try again'
        command = output_prompt_commands()
        