import discord
from discord.ext import commands
from databez import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.message_content = True 
intents.guilds = True
intents.members = True

GUILD_ID = 1367108374923055126  # your server ID


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = MyBot()
manager = DB_Manager(DATABASE)


@bot.event
async def on_ready():
    print(f"{bot.user} ready as Ticket Bot!")


# ----------- TICKET CREATION MODAL -----------

class TicketModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create a Ticket")

        self.title_input = discord.ui.TextInput(label="Ticket Title")
        self.desc_input = discord.ui.TextInput(
            label="Describe your problem",
            style=discord.TextStyle.paragraph
        )

        self.add_item(self.title_input)
        self.add_item(self.desc_input)

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        # Save to database
        manager.insert_ticket([(
            user.id,
            channel.id,
            self.title_input.value,
            self.desc_input.value
        )])

        await channel.send(
            f"🎫 Ticket created by {user.mention}\n\n"
            f"**{self.title_input.value}**\n"
            f"{self.desc_input.value}"
        )

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )


# ----------- TICKET DELETE SELECT -----------

class TicketDeleteSelect(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id

        tickets = manager.get_user_tickets(user_id)

        options = [
            discord.SelectOption(
                label=title,
                value=str(channel_id)
            )
            for channel_id, title in tickets
        ]

        super().__init__(
            placeholder="Select ticket to close",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = int(self.values[0])

        channel = interaction.guild.get_channel(channel_id)

        if channel:
            await channel.delete()

        manager.delete_ticket(channel_id)

        await interaction.response.send_message(
            "✅ Ticket closed and deleted.",
            ephemeral=True
        )


class TicketDeleteView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(TicketDeleteSelect(user_id))


# ----------- SLASH COMMANDS -----------

@bot.tree.command(name="ticket")
async def ticket(interaction: discord.Interaction):
    """Open a new support ticket"""
    await interaction.response.send_modal(TicketModal())


@bot.tree.command(name="close_ticket")
async def close_ticket(interaction: discord.Interaction):

    tickets = manager.get_user_tickets(interaction.user.id)

    if not tickets:
        await interaction.response.send_message(
            "You have no open tickets.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Select a ticket to close:",
        view=TicketDeleteView(interaction.user.id),
        ephemeral=True
    )


bot.run(TOKEN)
