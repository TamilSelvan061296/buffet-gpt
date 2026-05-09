import requests

endpoint = 'http://localhost:8080/chat'
payload = {"session_id":"123", 
           "message":"What is the single most thing that you regret?"}
response = requests.post(url=endpoint, json=payload)
print(response.text)