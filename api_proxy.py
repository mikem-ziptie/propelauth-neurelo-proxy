from fastapi import FastAPI, Request, HTTPException
import uvicorn
import httpx
import os
from propelauth_py import init_base_auth
from propelauth_py import UnauthorizedException


class APIProxy:
    def __init__(self):
        self.auth = init_base_auth(
            os.getenv("PROPEL_AUTH_URL"),
            os.getenv("PROPEL_AUTH_API_KEY"),
        )
        print("os.getenv(PROPEL_AUTH_URL)", os.getenv("PROPEL_AUTH_URL"))
        print("os.getenv(PROPEL_AUTH_API_KEY)", os.getenv("PROPEL_AUTH_API_KEY"))
        self.forward_domain = os.getenv("NEURELO_URL")
        self.additional_header_name = "X-API-KEY"
        self.additional_header_value = os.getenv("NEURELO_API_KEY")

    async def forward_request(self, request: Request, path: str):

        auth_header = request.headers.get("Authorization")
        try:
            user = self.auth.validate_access_token_and_get_user(auth_header)
            print("Logged in as", user.user_id)
        except UnauthorizedException:
            print("Invalid access token")
            raise HTTPException(status_code=401, detail="Invalid access token")

        forward_url = f"{self.forward_domain}/{path}"
        headers = {key: value for key, value in request.headers.items()}
        headers[self.additional_header_name] = self.additional_header_value
        print("Request url", forward_url)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=forward_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params,
            )
        print("Response.text", response.text[:240], "...")
        print("Response.status_code", response.status_code)
        print("Response.headers", response.headers)
        return response.text, response.status_code, response.headers.items()


app = FastAPI()
api_proxy = APIProxy()


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(request: Request, path: str):
    return await api_proxy.forward_request(request, path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
