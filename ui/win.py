from discord import ui, Interaction, ButtonStyle, Button
from discord.ext.commands import Bot

class winView(ui.View):
    def __init__(self, bot):
        self.bot: Bot = bot
        super().__init__(timeout=None)
    
    @ui.button(
        label="Accept",
        style=ButtonStyle.green,
        custom_id="asidj"
    )
    async def _accept(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        team = int(interaction.message.embeds[-1].title.split(", ")[0].replace("Team ", ""))
        id = int(interaction.message.embeds[-1].title.split(", ")[1].replace("Scrim #", ""))
        decision = True
        self.bot.dispatch("decision_made", team, id, decision, interaction)

    @ui.button(
        label="Deny",
        style=ButtonStyle.red,
        custom_id="asidjasd"
    )
    async def _deny(self, interaction: Interaction, button: Button):
        await interaction.response.defer()
        team = int(interaction.message.embeds[-1].title.split(", ")[0].replace("Team ", ""))
        id = int(interaction.message.embeds[-1].title.split(", ")[1].replace("Scrim #", ""))
        decision = False
        self.bot.dispatch("decision_made", team, id, decision, interaction)