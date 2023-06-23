from discord import ui, Interaction

class DiscordView(ui.Select):
    def __init__(self, options, id: int):
        self.id: int = id

        super().__init__(
            custom_id="persistent:select",
            placeholder="Please select a member",
            options=options,
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(":white_check_mark: Member selected!")
        self.disabled = True
        await interaction.message.edit(view=self.view)
        interaction.client.dispatch("member_selected", self.values[0], self.id)