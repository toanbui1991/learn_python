#to read data from google sheet using service account, google sheet api
#you need to have a project in google cloud
#you need to enable google drive api
#you need to enable google sheet api
#you need service account
#you need to share folder or file to service account.


from tools.tools.gsuite import GoogleSheet
from google.oauth2 import service_account
import json

#
service_account_path = "/root/.config/gcloud/toanbui1991_service_account.json"
with open(service_account_path, "rb") as file:
    service_dict = json.load(file)
sheet_id = "1s4Z6IW4L2Lf1s0JD16iDq6E3VC8K3qhmWWEFrAGqYVE"
#get google sheet instance, GoogleSheet use expect authenticate using dictionary format.
sheet = GoogleSheet(service_dict, sheet_id=sheet_id)
#loop through all sheet of sheet_book
for s in sheet:
    print(s.get_values())
    print("new")

#get value of active sheet
values = sheet.get_values()
print("values: ", values)
data = sheet.get_values_as_df()
print("data: ")
print(data)