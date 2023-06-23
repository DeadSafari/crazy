from os import getenv
from time import time
from discord.ext.commands import Bot, Cog
from discord import app_commands, Interaction, Embed, Color, Member, Attachment
from string import ascii_letters
from random import choice
from re import match
from json import dump, dumps, loads, load
from shutil import copyfile
from ui.link import Link
from ui.win import winView

class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot

    guild_id = int(getenv("MAIN_GUILD_ID"))

    elo = app_commands.Group(
        name="elo",
        description="Commands related to elo",
        guild_ids=[guild_id],
        guild_only=True
    )

    scrims = app_commands.Group(
        name="scrims",
        description="Commands related to scrims",
        guild_ids=[guild_id],
        guild_only=True
    )

    season = app_commands.Group(
        name="season",
        description="Commands related to seasons",
        guild_ids=[guild_id],
        guild_only=True
    )

    def calculate_elo(self, elo):
        if elo in range(0, 100):
            return 30*self.bot.multiplier, 5*self.bot.multiplier
        elif elo in range(100, 150):
            return 20*self.bot.multiplier, 10*self.bot.multiplier
        elif elo >= 150:
            return 10*self.bot.multiplier, 10*self.bot.multiplier

    async def give_elo(self, member: Member, elo: int):
        cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (member.id,))
        data = await cursor.fetchone()
        if not data:
            raise KeyError(f"{member.id} is not in the database!")
        if elo > 0:
            await self.bot.db.execute("UPDATE playerData SET wins = ? WHERE id = ?", (int(data[4]) + 1, member.id,))
            await self.bot.db.execute("UPDATE playerData SET games = ? WHERE id = ?", (int(data[3]) + 1, member.id,))
            await self.bot.db.execute("UPDATE playerData SET elo = ? WHERE id = ?", (int(data[2]) + int(elo), member.id,))
        elif elo < 0:
            eloToGive = data[2] + int(elo)
            if eloToGive <= 0:
                eloToGive = 0
            await self.bot.db.execute("UPDATE playerData SET games = ? WHERE id = ?", (int(data[3]) + 1, member.id,))
            await self.bot.db.execute("UPDATE playerData SET losses = ? WHERE id = ?", (int(data[4]) + 1, member.id,))
            await self.bot.db.execute("UPDATE playerData SET elo = ? WHERE id = ?", (eloToGive, member.id,))
        await self.bot.db.commit()

    async def give_elo_cmd(self, member: Member, elo: int):
        cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (member.id,))
        data = await cursor.fetchone()
        if not data:
            raise KeyError(f"{member.id} is not in the database!")
        if elo > 0:
            await self.bot.db.execute("UPDATE playerData SET elo = ? WHERE id = ?", (int(data[2]) + int(elo), member.id,))
        elif elo < 0:
            eloToGive = data[2] + int(elo)
            if eloToGive <= 0:
                eloToGive = 0
            await self.bot.db.execute("UPDATE playerData SET elo = ? WHERE id = ?", (eloToGive, member.id,))
        await self.bot.db.commit()
        return elo + data[2], data[1]



    @Cog.listener()
    async def on_decision_made(self, team: int, id: int, decision: bool, interaction: Interaction):
        cursor = await self.bot.db.execute("SELECT * FROM scrims WHERE id = ?", (id,))
        data = await cursor.fetchone()
        if not decision:
            txt = int(data[2])
            txt = self.bot.get_channel(txt)
            await txt.send(f":x: {interaction.user.mention}, your game winning request has been denied!")
            await interaction.message.edit(view=None)
            return

        await self.bot.db.execute("UPDATE scrims SET status = ?, ended = ?, winner = ?, loser = ? WHERE id = ?", (1, int(time()), team, 1 if team == 0 else 0, id,))
        await self.bot.db.commit()
        
        try:
            await interaction.message.edit(view=None)
        except:
            pass
        
        txt = int(data[2])
        txt = self.bot.get_channel(txt)
        if not txt:
            try:
                txt = await interaction.guild.fetch_channel(int(data[2]))
            except:
                await interaction.channel.send(":x: The text channel for this scrim has been deleted! Continuing anyways!")

        captain = int(data[8]) if team == 1 else int(data[9])
        await txt.send(f":white_check_mark: {interaction.guild.get_member(captain)}, your game winning request has been accepted!") if txt else print()
        await txt.send(f"Team {team} won!") if txt else print()
        
        if team == 1:
            players = loads(data[6])
            otherTeamPlayers = loads(data[7])
        elif team == 2:
            players = loads(data[7])
            otherTeamPlayers = loads(data[6])
        
        for player in players:
            cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (player,))
            data = await cursor.fetchone()
            member = interaction.guild.get_member(player)
            win, _ = self.calculate_elo(data[2])
            await self.give_elo(member, win)
            
            cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (player,))
            data = await cursor.fetchone()
            try:
                await member.edit(nick=f"[{data[2]}] {data[1]}")
            except:
                pass
        
        for player in otherTeamPlayers:
            cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (player,))
            data = await cursor.fetchone()
            member = interaction.guild.get_member(player)
            win, loss = self.calculate_elo(data[2])
            await self.give_elo(member, -loss)
            try:
                cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = ?", (player,))
                data = await cursor.fetchone()
                await member.edit(nick=f"[{data[2]}] {data[1]}")
            except:
                pass

        vc2 = int(data[4])
        vc3 = int(data[5])
        vc2 = self.bot.get_channel(vc2)
        try:
            await vc2.delete()
        except:
            pass
        try:
            await vc3.delete()
        except:
            pass


    @Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Commands is now ready!")
        self.bot.add_view(winView(self.bot))

    @app_commands.command()
    @app_commands.guilds(744228348703801394)
    async def verify(self, interaction: Interaction, ign: str):
        result_str = ''.join(choice(ascii_letters) for i in range(32))
        embed = Embed(
            title="Verification",
            color=Color.red(),
            description="In order to start playing Ranked Bedwars, you need to verify your account. Please click [here](https://discord.com/api/oauth2/authorize?client_id=1092182388496400384&redirect_uri=http%3A%2F%2Fhl.rbw.deadsafari.me%3A6969%2Fverify&response_type=code&scope=identify%20connections&state="+result_str+") to verify your account.",
        )
        embed.set_footer(
            text="Please note that verifying may take upto a minute to register. This message will be edited once you have verified your account."
        )

        view = Link("https://discord.com/api/oauth2/authorize?client_id=1092182388496400384&redirect_uri=http%3A%2F%2Fhl.rbw.deadsafari.me%3A6969%2Fverify&response_type=code&scope=identify%20connections&state="+result_str)
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

        def check(state, request):
            if state != result_str:
                return False
            return True
        
        _, __ = await self.bot.wait_for("verify_clicked", check=check, timeout=float(60.0*10.0))
        
        cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = (?)", (interaction.user.id,))
        data = await cursor.fetchone()
        if not data:
            await self.bot.db.execute("INSERT INTO playerData VALUES (?, ?, ?, ?, ?, ?)", (interaction.user.id, ign, 0, 0, 0, 0,))
            await self.bot.db.commit()
        else:
            await self.bot.db.execute("UPDATE playerData SET name = ? WHERE id = ?", (ign, interaction.user.id,))
            await self.bot.db.commit()
        
        embed = Embed(
            description=f"You have now successfully been verified as `{ign}`!",
            color=Color.green()
        )
        await interaction.edit_original_response(embed=embed, content="", view=None)
        try:
            await interaction.user.edit(nick=f"[{data[2]}] {ign}")
        except:
            pass

    @scrims.command(
        name="ping",
        description="Pings the scrims role."
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    async def _ping(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer()
        await interaction.channel.send(content=f"<@&{getenv('SCRIMS_ROLE_ID')}>")
        await interaction.followup.send("Done! :white_check_mark:", ephemeral=True)

    @app_commands.command(
        name="win",
        description="Request to win a game.",
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    @app_commands.describe(attachment="The first screenshot", attachment2="The second screenshot", attachment3="The third screenshot")
    @app_commands.guilds(744228348703801394)
    async def _win(
        self,
        interaction: Interaction,
        attachment: Attachment,
        attachment2: Attachment,
        attachment3: Attachment
    ):
        await interaction.response.defer()
        cursor = await self.bot.db.execute("SELECT * FROM scrims WHERE txt = (?)", (interaction.channel.id,))
        data = await cursor.fetchone()
        data = list(data)

        captains = [int(data[8]), 958390293760184392]
        # captains = [int(data[8]), int(data[9])]

        if not data:
            return await interaction.edit_original_response(content=f":x: This is not a scrims channel!")
        if not interaction.user.id in captains:
            return await interaction.edit_original_response(content=f":x: You are not the captain of this team!")
        if data[10] == 1:
            return await interaction.edit_original_response(content=f":x: This scrim has already ended!")
        
        team = 1 if data[8] == interaction.user.id else 2

        channelForSs = self.bot.get_channel(int(getenv("EVIDENCE_CHANNEL_ID")))
        embed = Embed(
            title=f"Team {team}, Scrim #{interaction.channel.name.split('-')[-1]}",
            color=Color.red()
        )
        embedForImage1 = Embed(color=Color.red())
        embedForImage1.set_image(url=attachment.url)
        embedForImage2 = Embed(color=Color.red())
        embedForImage2.set_image(url=attachment2.url)
        embedForImage3 = Embed(color=Color.red())
        embedForImage3.set_image(url=attachment3.url)
        view = winView(self.bot)
        await channelForSs.send(embeds=[embedForImage1, embedForImage2, embedForImage3, embed], view=view)
        await interaction.followup.send(":white_check_mark: Your request has successfully been submitted. Please wait for your proof to be accepted, in the meantime feel free to queue again.")

    @elo.command(
        name="add",
        description="Add elo to a member."
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    @app_commands.describe(member="The member to change the elo of.", amount="The amount of elo to add. Use negative numbers to remove elo.")
    async def _add(
        self,
        interaction: Interaction,
        member: Member,
        amount: int
    ):
        await interaction.response.defer()
        elo, ign = await self.give_elo_cmd(member, amount)
        try:
            await member.edit(nick=f"[{elo}] {ign}")
        except:
            pass
        await interaction.followup.send(content=f":white_check_mark: Successfully added {amount} elo to {member.mention}!")

    @elo.command(
        name="multiplier",
        description="Add a multiplier to the server."
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    @app_commands.describe(multiplier="The multiplier to add.")
    async def _multiplier(
        self, 
        interaction: Interaction,
        multiplier: str
    ):
        await interaction.response.defer()
        if not match(r"^\d+(\.\d+)?$", multiplier):
            return await interaction.followup.send(contnet=":x: The input must be a valid integer/float!", ephemeral=True)
        multiplier = float(multiplier)
        with open("multiplier.json", "r") as f:
            multipliers = load(f)
        multipliers[str(interaction.guild.id)] = multiplier
        with open("multiplier.json", "w") as f:
            dump(multipliers, f, indent=4)
        self.bot.multiplier = multiplier
        await interaction.followup.send(content=f":white_check_mark: Successfully set the multiplier to {multiplier}!")

    @app_commands.command(
        name="profile",
        description="View your profile."
    )
    @app_commands.guilds(744228348703801394)
    async def _profile(
        self,
        interaction: Interaction,
        member: Member = None
    ):
        await interaction.response.defer()
        member = interaction.user if not member else member
        cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = (?)", (member.id,))
        data = await cursor.fetchone()
        if not data:
            return await interaction.followup.send(content=":x: You are not verified!", ephemeral=True)
        embed = Embed(
            title=f"{member.name}'s Profile",
            color=Color.red()
        )
        embed.add_field(name="IGN", value=data[1], inline=True)
        embed.add_field(name="Elo", value=data[2], inline=True)
        embed.add_field(name="Wins", value=data[3], inline=True)
        embed.add_field(name="Losses", value=data[4], inline=True)
        embed.add_field(name="Games Played", value=data[5], inline=True)
        try:
            embed.add_field(name="Winrate", value=f"{round(data[3]/data[-1]*100)}%", inline=True)
        except ZeroDivisionError:
            embed.add_field(name="Winrate", value="0%")
        embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.followup.send(embed=embed)
        
    @scrims.command(
        name="sub",
        description="Substitue a player in a scrim."
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    async def _sub(
        self,
        interaction: Interaction,
        member: Member,
        sub: Member
    ):
        await interaction.response.defer()
        data = await self.bot.db.execute("SELECT * FROM banned_users WHERE id = ?", (sub.id,))
        data = await data.fetchone()
        if data:
            return await interaction.response.send_message(f":x: {sub.mention} is banned from scrims!", ephemeral=True)
        data = await self.bot.db.execute("SELECT * FROM scrims WHERE id = ?", (interaction.channel.id,))
        data = await data.fetchone()
        if not data:
            return await interaction.response.send_message(":x: This is not a scrim channel!", ephemeral=True)
        players = loads(data[1])
        if not member.id in players:
            return await interaction.response.send_message(":x: This player is not in the scrim!", ephemeral=True)
        if sub.id in players:
            return await interaction.response.send_message(":x: This player is already in the scrim!", ephemeral=True)
        players[players.index(member.id)] = sub.id
        await self.bot.db.execute("UPDATE scrims SET players = ? WHERE id = ?", (dumps(players), interaction.channel.id))
        await self.bot.db.commit()
        await interaction.response.send_message(f":white_check_mark: Successfully subbed {member.mention} with {sub.mention}!")

    @season.command(
        name="reset",
        description="Reset the stats for a new season."
    )
    @app_commands.checks.has_role(int(getenv("HOST_ROLE_ID")))
    async def _reset(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer()
        await self.bot.db.execute("UPDATE playerData SET wins = 0, losses = 0, games = 0")
        copyfile("database.db", "seasons/season1.db")
        await self.bot.db.commit()
        await interaction.followup.send(content=":white_check_mark: Successfully reset the stats!")

async def setup(bot: Bot):
    await bot.add_cog(Commands(bot))