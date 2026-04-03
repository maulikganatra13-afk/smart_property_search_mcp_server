import requests


LOGIN_URL = "https://www.themls.com/CLAW.Security.AuthServer/Account/Login"
USERNAME = "C145296"
PASSWORD = "C145296MG"


payload = {
    "account_key": "",
    "auth_legacy": True,
    "legacy": True,
    "trackUser": True,
    "accessUrl": "memberdashboard",
    "username": USERNAME,
    "password": PASSWORD,
    "scheme": ""
}

session = requests.Session()

response = session.post(LOGIN_URL, json=payload)

print("Login status:", response.status_code)

# --------------------------------
# CALL MLS API
# --------------------------------
url = "https://www.themls.com/MlsListingAPI/api/Search/ListingSearchElastic"

payload = {
    "searchType": "QCK",
    "criterias": [
        {"field": "Status", "value1": 5},
        {"field": "City", "value1": "Beverly Hills"}
    ]
}

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.themls.com",
    "Referer": "https://www.themls.com/"
}

response = session.post(url, json=payload, headers=headers)

print(response.status_code,"\n\n\n\n")
print(response.text[:1000])