import os
import discord
from discord import app_commands
from dotenv import load_dotenv

# You can get your Discord token for a bot on the developper portal
# https://discord.com/developers/applications
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEV_GUILD = discord.Object(id=956313821914484806)

intents = discord.Intents(messages = True, guilds = True, reactions = True)
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    # Refresh command list (remove guild when in production, may take to 1h to execute command)
    await tree.sync(guild = DEV_GUILD)
    print(f'{client.user} has connected to Discord!')

# Ping command
@tree.command(name = "ping", description = "Check if the bot is online and able to receive commands", guild = DEV_GUILD)
async def test_command(interaction):
    await interaction.response.send_message("Pong!")

# Add Rating command
@tree.command(name = "add_rating", description = "Add a movie or TV show rating to the database", guild = DEV_GUILD)
@app_commands.choices(rating = [
    app_commands.Choice(name = "Amazing", value = "⭐"),
    app_commands.Choice(name = "Good", value = "👍"),
    app_commands.Choice(name = "Meh", value = "🤷‍♂️"),
    app_commands.Choice(name = "Bad", value = "👎"),
    app_commands.Choice(name = "Terrible", value = "🗑️")
])
async def add_rating(interaction: discord.Interaction, rating: app_commands.Choice[str]):
    await interaction.response.send_message(interaction.user.name + " added a " + rating.value + " rating for a movie.")

# Make bot come online
client.run(TOKEN)