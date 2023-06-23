from discord.ui import View, Button

class Link(View):
    def __init__(self, url: str):
        super().__init__(timeout=10.0*60.0)

        self.add_item(
            Button(label="Click here to verify!", url=url)
        )