import logging
import requests
import asyncio
import discord
from discord import Embed
from discord.ext import commands
import sqlite3
import datetime
import math
import os
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()

# Access the DISCORD_TOKEN environment variable
import os
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()

SERVER_ID = "1121721749860515901"
CHANNEL_ID = "1123912418360307788"

def send_message_to_server(message):
    try:
        headers = {
            "Authorization": "Bot " + "DISCORD_TOKEN",
            "Content-Type": "application/json"
        }

        # Send message to server
        url = "https://discord.com/api/v9/channels/" + CHANNEL_ID + "/messages"
        payload = {"content": message}
        response = requests.post(url, headers=headers, json=payload)
        
        print("Message sent successfully")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred while sending message: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending message: {e}")

# Example usage
send_message_to_server("Hello, server!")


# Your bot code here


conn = sqlite3.connect('lfg.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lfg_posts (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        lfg_posting TEXT,
        category TEXT,
        time_and_date TEXT,
        channel_id INTEGER
    )
''')


# Create the guilds table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (
        guild_id INTEGER PRIMARY KEY,
        lfg_channel_id INTEGER,
        active_channel_id INTEGER
    )
""")

conn.commit()

# Create the intents and enable necessary intents
intents = discord.Intents.default()
intents.members = True  # Enable member-related events
intents.presences = True  # Enable presence-related events
intents.messages = True  # Enable message-related events
intents.message_content = True  # Enable access to message content
intents.typing = False  # Disable typing events for better performance
intents.guild_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="$", intents=intents)

bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print("------")
    
@bot.command()
async def lfg(ctx):
    # Your LFG command code here
    await ctx.reply('LFG Warframe!')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Error: Invalid command. Use $help to see the available commands.")

#Create Command

@bot.command()
async def create(ctx):
    def check_author(author):
        def inner_check(message):
            return message.author == author
        return inner_check

    try:
        await ctx.send("Enter the details for your LFG post.")

        description_embed = discord.Embed(title="LFG Post Description", description="Please provide the LFG posting's description:")
        description_message = await ctx.send(embed=description_embed)

        def check_cancel(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "❌" and reaction.message.id == description_message.id

        await description_message.add_reaction("❌")

        try:
            description_response = await bot.wait_for("message", check=check_author(ctx.author), timeout=60).author == ctx.author
            lfg_posting = description_response.content
        except asyncio.TimeoutError:
            await ctx.send("LFG post creation timed out.")
            return
        finally:
            await description_message.clear_reactions()

        time_and_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        category_options = {
            "1️⃣": "Hunting of Free-roam Bosses",
            "2️⃣": "Relic Hunt",
            "3️⃣": "Steel Path",
            "4️⃣": "Node Missions",
            "5️⃣": "Others"
        }

        embed = discord.Embed(title="Post Category", description="Select the category for your LFG post")
        options = "\n".join([f"{emoji} {category}" for emoji, category in category_options.items()])
        embed.add_field(name="Options", value=options)
        category_message = await ctx.send(embed=embed)

        for emoji in category_options.keys():
            await category_message.add_reaction(emoji)

        def check_reaction(reaction, user):
            return user == ctx.author and reaction.emoji in category_options.keys()

        reaction, _ = await bot.wait_for("reaction_add", check=check_reaction)
        selected_emoji = reaction.emoji
        selected_category = category_options[selected_emoji]

        if selected_category == "Others":
            await ctx.send("Enter the category for your LFG post:")
            category_message = await bot.wait_for("message", check=check_author(ctx.author))
            category = category_message.content
        else:
            category = selected_category

        post = discord.Embed(title="Looking for Group", description=lfg_posting, color=0x00ff00)
        post.add_field(name="Category", value=category, inline=False)
        post.add_field(name="Time and Date", value=time_and_date)
        post.set_footer(text=f"Posted by: {ctx.author.mention}")

        # Generate a unique post ID
        cursor.execute(
            "INSERT INTO lfg_posts (user_id, lfg_posting, category, time_and_date, channel_id) VALUES (?, ?, ?, ?, ?)",
            (ctx.author.id, lfg_posting, category, time_and_date, ctx.channel.id)
        )
        post_id = cursor.lastrowid  # Get the last inserted row ID
        conn.commit()

        post.add_field(name="Post ID", value=post_id, inline=False)  # Add post ID to the embed

        posted_message = await ctx.send(embed=post)

        lfg_role = discord.utils.get(ctx.guild.roles, name="LFG")
        if lfg_role is not None:
            await posted_message.channel.send(f"{lfg_role.mention} New LFG post by {ctx.author.mention}!")

    except asyncio.CancelledError:
        # Handle the cancellation, e.g., cleanup or logging
        pass  # or raise an exception or perform necessary cleanup

#Setting LFG Channel

# Set LFG and Active Channel
@bot.command()
@commands.has_permissions(administrator=True)
async def set_channel(ctx, lfg_channel: discord.TextChannel, active_channel: discord.TextChannel):
    set_guild_setting(ctx.guild.id, "lfg_channel_id", lfg_channel.id)
    set_guild_setting(ctx.guild.id, "active_channel_id", active_channel.id)
    await ctx.send(f"LFG channel set to {lfg_channel.mention} and active channel set to {active_channel.mention}")

# Set LFG Role and LFG Ping Role
@bot.command()
@commands.has_permissions(administrator=True)
async def set_role(ctx, lfg_role: discord.Role, lfg_ping_role: discord.Role):
    set_guild_setting(ctx.guild.id, "lfg_role_id", lfg_role.id)
    set_guild_setting(ctx.guild.id, "lfg_ping_role_id", lfg_ping_role.id)
    await ctx.send(f"LFG role set to {lfg_role.mention} and LFG ping role set to {lfg_ping_role.mention}")

# Common function to set guild settings
def set_guild_setting(guild_id, setting_name, setting_value):
    cursor.execute("INSERT OR REPLACE INTO guilds (guild_id, " + setting_name + ") VALUES (?, ?)", (guild_id, setting_value))
    conn.commit()

# Event: Message received
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.TextChannel):
        cursor.execute("SELECT lfg_channel_id FROM guilds WHERE guild_id = ?", (message.guild.id,))
        result = cursor.fetchone()

        if result is not None and result[0] is not None:
            lfg_channel_id = result[0]
            if message.channel.id == lfg_channel_id:
                await bot.process_commands(message)

#Filter Commands

@bot.command()
async def filter(ctx):
    def check_author(author):
        def inner_check(message):
            return message.author == author
        return inner_check

    category_options = {
        "1️⃣": "Hunting of Free-roam Bosses",
        "2️⃣": "Relic Hunt",
        "3️⃣": "Steel Path",
        "4️⃣": "Node Missions",
        "5️⃣": "Others"
    }

    cancel_emoji = "❌"

    embed = discord.Embed(title="Filter LFG Posts", description="React with the corresponding emoji to select a category to filter LFG posts")

    for emoji, category in category_options.items():
        embed.add_field(name=f"{emoji} {category}", value="\u200b", inline=False)

    embed.add_field(name=f"{cancel_emoji} Cancel", value="\u200b", inline=False)

    message = await ctx.send(embed=embed)

    for emoji in category_options.keys():
        await message.add_reaction(emoji)

    await message.add_reaction(cancel_emoji)

    def check_reaction(reaction, user):
        return user == ctx.author and (str(reaction.emoji) in category_options.keys() or str(reaction.emoji) == cancel_emoji)

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
        if str(reaction.emoji) == cancel_emoji:
            await ctx.send("Filtering process canceled.")
            return
        selected_category = category_options[str(reaction.emoji)]
    except asyncio.TimeoutError:
        await ctx.send("Category selection timed out.")
        return

    if selected_category == "Others":
        excluded_categories = [category_options[emoji] for emoji in category_options.keys() if emoji != "5️⃣"]
        cursor.execute("SELECT * FROM lfg_posts WHERE category NOT IN ({})".format(','.join('?' * len(excluded_categories))), excluded_categories)
    else:
        cursor.execute("SELECT * FROM lfg_posts WHERE category = ?", (selected_category,))

    filtered_posts = cursor.fetchall()

    if filtered_posts:
        await ctx.send(f"Here are the filtered LFG posts in the {selected_category} category:")
        for post in filtered_posts:
            user_id = post[1]
            user = ctx.guild.get_member(user_id)
            if user:
                user_mention = user.mention
            else:
                user_mention = f"User ID: {user_id}"
                
            embed = discord.Embed(title="Looking for Group", description=post[2], color=0x00ff00)
            embed.add_field(name="Category", value=post[3])
            embed.add_field(name="Time and Date", value=post[4])
            embed.set_footer(text=f"Posted by: {user_mention}")
            await ctx.send(embed=embed)
    else:
        await ctx.send(f"No LFG posts found in the {selected_category} category.")


#Delete Command

@bot.command()
@commands.has_permissions(manage_messages=True)
async def delete(ctx, post_id: int):
    try:
        cursor.execute("SELECT * FROM lfg_posts WHERE post_id = ?", (post_id,))
        post = cursor.fetchone()

        if post:
            embed = discord.Embed(title="LFG Posting", description=post[2], color=0x00ff00)
            embed.add_field(name="Author", value=ctx.guild.get_member(post[1]).mention)
            embed.add_field(name="Category", value=post[3])
            embed.add_field(name="Time and Date", value=post[4])

            delete_emoji = "❌"
            confirm_emoji = "✅"

            message = await ctx.send(embed=embed)
            await message.add_reaction(delete_emoji)
            await message.add_reaction(confirm_emoji)

            def check_reaction(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and reaction.emoji in [delete_emoji, confirm_emoji]
                )

            reaction, _ = await bot.wait_for("reaction_add", timeout=120.0, check=check_reaction)

            if reaction is None:
                await message.delete()
                await ctx.send("No reaction received. Post deletion canceled.")
                return
            
            if reaction.emoji == confirm_emoji:
                cursor.execute("DELETE FROM lfg_posts WHERE post_id = ?", (post_id,))
                conn.commit()
                await message.delete()
                await ctx.send(f"Post with ID {post_id} has been deleted.")
            else:
                await message.delete()
                await ctx.send("Post deletion canceled.")
        else:
            await ctx.send(f"Post with ID {post_id} was not found or has already been deleted.")
    except discord.errors.NotFound:
        await ctx.send(f"Post with ID {post_id} was not found or has already been deleted.")
    except asyncio.TimeoutError:
        await ctx.send("Timeout: You took too long to respond.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

#List Command

@bot.command()
async def list(ctx):
    try:
        cursor.execute("SELECT * FROM lfg_posts")
        posts = cursor.fetchall()

        if not posts:
            await ctx.send("No LFG posts found.")
            return

        if len(posts) <= 4:
            embed = discord.Embed(title="LFG Posts", color=0x00ff00)

            for post in posts:
                author = ctx.guild.get_member(post[1]).mention
                description = post[2] or "No description available"
                category = post[3]
                time_and_date = post[4]

                embed.add_field(name="ID", value=post[0], inline=True)
                embed.add_field(name="Author", value=author, inline=True)
                embed.add_field(name="Description", value=description, inline=True)
                embed.add_field(name="Category", value=category, inline=True)
                embed.add_field(name="Time and Date", value=time_and_date, inline=True)
                embed.add_field(name="\u200b", value="".join(["-" for _ in range(len(embed.fields[0].value))]), inline=False)

            embed.set_footer(text="No pagination needed.")
            await ctx.send(embed=embed)
            return

        posts_per_page = 4
        total_pages = math.ceil(len(posts) / posts_per_page)
        page = 1

        while True:
            start_index = (page - 1) * posts_per_page
            end_index = start_index + posts_per_page
            paged_posts = posts[start_index:end_index]

            embed = discord.Embed(title="LFG Posts", color=0x00ff00)

            for post in paged_posts:
                author = ctx.guild.get_member(post[1]).mention
                description = post[2] or "No description available"
                category = post[3]
                time_and_date = post[4]

                embed.add_field(name="ID", value=post[0], inline=True)
                embed.add_field(name="Author", value=author, inline=True)
                embed.add_field(name="Description", value=description, inline=True)
                embed.add_field(name="Category", value=category, inline=True)
                embed.add_field(name="Time and Date", value=time_and_date, inline=True)
                embed.add_field(name="\u200b", value="".join(["-" for _ in range(len(embed.fields[0].value))]), inline=False)

            embed.set_footer(text=f"Page {page}/{total_pages} | Use ◀️ and ▶️ to navigate between pages | React with ❌ to cancel.")

            message = await ctx.send(embed=embed)

            if total_pages > 1:
                if page > 1:
                    await message.add_reaction("◀️")
                if page < total_pages:
                    await message.add_reaction("▶️")
                await message.add_reaction("❌")

                def check_reaction(reaction, user):
                    return (
                        user == ctx.author
                        and reaction.message.id == message.id
                        and reaction.emoji in ["◀️", "▶️", "❌"]
                    )

                try:
                    reaction, _ = await bot.wait_for("reaction_add", check=check_reaction)
                except Exception:
                    # Handle any exceptions during wait_for
                    break
                else:
                    if reaction.emoji == "◀️" and page > 1:
                        page -= 1
                    elif reaction.emoji == "▶️" and page < total_pages:
                        page += 1
                    elif reaction.emoji == "❌":
                        await message.clear_reactions()
                        await message.edit(content="List process canceled.")
                        break

                    await message.clear_reactions()

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

#Ping Command

@bot.command(name="ping")
async def ping(ctx):
    latency = bot.latency
    await ctx.send(f"Pong! Latency: {latency * 1000:.2f} ms")

#About Command

@bot.command()
async def about(ctx):
    developer_id = 479209697606500364
    developer = await bot.fetch_user(developer_id)

    bot_name = bot.user.name
    bot_icon = bot.user.avatar.url

    embed = discord.Embed(title="About {}".format(bot_name), color=0x00ff00)
    embed.set_thumbnail(url=bot_icon)
    embed.add_field(name="Bot Name", value=bot_name, inline=False)
    embed.add_field(name="Developer", value=developer.name, inline=False)
    embed.add_field(name="Description", value="I am an LFG Warframe bot that is designed to make it easy for players to find groups for missions. Just provide a description and the type of hunting you want help with, and I will create a request post for you. Players will be able to see your username and join your group.", inline=False)
    embed.add_field(name="Usage", value="To create a group request, use `$create`. To filter group requests, use `$filter`. For more commands, use `$help`.", inline=False)
    embed.add_field(name="Development Status", value="I am still under development, so if I encounter issues, please bear with me. I am continuously working to improve and provide the best LFG Warframe experience.", inline=False)
    embed.set_footer(text="Developed by {} • Thank you for using {}!".format(developer.name, bot_name), icon_url=developer.avatar.url)

    await ctx.send(embed=embed)



@bot.command()
async def help(ctx):
    prefix = "$"  # Customize the bot's prefix as needed

    general_commands = {
        "$create": "Create a new LFG post.\nUsage: {}create".format(prefix),
        "$filter": "Filter LFG posts.\nUsage: {}filter".format(prefix),
        "$delete <post_id>": "Deletes an LFG post.\nUsage: {}delete [post_id]".format(prefix),
        "$list": "Show all registered LFG posts.\nUsage: {}list".format(prefix),
        "$ping": "Ping the bot.\nUsage: {}ping".format(prefix),
        "$help": "Shows this help message.\nUsage: {}help".format(prefix),
        "$about": "Display information about the bot.\nUsage: {}about".format(prefix),
        "$report <bug_description>": "Report a bug or issue with the bot.\nUsage: {}report [bug_description]".format(prefix)
    }

    moderator_commands = {
        "$set_guild_setting <setting_name> <value>": "Set the value of a guild setting.\nUsage: {}set_guild_setting [setting_name] [value]".format(prefix),
        "$set_lfg_channel #Channel_Name": "Set the channel where LFG posts are sent.\nUsage: {}set_lfg_channel [#channel]".format(prefix),
        "$set_lfg_role @Role_Name": "Set the role to ping for LFG posts.\nUsage: {}set_lfg_role [@role]".format(prefix)
    }

    embed = discord.Embed(title="Bot Commands", color=0x00ff00)

    general_help = "Here are the available commands:\n\n" + "\n".join([
        "**{}**: {}".format(command, usage) for command, usage in general_commands.items()
    ])
    embed.add_field(name="General Commands", value=general_help, inline=False)

    if ctx.author.guild_permissions.manage_guild:
        moderator_help = "Here are the moderator-exclusive commands:\n\n" + "\n".join([
            "**{}**: {}".format(command, usage) for command, usage in moderator_commands.items()
        ])
        embed.add_field(name="Moderator Commands", value=moderator_help, inline=False)

    about_help = "This bot helps users create and manage LFG (Looking For Group) posts in your server.\nUse the following command to get more information about the bot:\n{}about".format(prefix)
    embed.add_field(name="About", value=about_help, inline=False)

    bug_report_help = "To report a bug or issue with the bot, use the following command:\n{}report <bug_description>".format(prefix)
    embed.add_field(name="Bug Report", value=bug_report_help, inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def report(ctx, *, bug_description):
    bug_report_guild_id = 1121721749860515901  # Replace with the bug report server ID
    bug_report_channel_id = 1123887077365395536  # Replace with the bug report channel ID

    bug_report_guild = bot.get_guild(bug_report_guild_id)
    if bug_report_guild:
        bug_report_channel = bug_report_guild.get_channel(bug_report_channel_id)
        if bug_report_channel:
            await bug_report_channel.send(f"Bug Report by {ctx.author.mention}:\n{bug_description}")
            await ctx.send("Bug report submitted. Thank you for your feedback!")
            return

    await ctx.send("Bug report channel not found. Please contact the bot owner.")


try:
    bot.run(DISCORD_TOKEN)

except KeyboardInterrupt:
    # Handle the keyboard interrupt, e.g., perform cleanup or exit gracefully
    pass  # or raise an exception or perform necessary cleanup
