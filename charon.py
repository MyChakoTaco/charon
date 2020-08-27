# charon.py
import os
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import roles
import party
import random
import logging

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

COMMAND_PREFIX = '.'
bot = commands.Bot(command_prefix=COMMAND_PREFIX)

parties = []

logging.basicConfig(level=logging.INFO)

# returns the role regardless of input case-sensitivity
# returns None if no match can be found


def getRole(roles, roleName):
    for r in roles:
        if roleName.casefold() == str(r).casefold():
            return r
    return None

# restricts roles that can be picked based on roles.py


def isGamesRole(role):
    for validRole in roles.ROLES_LIST:
        if validRole.name.casefold() == str(role).casefold():
            return True
    return False

# On any message, if the exact text is '.iam valorant' or
# '.iamnot valorant', the bot will grant the role matching the String
# stored in roles.py. The bot will message on errors such as
# role name not found in server or the bot does not have enough permissions


@bot.command(name='iam', brief='Add yourself to SomeRole',
             description=f'''\"{COMMAND_PREFIX}iam SomeRole\" - '
             'Add yourself to SomeRole''')
async def iam(context, *arg):
    if len(arg) == 0:
        return await context.channel.send(
            f'{context.author.name}, please tell me what role to use for iam')

    role = getRole(context.guild.roles, arg[0])

    if role is None:
        return await context.channel.send(
            f'{context.author.name}, role \'{arg[0]}\' does not exist')

    if not isGamesRole(role):
        return await context.channel.send(
            f'{context.author.name}, {role} is a restricted role')

    if role in context.author.roles:
        return await context.channel.send(
            f'{context.author.name}, but you are already {role}')

    await context.author.add_roles(role)
    await context.channel.send(
        f'{context.author.name}, you are granted {role}')


@bot.command(name='iamnot', brief='Remove yourself from SomeRole',
             description=f'''\"{COMMAND_PREFIX}iamnot SomeRole\" - '
             'Remove yourself from SomeRole''')
async def iamnot(context, *arg):
    if len(arg) == 0:
        return await context.channel.send(
            f'{context.author.name}, please tell me what role to use for '
            'iamnot')

    role = getRole(context.guild.roles, arg[0])

    if role is None:
        return await context.channel.send(
            f'{context.author.name}, role \'{arg[0]}\' does not exist')

    if role not in context.author.roles:
        return await context.channel.send(
            f'{context.author.name}, but you were never {role}')

    await context.author.remove_roles(role)
    await context.channel.send(
        f'{context.author.name}, you are removed from {role}')


@bot.command(name='whois', brief='Prints users belonging to role',
             description=f'''\"{COMMAND_PREFIX}whois SomeRole\" - Prints a '
             'list of users belonging to SomeRole''')
async def whois(context, *arg):
    if len(arg) == 0:
        return await context.channel.send(f'{context.author.name}, '
                                          'please tell me what role to '
                                          'use for whois')

    role = getRole(context.guild.roles, arg[0])

    if role is None:
        return await context.channel.send(
            f'{context.author.name}, role \'{arg[0]}\' does not exist')

    members = sorted(
        list(member.name for member in role.members), key=str.casefold)

    if len(members) == 0:
        return await context.channel.send(
            f'{context.author.name}, {role} has no users')

    # prepend \n because code block bug removes first member
    memberStr = "\n" + "\n".join(members)
    await context.channel.send(
        f'{context.author.name}, here is the list of users in '
        f'{role} you requested: ```{memberStr}```')

# Lists out games supported


@bot.command(name='games', brief='Prints my supported roles',
             description=f'''\"{COMMAND_PREFIX}games\" - '
             'Prints a list of my supported roles''')
