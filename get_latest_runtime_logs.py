import urllib.request
import json
import ssl

TOKEN = "9a5ae91c-0e69-4db5-8097-74c3f87c42cc"
DEPLOYMENT_ID = "e10f276a-4f19-42e2-bcd9-b5ff6776751c"

URL = "https://backboard.railway.app/graphql/v2"

ctx = ssl._create_unverified_context()

def cf_graphql(query, variables=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode('utf-8')}

def main():
    print(f"Fetching Container Runtime Logs for {DEPLOYMENT_ID}...")
    q1 = cf_graphql("""
        query deploymentLogs($deploymentId: String!) {
            deploymentLogs(deploymentId: $deploymentId, limit: 50) {
                timestamp
                message
            }
        }
    """, {
        "deploymentId": DEPLOYMENT_ID
    })
    print("Logs:", json.dumps(q1, indent=2))

if __name__ == "__main__":
    main()
