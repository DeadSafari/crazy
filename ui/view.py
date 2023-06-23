from discord import Member, ui, Interaction
from ui.select import SelectMenu

class DiscordView(ui.View):
    def __init__(self, options, user: Member, id: int):
        super().__init__(timeout=None)
        self.add_item(SelectMenu(options, id))
        self.user = user

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if not interaction.user == self.user:
            await interaction.response.send_message(":x: This is not meant for you!", ephemeral=True)
        return interaction.user == self.user