async def games(context):
    games = []

    # Variables are used for string formatting purposes
    longestRole = 0
    padding = 1

    # Add valid roles to our display
    for role in context.guild.roles:
        if isGamesRole(role):
            games.append([str(role), str(len(role.members))])
            if len(str(role)) > longestRole:
                longestRole = len(str(role))

    if len(games) == 0:
        return await context.channel.send(f'{context.author.name}, '
                                          'I manage no games here')

    formatter = "{:<"+str(longestRole+padding)+"}({})\n"
    gamesToStr = ""
    for pair in games:
        gamesToStr += formatter.format(pair[0], pair[1])
    await context.channel.send(f'{context.author.name}, here is a list of the'
                               f' roles that I manage: ```{gamesToStr}```')


@bot.command(name='party', brief='Creates a party people can join',
             description=f'''\"{COMMAND_PREFIX}party Role\" - '
             'Creates party creator for specific Role with presets\n \
\"{COMMAND_PREFIX}party SomeName OptionalSize\" - '
'Creates a custom party of SomeName and OptionalSize '
'(default size will be 4)''')
async def createParty(context, *args):
    if len(args) == 0:
        return await context.channel.send(
            f'{context.author.name}, please include a party name and optional '
            f'party size (default size is {party.DEFAULT_PARTY_SIZE} '
            'or preset)')

    name = args[0]

    if name.isspace() or len(name) == 0:
        return await context.channel.send('Please type a valid party name')

    try:
        size = int(args[1]) if len(args) >= 2 else None
    except ValueError:
        return await context.channel.send('Ensure that party size is a number')

    if len(name) > 256:
        return await context.channel.send('Your party name is too long. '
                                          '(256 characters please)')

    if size is not None and size <= 0:
        return await context.channel.send('Your party size is too small.')

    role = getRole(context.guild.roles, name)

    if role is not None and isGamesRole(role):
        message = await context.channel.send(role.mention)
    else:
        message = await context.channel.send(embed=discord.Embed())

    newParty = (party.party(message, context.author, name) if size is None
                else party.party(message, context.author, name, size))
    parties.append(newParty)

    await message.edit(embed=newParty.getEmbed())
    await message.add_reaction(newParty.joinEmoji)
    await message.add_reaction(newParty.leaveEmoji)


@bot.event
async def on_member_join(member):
    # Pick text channel that is top of the list.
    # Can change to check for Continental in future patch
    textChannel = list(filter(
        lambda x: (x.type == discord.ChannelType.text and
                   x.position == 0), member.guild.channels))[0]
    # For flavor, pick a random number of days
    numDays = random.randrange(1, 366)
    await textChannel.send(
        f'Welcome to the Continental, {member.mention}.\n'
        f'My name is Charon. I see you will be staying with us for {numDays} '
        f'day{"s" if numDays > 1 else ""}.\nFeel free to dial '
        f'\"{COMMAND_PREFIX}help\" if you require any assistance.\n'
        f'...and as always, it is a pleasure having you with us again, '
        f'{member.name}.')


@bot.event
async def on_reaction_add(reaction, user):
    global parties
    for p in parties:
        if user.name == bot.user.name:
            continue
        if p.isMatchJoinEmoji(reaction):
            if not p.hasMember(user.name):
                p.addMember(user.name)
                await reaction.message.edit(embed=p.getEmbed())
            await reaction.remove(user)
            break
        if p.isMatchLeaveEmoji(reaction):
            if p.hasMember(user.name):
                p.removeMember(user.name)
                await reaction.message.edit(embed=p.getEmbed())
                if p.isClosed():
                    parties.remove(p)
            await reaction.remove(user)
            break

# seconds of running background loop
BACKGROUND_LOOP_TIME = 60
# This function checks if parties are inactive
# and cleans up them up if they are


@tasks.loop(seconds=BACKGROUND_LOOP_TIME)
async def update_parties():
    global parties
    for p in parties:
        if p.isInactive():
            await p.message.edit(embed=p.getEmbed())
            parties.remove(p)

update_parties.start()
bot.run(TOKEN)
