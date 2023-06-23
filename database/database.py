import aiosqlite
from discord.ext.commands import Cog, Bot
import logging
from discord import Member

class Database(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.db: aiosqlite.Connection = None

    @Cog.listener()
    async def on_ready(self):
        self.db = await aiosqlite.connect("database.db")
        self.bot.db = self.db
        await self.bot.db.execute("""
        CREATE TABLE IF NOT EXISTS scrims (
        id INTEGER,
        players TEXT,
        txt INTEGER,
        vc1 INTEGER,
        vc2 INTEGER,
        vc3 INTEGER,
        team1 TEXT,
        team2 TEXT,
        team1Captain INTEGER,
        team2Captain INTEGER,
        status INTEGER,
        started INTEGER,
        ended INTEGER,
        winner INTEGER,
        loser INTEGER
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS count (
        count INTEGER
        )
        """)
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS playerData (
        id INTEGER,
        name TEXT,
        elo INTEGER,
        wins INTEGER,
        losses INTEGER,
        games INTEGER
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER,
        time INTEGER,
        reason TEXT
        )
        """)

        cursor = await self.db.execute("SELECT * FROM count")
        data = await cursor.fetchone()
        if not data:
            await self.db.execute("INSERT INTO count VALUES (1)")
            await self.db.commit()

        await self.db.commit()


        logging.info("Database is now ready!")


async def setup(bot: Bot):
    database = Database(bot)
    database.db = await aiosqlite.connect("database.db")
    database.bot.db = database.db
    await bot.add_cog(database)