from discord.ext.commands import Bot
from discord import Intents, Status, Game, Object
from discord.utils import setup_logging
from os import getenv, listdir
from dotenv import load_dotenv
from logging import getLogger
from asyncio import run
from json import load
from webserver import run_server
from threading import Thread
from aiosqlite import Connection, connect
from traceback import print_exc

class Bot(Bot):
    def __init__(self):

        intents = Intents.none()
        intents.members = True
        intents.voice_states = True
        intents.guilds = True
        intents.message_content = True
        intents.guild_messages = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            status=Status.dnd,
            acitvity=Game(name="RBW"),
            chunk_guilds_at_startup=False
        )

        self.token: str = getenv("TOKEN")
        
        self.logger = getLogger("bot")

        self.main_guild_id: int = int(getenv("MAIN_GUILD_ID"))

        self.multiplier: float = load(open("mutliplier.json", "r"))['multiplier'] 

    def __str__(self) -> str:
        return self.token
    
    async def load_cogs(self):
        # for cog in listdir("./moderation"):
        #     if not cog.endswith(".py"):
        #         continue
        #     try:
        #         await self.load_extension(f"moderation.{cog[:-3]}")
        #     except:
        #         self.logger.error("Failed to load cog {cog}")
        #         print_exc()

        for cog in listdir("./autoqueue"):
            if not cog.endswith(".py"):
                continue
            try:
                await self.load_extension(f"autoqueue.{cog[:-3]}")
            except:
                self.logger.error("Failed to load cog {cog}")
                print_exc()

        for cog in listdir("./database"):
            if not cog.endswith(".py"):
                continue
            try:
                await self.load_extension(f"database.{cog[:-3]}")
            except:
                self.logger.error("Failed to load cog {cog}")
                print_exc()
        
                    
    async def on_connect(self):
        await self.tree.sync(
            guild=Object(id=self.main_guild_id)
        )

    async def on_ready(self):
        self.logger.info("===============================================")
        self.logger.info("Logged in as:")
        self.logger.info(f"Bot Name: {str(self.user)}")
        self.logger.info(f"Bot ID: {self.user.id}")
        self.logger.info(f"Bot Users: {len(self.users)}")
        self.logger.info("===============================================")

    async def start(self):
        await super().start(self.token, reconnect=True)
        
    async def on_connect(self):
        self.con: Connection = await connect("db.sqlite")
        await self.load_cogs()
        await self.tree.sync(guild=Object(id=self.main_guild_id))

async def main():
    load_dotenv()
    setup_logging()
    bot = Bot()
    thread = Thread(target=run, args=[bot.start()])
    thread.start()
    await run_server(bot)

if __name__ == "__main__":
    run(main())