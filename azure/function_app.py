import azure.functions as func
import json
import random
import string
import os
from azure.cosmos import CosmosClient

app = func.FunctionApp()

COSMOS_URL = os.environ["COSMOS_URL"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
DATABASE = "url-shortener"
CONTAINER = "urls"

client = CosmosClient(COSMOS_URL, COSMOS_KEY)
container = client.get_database_client(DATABASE).get_container_client(CONTAINER)

def generate_short_code():
    # 6 chars is enough to avoid collisions at small scale
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=6))

@app.route(route="shorten", methods=["POST"])
def shorten_url(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    long_url = body.get("long_url")

    if not long_url:
        return func.HttpResponse(
            json.dumps({"error": "long_url is required"}),
            status_code=400
        )

    short_code = generate_short_code()

    # store the mapping in cosmos
    container.upsert_item({
        "id": short_code,
        "long_url": long_url
    })

    return func.HttpResponse(
        json.dumps({
            "short_code": short_code,
            "short_url": f"https://urlshortenerfn-f5cdbgc6bbcwc0bd.westus2-01.azurewebsites.net/api/{short_code}"
        }),
        status_code=200
    )

@app.route(route="{short_code}", methods=["GET"])
def redirect_url(req: func.HttpRequest) -> func.HttpResponse:
    short_code = req.route_params.get("short_code")

    try:
        item = container.read_item(item=short_code, partition_key=short_code)
        return func.HttpResponse(
            status_code=301,
            headers={"Location": item["long_url"]}
        )
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "URL not found"}),
            status_code=404
        )