#to read data from google sheet using service account, google sheet api
#you need to have a project in google cloud
#you need to enable google drive api
#you need to enable google sheet api
#you need service account
#you need to share folder or file to service account.


from tools.tools.gsuite import GoogleDrive
from google.oauth2 import service_account
import json

#
service_account_path = "/root/.config/gcloud/toanbui1991_service_account.json"
with open(service_account_path, "rb") as file:
    service_dict = json.load(file)
#get google sheet instance, GoogleSheet use expect authenticate using dictionary format.
drive = GoogleDrive(service_dict)
parent_id = "1Th5J2jv_ryy9RVFRYZ5Viys9if8pjxiD"
children = drive.list_children(parent_id=parent_id)
print("children: ")
print(children)
#upload file to drive
file_path = "./package_datetime.py"
drive.upload_file(file_path, parent_id)