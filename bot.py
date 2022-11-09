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
async def add_rating(interaction: discord.Interaction, imdb_link: str, rating: app_commands.Choice[str]):
    discord_user = interaction.user

    # Check if user already rated movie or TV Show
    if (db_collection.count_documents({"discord_id": discord_user.id, "imdb_link": imdb_link}) > 0):
        await interaction.response.send_message(f"It seems you've already rated this <@{str(discord_user.id)}>. Please change your rating with the `/change_rating` command.")
    else:
        x = db_collection.insert_one({"discord_id": discord_user.id, "imdb_link": imdb_link, "rating": rating.name})
        print(f"New entry for {discord_user.id} ({discord_user.name}) with document id={str(x.inserted_id)}")
        await interaction.response.send_message(f"<@{str(discord_user.id)}> added a {rating.value} rating for {imdb_link}")

# View rating command
@tree.command(name = "view_rating", description = "View your rating of a movie or TV show from the database", guild = DEV_GUILD)
async def view_rating(interaction: discord.Interaction, imdb_link: str):
    discord_user = interaction.user

    x = db_collection.find_one({"discord_id": discord_user.id, "imdb_link": imdb_link})
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
        
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, your rating for {imdb_link} is {rating}")
    else:
        await interaction.response.send_message(f"It seems you have yet to review this <@{str(discord_user.id)}>. Use the `/add_rating` command to add your rating for it.")

# View someone's rating command
@tree.command(name = "view_user_rating", description = "View someone else's rating for a movie or TV show from the database", guild = DEV_GUILD)
async def view_user_rating(interaction: discord.Interaction, imdb_link: str, discord_user: discord.User):
    x = db_collection.find_one({"discord_id": discord_user.id, "imdb_link": imdb_link})
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
        
        await interaction.response.send_message(f"{discord_user.name}'s rating for {imdb_link} is {rating}")
    else:
        await interaction.response.send_message(f"{discord_user.name} has not reviewed that yet.")

# View ratings command
@tree.command(name = "view_ratings", description = "View all ratings for a movie or TV show from the database", guild = DEV_GUILD)
async def view_ratings(interaction: discord.Interaction, imdb_link: str):
    x = list(db_collection.find({"imdb_link": imdb_link}))
    
    if (len(x) > 0):
        amazing_rating = good_rating = meh_rating = bad_rating = terrible_rating = 0
        for document in x:
            if (document["rating"] == "Amazing"):
                amazing_rating += 1
            elif (document["rating"] == "Good"):
                good_rating += 1
            elif (document["rating"] == "Meh"):
                meh_rating += 1
            elif (document["rating"] == "Bad"):
                bad_rating += 1
            elif (document["rating"] == "Terrible"):
                terrible_rating += 1

        await interaction.response.send_message(f"Current ratings for {imdb_link} are\n" +
            f"⭐ : {str(amazing_rating)} | " +
            f"👍 : {str(good_rating)} | " +
            f"🤷‍♂️ : {str(meh_rating)} | " +
            f"👎 : {str(bad_rating)} | " +
            f"🗑️ : {str(terrible_rating)}")
    else: 
        await interaction.response.send_message(f"That entry doesn't have any ratings yet.")

# Change rating command
@tree.command(name = "change_rating", description = "Change your rating for a movie or TV show from the database", guild = DEV_GUILD)
@app_commands.choices(rating = [
    app_commands.Choice(name = "Amazing", value = "⭐"),
    app_commands.Choice(name = "Good", value = "👍"),
    app_commands.Choice(name = "Meh", value = "🤷‍♂️"),
    app_commands.Choice(name = "Bad", value = "👎"),
    app_commands.Choice(name = "Terrible", value = "🗑️")
])
async def change_rating(interaction: discord.Interaction, imdb_link: str, rating: app_commands.Choice[str]):
    discord_user = interaction.user

    x = db_collection.find_one_and_update({"discord_id": discord_user.id, "imdb_link": imdb_link}, {'$set' : {"rating": rating.name}})
    if (x != None):
        print(f"Updated entry for {discord_user.id} ({discord_user.name}) with document id=" + str(x["_id"]))
        await interaction.response.send_message(f"<@{str(discord_user.id)}> changed their rating for {imdb_link} to {rating.value}")
    else:
        await interaction.response.send_message(f"It seems you have yet to review this <@{str(discord_user.id)}>. Use the `/add_rating` command to add your rating for it.")

# Remove rating command
@tree.command(name = "remove_rating", description = "Remove your rating for a movie or TV show from the database", guild = DEV_GUILD)
async def remove_rating(interaction: discord.Interaction, imdb_link: str):
    discord_user = interaction.user

    x = db_collection.find_one_and_delete({"discord_id": discord_user.id, "imdb_link": imdb_link})
    if (x != None):
        await interaction.response.send_message(f"<@{str(discord_user.id)}>, your rating for that is removed")
    else:
        await interaction.response.send_message(f"It seems you have yet to review this <@{str(discord_user.id)}>. Use the `/add_rating` command to add your rating for it.")

# Close connection to database
@tree.command(name = "disconnect", description = "Close connection to the database and disconnect bot", guild = DEV_GUILD)
async def disconnect(interaction: discord.Interaction):
    db_client.close()
    await interaction.response.send_message("Closed the connection to the database! Disconecting from Discord...")
    # TODO: Make sure bellow is proper way to exit discord and python script
    await bot_client.close()
    quit()

# Connect bot to Discord
bot_client.run(TOKEN)