import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. GET to grab CSRF token
response = opener.open('http://127.0.0.1:8000/accounts/login/')
csrftoken = ""
for cookie in cj:
    if cookie.name == 'csrftoken':
        csrftoken = cookie.value
        break

# 2. POST to login
data = urllib.parse.urlencode({
    'login': 'debugadmin',
    'password': 'DebugPass123!',
    'csrfmiddlewaretoken': csrftoken
}).encode('utf-8')

request = urllib.request.Request('http://127.0.0.1:8000/accounts/login/', data=data)
request.add_header('Referer', 'http://127.0.0.1:8000/accounts/login/')

try:
    post_resp = opener.open(request)
    print("STATUS AFTER SUCCESSFUL LOGIN:", post_resp.status)
    print("CURRENT URL:", post_resp.geturl())
    html = post_resp.read().decode('utf-8')
    if "error" in html.lower() or "exception" in html.lower():
        print("POSSIBLE ERROR IN HTML!")
    print(html[:500])
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print("OTHER ERROR:", str(e))
