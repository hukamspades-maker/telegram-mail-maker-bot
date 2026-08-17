import urllib.request
import json
import ssl

TOKEN = "9a5ae91c-0e69-4db5-8097-74c3f87c42cc"
PROJECT_ID = "2d6e959a-32e6-48f0-a478-b6f556bcf4b4"
SERVICE_ID = "961cc98b-643b-4689-8ade-348f12bbf478"
ENV_ID = "c0b3b623-b55b-48e6-b555-ff056e49a111"

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
    print("1️⃣ Redeploying Railway Service...")
    q1 = cf_graphql("""
        mutation serviceInstanceRedeploy($environmentId: String!, $serviceId: String!) {
            serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
        }
    """, {
        "environmentId": ENV_ID,
        "serviceId": SERVICE_ID
    })
    print("Redeploy Result:", json.dumps(q1, indent=2))

if __name__ == "__main__":
    main()
