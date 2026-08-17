import urllib.request
import json
import ssl

TOKEN = "9a5ae91c-0e69-4db5-8097-74c3f87c42cc"
PROJECT_ID = "2d6e959a-32e6-48f0-a478-b6f556bcf4b4"

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
    print("1️⃣ Querying All Railway Deployments...")
    q1 = cf_graphql("""
        query deployments($input: DeploymentListInput!) {
            deployments(input: $input) {
                edges {
                    node {
                        id
                        status
                        createdAt
                    }
                }
            }
        }
    """, {
        "input": {
            "projectId": PROJECT_ID
        }
    })
    print("Deployments:", json.dumps(q1, indent=2))

if __name__ == "__main__":
    main()
