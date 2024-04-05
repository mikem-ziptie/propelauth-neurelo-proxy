from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

FORWARD_DOMAIN = "https://us-west-2.aws.neurelo.com"
ADDITIONAL_HEADER_NAME = 'X-API-KEY'
ADDITIONAL_HEADER_VALUE = os.getenv('NEURELO_API_KEY')

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(request: Request, path: str):
    forward_url = f"{FORWARD_DOMAIN}/{path}"
    headers = {key: value for key, value in request.headers.items()}
    headers[ADDITIONAL_HEADER_NAME] = ADDITIONAL_HEADER_VALUE

    async with requests.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=forward_url,
            headers=headers,
            content=await request.body(),
            params=request.query_params
        )

    return response.text, response.status_code, response.headers.items()

