import os
import discord
import pymongo
import certifi
from discord import app_commands
from dotenv import load_dotenv

# You can get your Discord token for a bot on the developper portal
# https://discord.com/developers/applications
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CONNECTION_STRING = os.getenv('DB_CONNECTION_STR')
DEV_GUILD = discord.Object(id=956313821914484806)

intents = discord.Intents(messages = True, guilds = True, reactions = True)
bot_client = discord.Client(intents = intents)
tree = app_commands.CommandTree(bot_client)

# Connect to database
ca = certifi.where()
db_client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile = ca)
db_collection = db_client["MovRater"]["ratings"]

@bot_client.event
async def on_ready():
    # Refresh command list (remove guild when in production, may take to 1h to execute command)
    await tree.sync(guild = DEV_GUILD)
    print(f'{bot_client.user} has connected to Discord!')

# Ping command
@tree.command(name = "ping", description = "Check if the bot is online and able to receive commands", guild = DEV_GUILD)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# Add rating command
@tree.command(name = "add_rating", description = "Add a movie or TV show rating to the database", guild = DEV_GUILD)
@app_commands.choices(rating = [
    app_commands.Choice(name = "Amazing", value = "⭐"),
    app_commands.Choice(name = "Good", value = "👍"),
    app_commands.Choice(name = "Meh", value = "🤷‍♂️"),
    app_commands.Choice(name = "Bad", value = "👎"),
    app_commands.Choice(name = "Terrible", value = "🗑️")
])
async def add_rating(interaction: discord.Interaction, movie_link: str, rating: app_commands.Choice[str]):
    discord_user = interaction.user

    # Check if user already rated movie
    if (db_collection.count_documents({"discord_id": discord_user.id, "movie_link": movie_link}) > 0):
        await interaction.response.send_message(f"It seems you've already rated this movie <@{str(discord_user.id)}>. Please remove your rating with the `/remove_rating` before rating it again.")
    else:
        x = db_collection.insert_one({"discord_id": discord_user.id, "movie_link": movie_link, "rating": rating.name})
        print(f"Inserted movie for {discord_user.id} ({discord_user.name}) with document id={str(x.inserted_id)}")
        await interaction.response.send_message(f"<@{str(discord_user.id)}> added a {rating.value} rating for the movie {movie_link}")

# View rating command
@tree.command(name = "view_rating", description = "View your rating of a movie or TV show from the database", guild = DEV_GUILD)
async def view_rating(interaction: discord.Interaction, movie_link: str):
    discord_user = interaction.user

    x = db_collection.find_one({"discord_id": discord_user.id, "movie_link": movie_link})
    if (x != None):
        if (x["rating"] == "Amazing"):
            rating = "⭐"
        elif (x["rating"] == "Good"):
            rating = "👍"
        elif (x["rating"] == "Meh"):
            rating = "🤷‍♂️"
        elif (x["rating"] == "Bad"):
            rating = "👎"
        elif (x["rating"] == "Terrible"):
            rating = "🗑️"
        
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, your rating for the movie {movie_link} is {rating}")
    else:
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, you have yet to review that movie. Use the `/add_rating` command to add your rating for it.")

# Remove rating command
@tree.command(name = "remove_rating", description = "Remove your rating for a movie or TV show from the database", guild = DEV_GUILD)
async def remove_rating(interaction: discord.Interaction, movie_link: str):
    discord_user = interaction.user

    x = db_collection.find_one_and_delete({"discord_id": discord_user.id, "movie_link": movie_link})
    if (x != None):
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, your rating for that movie is removed")
    else:
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, you have yet to review that movie. Use the `/add_rating` command to add your rating for it.")

# Close connection to database
@tree.command(name = "disconnect", description = "Close connection to the database and disconnect bot", guild = DEV_GUILD)
async def disconnect(interaction: discord.Interaction):
    db_client.close()
    print("Connection to database successful! Disconecting...")
    # TODO: Make sure bellow is proper way to exit discord and python script
    await bot_client.close()
    quit()

# Connect bot to Discord
bot_client.run(TOKEN)