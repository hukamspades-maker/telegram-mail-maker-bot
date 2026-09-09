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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
    print("1️⃣ Updating DEFAULT_DOMAINS on Railway...")
    q1 = cf_graphql("""
        mutation variableCollectionUpsert($input: VariableCollectionUpsertInput!) {
            variableCollectionUpsert(input: $input)
        }
    """, {
        "input": {
            "projectId": PROJECT_ID,
            "environmentId": ENV_ID,
            "serviceId": SERVICE_ID,
            "variables": {
                "BOT_TOKEN": "8985612343:AAGy2ihloKSeND_Oq0Iy2feqpbBpIUBGqsY",
                "ADMIN_IDS": "8603872187",
                "DEFAULT_DOMAINS": "hukam.bond,jattjames.bond",
                "DATABASE_PATH": "/app/data/mail_bot.db",
                "NIXPACKS_NO_CACHE": "1"
            }
        }
    })
    print("Railway Variable Upsert Result:", json.dumps(q1, indent=2))

    print("\n2️⃣ Triggering Deployment...")
    q2 = cf_graphql("""
        mutation serviceInstanceDeploy($environmentId: String!, $serviceId: String!) {
            serviceInstanceDeploy(environmentId: $environmentId, serviceId: $serviceId)
        }
    """, {
        "environmentId": ENV_ID,
        "serviceId": SERVICE_ID
    })
    print("Railway Deploy Result:", json.dumps(q2, indent=2))

if __name__ == "__main__":
    main()
