import discord
import random
import datetime
import asyncio
from discord.ext import commands

# Rest of the code


bot_texts = {
    "Initiate": [
        "Tenno, a new Tenno operative has emerged from their sleep, will you be kind and guide {user_mention} in their upcoming journeys and be a mentor to them?",
        "Tenno, a new Tenno operative has emerged from their sleep, will you be kind and guide {user_mention} as a mentor just like how we started from the beginning?"
    ],
    "LFG": [
        "Tennos, a fellow Tenno operative needs your help in {event_type}, will you join this mission and help {user_mention} conquer their quests?",
        "Tennos, a fellow Tenno operative needs your help for their adventures, will you join them and help {user_mention} set forth in creating a joyous memory?"
    ]
}

event_types = {
    "Free-roaming": [
        "Plains of Eidolon",
        "Bounty",
        "Eidolon Hunt",
        "Profit-Taker Orb",
        "Cetus",
        "Fishing",
        "Mining",
        "Conservation"
    ],
    "Farming": [
        "Fortuna",
        "Bounty",
        "Orb Vallis Bounty",
        "Exploiter Orb",
        "Profit-Taker Orb",
        "Duviri Paradox",
        "The Maw",
        "The Vault",
        "The Circuit"
    ],
    "Node Missions": [
        "Defense",
        "Excavation",
        "Interception",
        "Mobile Defense",
        "Nightmare Missions",
        "Onslaught",
        "Rescue",
        "Sabotage",
        "Survival"
    ],
    "Other": [
        "Arbitration",
        "Fissures",
        "Nightwave",
        "Relics",
        "Steel Path"
    ]
}


intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.messages = True
intents.message_content = True

client = commands.Bot(command_prefix="$", intents=intents, help_command=None)
lfg_posts = []
lfg_ratings = {}
lfg_reports = {}
def find_lfg_message(client):
    """Finds the LFG message ID by searching for the joining reaction."""
    for channel in client.get_all_channels():
        for message in channel.history(limit=100):
            if JOINING_REACTION in message.reactions:
                return message.id

    return None

LFG_MESSAGE_ID = find_lfg_message(client)

JOINING_REACTION = "✅"  # Replace with the joining reaction emoji or text

@client.event
async def on_ready():
    print(f"LFG Bot is ready!")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Invalid command. Use `$help` to see a list of available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments. Use `$help <command>` to see the command usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")


def check(message, author, channel):
    return message.author == author and message.channel == channel

