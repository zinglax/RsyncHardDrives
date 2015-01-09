import getpass
import requests
from BeautifulSoup import BeautifulSoup

class Trac_Wiki_Communicator:
    username = None
    password = None
    url = None
    cookies = None
        
    def __init__(self, *args, **kwargs):        
        '''
        Acceptable kwargs = username, password, url 
        Tries to log in and get cookies if URL is provided
        '''
        # Setting Username and Password
        if ('username' not in kwargs.keys()) and ('password' not in kwargs.keys()):        
            self.username, self.password = self.get_user_info()
        else:
            self.username = kwargs.get("username")
            self.password = kwargs.get("password")
            
        # Setting home page URL if provided, logs in and gets authentication cookies
        if ('url' in kwargs.keys()):
            self.url = kwargs.get('url')
            self.cookies = self.wiki_login()
    
    def get_user_info(self):
        '''
        This funciton gets the username and password of the user and returns
        them 
        '''
        self.username = str(raw_input("Enter Trac Username: "))
        self.password = str(getpass.getpass("Enter Trac Password: "))
        return self.username, self.password
    
    def wiki_login(self):
        '''
        Generates the authenticated cookies used to naviage pages
        '''
        print "Verifying user credentials for: " + self.username + "\n"
        r = requests.get(self.url + '/login', auth=(self.username, self.password))
        self.cookies = r.history[0].cookies
        return self.cookies
    
    def create_page(self, page_name, page_text="== TEST PAGE CREATED =="):
        '''
        Creates a wiki page at the given url
        '''        
        page_url = self.url + "/wiki/" + page_name + "?action=edit"

        print "Creating page: " + page_url + "\n"
            
        get = requests.get(page_url, cookies=self.cookies)
        self.cookies.update(get.cookies)
        form_token = BeautifulSoup(get.text).find("input", {"name": "__FORM_TOKEN"})["value"]
        version = BeautifulSoup(get.text).find("input", {"name": "version"})["value"]
        
        post_data = {
                "__FORM_TOKEN" : form_token,
                "version": version,
                "text": page_text,
                "action": "edit"
        }
    
        requests.post(page_url, post_data, cookies=self.cookies)


    def delete_page(self, page_name):
	page_url = self.url + "/wiki/" + page_name

	print "Deleting page: " + page_url + "\n"


	get = requests.get(page_url + "?action=edit", cookies=self.cookies)
	self.cookies.update(get.cookies)
	form_token = BeautifulSoup(get.text).find("input", {"name": "__FORM_TOKEN"})["value"]
	version = BeautifulSoup(get.text).find("input", {"name": "version"})["value"]

	page_url = page_url + "?action=delete&version=%s" % version

	post_data = {
                "__FORM_TOKEN" : form_token,
                "action": "delete"
        }

	requests.post(page_url, post_data, cookies=self.cookies)


if __name__=="__main__":
    usr = "dzingler"
    pwd = "dzingler"
    gatefusion = "http://10.1.10.175/projects/gatefusion"
    
    TWC = Trac_Wiki_Communicator(username=usr, password=pwd, url=gatefusion)
    TWC.create_page("LargeFileContentManagementSystem/GrpADrv2", page_text="== TEST PAGE CREATED ==")
    
    # Set brake point or uncomment
    TWC.delete_page("LargeFileContentManagementSystem/GrpADrv2")