import requests

USER_ID = "38056054-049b-4ad2-8929-82dc0ca985d0"
url = f"https://www.credly.com/api/v1/users/{USER_ID}/external_badges/open_badges/public?page=1&page_size=48"

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
print(r.status_code)
print(r.text[:500])