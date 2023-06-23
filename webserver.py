from quart import Quart, render_template, request
import aiohttp


app = Quart("HL RBW")

@app.route("/")
async def index():
    return "Hello, World"

@app.route("/verify")
async def oauth():
    data = {
        'grant_type': 'client_credentials',
        'scope': 'identify connections'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers, auth=aiohttp.BasicAuth('1092182388496400384', "64BjXSpww6TSUeuz6UqQuOnJaPfFxivR")) as r:
            resp = await r.json()
            headers = {
                "Authorization": "Bearer "+resp["access_token"]
            }
            async with session.get("https://discord.com/api/v10/users/@me/connections", headers=headers) as req:
                req = await req.json()
                app.bot.dispatch("verify_clicked", request.args.get("state"), req)
    return render_template("index.html")

async def run_server(bot):
    app.bot = bot
    await app.run_task(
        host="0.0.0.0",
        port=5000
    )