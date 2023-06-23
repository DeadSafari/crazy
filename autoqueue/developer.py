import discord
from discord.ext import commands
import logging
import os

class DeveloperStuff(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logging.debug("DeveloperStuff is now ready!")

    @commands.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, members: commands.Greedy[discord.Member]):
        for member in members:
            await ctx.send(f"Added {member.mention} to the database!")
            await self.bot.db.execute("INSERT INTO playerData VALUES (?, ?, ?, ?, ?, ?)", (member.id, member.name, 0, 0, 0, 0))
        await self.bot.db.commit()
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def reset_db(self, ctx: commands.Context):
        os.remove("database.db")
        await self.bot.db.commit()
        await ctx.send("Done!")

async def setup(bot: commands.Bot):
    await bot.add_cog(DeveloperStuff(bot))