@client.command(name="create")
async def create_lfg(ctx):
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    async def prompt_input(ctx, prompt, timeout=60.0):
        await ctx.send(prompt)
        try:
            user_input = await client.wait_for('message', check=check, timeout=timeout)
            return user_input.content
        except asyncio.TimeoutError:
            await ctx.send("Timed out. No response received.")
            return None

    async def show_confirmation_embed(ctx, game, platform, event_type):
        embed = discord.Embed(title="LFG - Confirmation", color=discord.Color.blue())
        embed.add_field(name="Game", value=game, inline=False)
        embed.add_field(name="Platform", value=platform, inline=False)
        embed.add_field(name="Event Type", value=event_type, inline=False)
        embed.set_footer(text=f"Posted by {ctx.author.display_name}")

        await ctx.send(embed=embed)

    await ctx.send("Let's create a new LFG post. Please provide the following details:")

    game = await prompt_input(ctx, "Game:", timeout=60.0)
    if game is None:
        await ctx.send("Timed out. No post created.")
        return

    platform = await prompt_input(ctx, "Platform:", timeout=60.0)
    if platform is None:
        await ctx.send("Timed out. No post created.")
        return

    # Rest of the code...


    event_type_options = list(event_types.keys())

    event_type_prompt = "Event Type: Please select the number corresponding to the event type:\n"
    for index, event_type in enumerate(event_type_options):
        event_type_prompt += f"{index+1}. {event_type}\n"
    event_type_prompt += "Enter your choice:"

    await ctx.send(event_type_prompt)

    try:
        event_type_choice = await client.wait_for('message', check=check, timeout=60.0)
        choice = int(event_type_choice.content)
        if choice < 1 or choice > len(event_type_options):
            await ctx.send("Invalid choice. Please select a valid option.")
            return
        event_type = event_type_options[choice - 1]
    except (asyncio.TimeoutError, ValueError):
        await ctx.send("Timed out or invalid choice. No response received.")
        return

    await show_confirmation_embed(ctx, game, platform, event_type)

    confirmation_message = await ctx.send("Confirm your post by reacting with ✅.")

    # Adding the emoji reaction
    await confirmation_message.add_reaction("✅")

    try:
        reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=lambda r, u: str(r.emoji) == "✅" and u == ctx.author)
    except asyncio.TimeoutError:
        await ctx.send("Timed out. No confirmation received.")
        return

    role = get_user_role(ctx.author)

    if role not in bot_texts:
        await ctx.send("Invalid role. Available roles: Initiate, LFG")
        return

    bot_text = random.choice(bot_texts[role])
    user_mention = ctx.author.mention
    event_type = event_type.capitalize()

    description = bot_text.format(user_mention=user_mention, event_type=event_type)

    embed = discord.Embed(
        title="LFG",
        description=description,
        color=discord.Color.blue()
    )
    embed.add_field(name="Game", value=game, inline=False)
    embed.add_field(name="Platform", value=platform, inline=False)
    embed.add_field(name="Event Type", value=event_type, inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction(JOINING_REACTION)  # Reaction for participation

    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")

    lfg_posts.append({
        "game": game,
        "platform": platform,
        "role": role,
        "event_type": event_type,
        "author": ctx.author,
        "message": message,
        "timestamp": timestamp
    })

    await ctx.send("LFG post created successfully!")


@client.command(name="search")
async def search_lfg(ctx, game, platform):
    results = []
    for post in lfg_posts:
        if post["game"] == game and post["platform"] == platform:
            results.append(post)

    if results:
        embed = discord.Embed(
            title="LFG - Search Results",
            description="Here are the results for your search:",
            color=discord.Color.green()
        )

        for result in results:
            embed.add_field(name=result['game'], value=f"Platform: {result['platform']}", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("No matching results found.")

@client.command(name="advanced_search")
async def advanced_search_lfg(ctx):
    async def prompt_input(ctx, prompt):
        await ctx.send(prompt)
        try:
            response = await client.wait_for('message', check=check, timeout=60.0)
            return response.content
        except asyncio.TimeoutError:
            await ctx.send("Timed out. No response received.")
            return None

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    await ctx.send("Let's start the advanced search.")
    await ctx.send("Please provide the following details:")

    game = await prompt_input(ctx, "Game:")
    platform = await prompt_input(ctx, "Platform:")
    event_type = await prompt_input(ctx, "Event Type (optional):")
    difficulty = await prompt_input(ctx, "Difficulty (optional):")
    time_of_day = await prompt_input(ctx, "Time of Day (optional):")

    await ctx.send("Searching for LFG posts...")

    results = []
    for post in lfg_posts:
        if post["game"] == game and post["platform"] == platform:
            if event_type and post["event_type"] != event_type:
                continue
            if difficulty and "difficulty" in post and post["difficulty"] != difficulty:
                continue
            if time_of_day and "time_of_day" in post and post["time_of_day"] != time_of_day:
                continue
            results.append(post)

    if results:
        embed = discord.Embed(
            title="LFG - Search Results",
            description="Here are the results for your search:",
            color=discord.Color.green()
        )

        for result in results:
            embed.add_field(name=result['game'], value=f"Platform: {result['platform']}", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("No matching results found.")


@client.command(name="rate")
async def rate_lfg(ctx, post_id, rating):
    try:
        post_id = int(post_id)
        rating = int(rating)
    except ValueError:
        await ctx.send("Invalid post ID or rating. Please provide valid numeric values.")
        return

    if post_id < 0 or post_id >= len(lfg_posts):
        await ctx.send("Invalid post ID. Please provide a valid post ID.")
        return

    if rating < 1 or rating > 5:
        await ctx.send("Invalid rating. Please provide a rating between 1 and 5.")
        return

    author_id = ctx.author.id
    post = lfg_posts[post_id]

    if author_id == post["author"].id:
        await ctx.send("You cannot rate your own post.")
        return

    if post_id not in lfg_ratings:
        lfg_ratings[post_id] = []

    lfg_ratings[post_id].append(rating)
    await ctx.send("Thank you for rating the LFG post!")


@client.command(name="report")
async def report_lfg(ctx, post_id, reason):
    try:
        post_id = int(post_id)
    except ValueError:
        await ctx.send("Invalid post ID. Please provide a valid numeric post ID.")
        return

    if post_id < 0 or post_id >= len(lfg_posts):
        await ctx.send("Invalid post ID. Please provide a valid post ID.")
        return

    post = lfg_posts[post_id]

    if post_id not in lfg_reports:
        lfg_reports[post_id] = []

    lfg_reports[post_id].append({"author": ctx.author, "reason": reason})
    await ctx.send("The LFG post has been reported. Thank you for your feedback.")

@client.command(name="complete")
async def complete_lfg(ctx, post_id):
    try:
        post_id = int(post_id)
    except ValueError:
        await ctx.send("Invalid post ID. Please provide a valid numeric post ID.")
        return

    if post_id < 0 or post_id >= len(lfg_posts):
        await ctx.send("Invalid post ID. Please provide a valid post ID.")
        return

    post = lfg_posts[post_id]

    if ctx.author.id != post["author"].id:
        await ctx.send("You can only mark your own LFG post as completed.")
        return

    # Perform any necessary actions when the post is completed

    # Remove the LFG post from the list
    del lfg_posts[post_id]
    await ctx.send("LFG post marked as completed and deleted.")
   
@client.command(name="clear")
async def clear_lfg(ctx):
    lfg_posts.clear()
    await ctx.send("All LFG posts have been cleared.")
    
async def create_lfg(ctx):
    role = get_user_role(ctx.author)

    if role not in bot_texts:
        await ctx.send("Invalid role. Available roles: Initiate, LFG")
        return

    bot_text = random.choice(bot_texts[role])
    user_mention = ctx.author.mention

    embed = discord.Embed(
        title="LFG - Create Post",
        description="Please select the options for your LFG post:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Event", value="\u200b", inline=False)
    embed.add_field(name="Platform", value="\u200b", inline=False)
    embed.add_field(name="Game", value="\u200b", inline=False)

    message = await ctx.send(embed=embed)

    options = {
        "Event": event_types,
        "Platform": ["PC", "Xbox", "PlayStation"],
        "Game": ["Warframe", "Destiny 2", "Apex Legends", "Overwatch"]
    }

    reactions = ["\U0001F1E6", "\U0001F1E8", "\U0001F1F7"]
    for reaction in reactions[:len(options)]:
        await message.add_reaction(reaction)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions[:len(options)]

    try:
        reaction, _ = await client.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("LFG post creation timed out.")
        return

    selected_option = options[embed.fields[reactions.index(str(reaction.emoji))].name]
    embed.clear_fields()
    embed.title = "LFG - Confirm Post"
    embed.description = "Please review and confirm your LFG post:"
    embed.add_field(name="Event", value=selected_option, inline=False)
    embed.add_field(name="Platform", value="\u200b", inline=False)
    embed.add_field(name="Game", value="\u200b", inline=False)

    await message.edit(embed=embed)

    try:
        reaction, _ = await client.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("LFG post creation timed out.")
        return

    selected_option = options[embed.fields[reactions.index(str(reaction.emoji))].name]
    embed.clear_fields()
    embed.title = "LFG - Confirm Post"
    embed.description = "Please review and confirm your LFG post:"
    embed.add_field(name="Event", value=selected_option[embed.fields[0].value], inline=False)
    embed.add_field(name="Platform", value=selected_option[embed.fields[1].value], inline=False)
    embed.add_field(name="Game", value=selected_option[embed.fields[2].value], inline=False)

    await message.edit(embed=embed)

    # Retrieve the selected options
    event = selected_option[embed.fields[0].value]
    platform = selected_option[embed.fields[1].value]
    game = selected_option[embed.fields[2].value]

    # Customize the bot text based on the selected options
    bot_text = random.choice(bot_texts[role])
    description = bot_text.format(user_mention=user_mention, event_type=event)

    embed = discord.Embed(
        title="LFG",
        description=description,
        color=discord.Color.blue()
    )
    embed.add_field(name="Platform", value=platform)
    embed.add_field(name="Game", value=game)

    await ctx.send(embed=embed)

    # Add the LFG post to the list
    lfg_posts.append({"author": ctx.author, "event": event, "platform": platform, "game": game, "role": role})
        
async def search_lfg(ctx, game, platform):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []
    for post in lfg_posts:
        if post["game"] == game and post["platform"] == platform:
            results.append(post)

    if results:
        embed = discord.Embed(
            title="LFG - Search Results",
            description="Here are the results for your search:",
            color=discord.Color.green()
        )

        for result in results:
            embed.add_field(name=result['game'], value=f"Platform: {result['platform']}\nPosted at: {current_time}", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("No matching results found.")

@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == LFG_MESSAGE_ID and str(payload.emoji) == JOINING_REACTION:
        channel = await client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        author_id = message.embeds[0].footer.text
        author = await client.fetch_user(int(author_id))
        user = await client.fetch_user(payload.user_id)
        await author.send(f"{user.mention} has joined your LFG post!")


@client.command(name="help")
async def help_command(ctx):
    help_message = """
    **LFG Bot Help**

    **Commands:**
    `$create` - Create an LFG post.
    `$search <game> <platform>` - Search for LFG posts by game and platform.
    `$advanced_search` - Perform an advanced search with additional criteria.
    `$rate <post_id> <rating>` - Rate an LFG post.
    `$report <post_id> <reason>` - Report an LFG post.
    `$complete <post_id>` - Mark your own LFG post as completed.
    `$clear` - Clear all LFG posts.
    `$help` - Show this help message.
    """

    embed = discord.Embed(
        title="LFG Bot Help",
        description=help_message,
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)


@client.command(name="ping")
async def ping(ctx):
    latency = client.latency
    await ctx.send(f"Pong! Latency: {latency * 1000:.2f} ms")


def get_user_role(author):
    for role in author.roles:
        if role.name == "Initiate":
            return "Initiate"
    return "LFG"


def get_random_event_type():
    event_type = random.choice(list(event_types.keys()))
    sub_event_type = random.choice(event_types[event_type])
    return f"{event_type} - {sub_event_type}"


client.run("MTEyMTY4NzI0NTk1MTMzNjUyOQ.GGapZQ.DeecEr1Z5pNq1EuCMVYh-qjGFygmE1-3Z9Nx-o")
