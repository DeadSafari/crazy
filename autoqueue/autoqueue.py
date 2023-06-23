from json import dumps
from time import time
from discord.ext.commands import Bot, Cog
from discord import Interaction, Member, VoiceState, VoiceChannel, PermissionOverwrite, Embed, Color, ui, SelectOption
import logging
from os import getenv
from ui.select import DiscordView

class Autoqueue(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.autoqueue_channel_id: int = int(getenv("AUTOQUEUE_CHANNEL_ID"))

    @Cog.listener()
    async def on_ready(self):
        cursor = await self.bot.db.execute("SELECT * FROM banned_users")
        data = await cursor.fetchall()
        for row in data:
            if row[1] < time():
                await self.bot.db.execute("DELETE FROM banned_users WHERE user_id = ?", (row[0],))
        await self.bot.db.commit()
        logging.info("Autoqueue is now ready!")

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        # if member.bot:
        #     logging.debug("member is bot")
            # return
        if not after.channel:
            return
        if after.channel.id != self.autoqueue_channel_id:
            return
        if before.channel:
            if before.channel.id == self.autoqueue_channel_id:
                return
            return
        
        if isinstance(after.channel, VoiceChannel):
            banned_user = await self.bot.db.execute("SELECT * FROM banned_users WHERE user_id = ?", (member.id,))
            banned_user = await banned_user.fetchone()
            if banned_user:
                await member.move_to(None, reason="Banned from scrimming!")
                return
            if len(after.channel.members) == 8:

                members = after.channel.members
                guild = member.guild
                cursor = await self.bot.db.execute("SELECT * FROM count")
                data = await cursor.fetchone()
                count = data[0]
                await self.bot.db.execute("UPDATE count SET count = ? WHERE count = ?", (data[0]+1, data[0],))
                await self.bot.db.commit()

                category = self.bot.get_channel(int(getenv("AUTOQUEUE_CATEGORY_ID")))

                overwrites = {
                    member.guild.default_role: PermissionOverwrite(view_channel=False)
                }
                vcOverwrites = {
                    member.guild.default_role: PermissionOverwrite(view_channel=True, connect=False)
                }
                for member in members:
                    overwrites[member] = PermissionOverwrite(view_channel=True, send_messages=True, add_reactions=True)
                    vcOverwrites[member] = PermissionOverwrite(view_channel=True, connect=True, speak=True)

                txt = await category.create_text_channel(
                    name=f"game-{count}",
                    overwrites=overwrites,
                    reason="Scrim Channel"
                )

                vc = await category.create_voice_channel(
                    name=f"Teaming game #{count}",
                    user_limit=8,
                    overwrites=vcOverwrites,
                    reason="Scrim Channel"
                )

                vc2 = await category.create_voice_channel(
                    name=f"Team 1 game #{count}",
                    user_limit=4,
                    overwrites=vcOverwrites,
                    reason="Scrim Channel"
                )
                
                vc3 = await category.create_voice_channel(
                    name=f"Team 2 game #{count}",
                    user_limit=4,
                    overwrites=vcOverwrites,
                    reason="Scrim Channel"
                )


                for member in after.channel.members:
                    try:
                        await member.move_to(vc)
                    except:
                        pass

                membersWithElo = {}

                for member in members:
                    cursor = await self.bot.db.execute("SELECT * FROM playerData WHERE id = (?)", (member.id,))
                    data = await cursor.fetchone()
                    membersWithElo[member.id] = data[2]

                sorted_dict = dict(sorted(membersWithElo.items(), key=lambda x: x[1]), reverse=True)

                t1c = list(sorted_dict.keys())[0]
                t2c = list(sorted_dict.keys())[1]

                embed = Embed(
                    title=f"HL RBW Game#{count}",
                    description=f"Two captains have been picked;\nTeam 1: <@!{t1c}>\nTeam 2: <@!{t2c}>",
                    color=Color.blue()
                )
                mentions = [member.mention for member in members]

                options = []
                newMembers = members
                t1cMember = member.guild.get_member(t1c)
                t2cMember = member.guild.get_member(t2c)
                newMembers.remove(t1cMember)
                newMembers.remove(t2cMember)
                t1 = []
                t2 = []
                await txt.send(embed=embed, content=", ".join(mentions))


                while True:
                    options = []
                    for member in newMembers:
                        options.append(
                            SelectOption(
                            label=member.name,
                            value=member.id
                        )
                    )
                    if newMembers == []: break
                    view = DiscordView(options, t1cMember, count)
                    await txt.send(content=f"<@!{t1c}> please choose the member with the Select Menu below:", view=view)

                    def check(member, id):
                        return id == count
                    member, id = await self.bot.wait_for("member_selected", check=check)

                    await txt.send(f"<@!{member}> has been picked by <@!{t1c}>")
                    t1.append(int(member))
                    newMembers.remove(guild.get_member(int(member)))

                    options = []
                    for member in newMembers:
                        options.append(
                            SelectOption(
                            label=member.name,
                            value=member.id
                            )
                        )
        
                    view = DiscordView(options, t2cMember, count)

                    await txt.send(content=f"<@!{t2c}> please choose the member with the Select Menu below:", view=view)
                    
                    member, id = await self.bot.wait_for("member_selected", check=check)

                    await txt.send(f"<@!{member}> has been picked by <@!{t2c}>")

                    t2.append(int(member))
                    newMembers.remove(guild.get_member(int(member)))
                t1.append(t1cMember.id)
                t2.append(t2cMember.id)
                playersIDs = t1 + t2
                players = dumps(playersIDs)

                team1 = dumps(t1)
                team2 = dumps(t2)
                await self.bot.db.execute(
                    """INSERT INTO scrims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (count, players, txt.id, vc.id, vc2.id, vc3.id, team1, team2, t1c, t2c, 0, int(time()), 0, 0, 0,)
                )
                await self.bot.db.commit()
                
                embed = Embed(
                    title="Teams have been picked!",
                    description=f"Team 1: {', '.join([guild.get_member(member).mention for member in t1])}\nTeam 2: {', '.join([guild.get_member(member).mention for member in t2])}",
                    color=Color.blue()
                )
                await txt.send(embed=embed)
                for member in vc.members:
                    if member.id in t1:
                        try:
                            await member.move_to(vc2)
                        except:
                            pass
                    elif member.id in t2:
                        try:
                            await member.move_to(vc3)
                        except:
                            pass
                await vc.delete()
                await txt.send(content="Once you're done with your game, please run /win and upload screenshots of you winning the rounds.")
                

async def setup(bot: Bot):
    autoqueue = Autoqueue(bot)
    await bot.add_cog(autoqueue)