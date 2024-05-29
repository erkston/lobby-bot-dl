# lobby-bot-dl
import asyncio
import datetime
from datetime import timezone
import distutils
from distutils import util
import random
from zoneinfo import ZoneInfo
import discord
from discord.ext import tasks
import json
import re
from datetime import timedelta

# importing config and reading variables
with open("config/config.json", "r") as jsonfile:
    config = json.load(jsonfile)
DiscordBotToken = config['DiscordBotToken']
BotTimezone = config['BotTimezone']
BotGame = config['BotGame']
BotAdminRole = config['BotAdminRole']
LobbyChannelName = config['LobbyChannelName']
LobbyRole = config['LobbyRole']
LobbyMessageTitle = config['LobbyMessageTitle']
LobbyMessageColor = config['LobbyMessageColor']
NappingMessageColor = config['NappingMessageColor']
NudgeMessageEnable = config['NudgeMessageEnable']
NudgeCooldown = config['NudgeCooldown']
NudgeThreshold = config['NudgeThreshold']
NudgeChannelName = config['NudgeChannelName']
LobbyThreshold = config['LobbyThreshold']
LobbyCooldown = config['LobbyCooldown']
PingRemovalTimer = config['PingRemovalTimer']
TeamNames = config['TeamNames']
Servers = config['Servers']
NudgeMessages = config['NudgeMessages']

# declaring other stuff
version = "v0.0.1"
ReactionIntervalsSeconds = []
Units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
serverinfo = []
LobbyTimers = []
CurrentLobbyMembers = []
CurrentLobbyMemberIDs = []
utc = datetime.datetime.now(timezone.utc)
nudge_utc_ts = utc.timestamp()
LobbyActive = False
UpdatingServerInfo = False
allowed_mentions = discord.AllowedMentions(roles=True)
lbsetCommandList = ["BotGame", "LobbyMessageTitle", "LobbyMessageColor", "NappingMessageColor",
                    "LobbyThreshold", "LobbyCooldown", "PingRemovalTimer", "NudgeMessageEnable",
                    "NudgeCooldown", "NudgeThreshold"]


# convert config time intervals into seconds (once) for use in asyncio.sleep
def convert_to_seconds(s):
    return int(timedelta(**{
        Units.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())


LobbyCooldownSeconds = convert_to_seconds(LobbyCooldown)
PingRemovalTimerSeconds = convert_to_seconds(PingRemovalTimer)
NaptimeRemainingSeconds = LobbyCooldownSeconds - PingRemovalTimerSeconds
NudgeCooldownSeconds = convert_to_seconds(NudgeCooldown)

# cleanup functions to delete any messages and remove all users from lobby roles
class Bot(discord.Bot):
    async def cleanup(self):
        print('------------------------------------------------------')
        print(f'Shutting down {bot.user}...')
        print("Cleaning up messages...")
        if LobbyActive:
            await active_lobby_message.delete()
        else:
            lobby_message = main_lobby_message
            await lobby_message.delete()
        print("Removing roles...")
        for member in lobby_role.members:
            await member.remove_roles(lobby_role)

    async def close(self):
        await self.cleanup()
        print("Goodbye...")
        await super().close()


# need members intent for detecting removal of reactions
intents = discord.Intents.default()
intents.members = True
bot = Bot(intents=intents)


class LobbyTimer:
    def __init__(self, reacter, display_name, user_id, timer, timer_end_utc, reacted_message_id, reaction_utc, reaction_emoji):
        self.reacter = reacter
        self.display_name = display_name
        self.user_id = user_id
        self.timer = timer
        self.timer_end_utc = timer_end_utc
        self.reacted_message_id = reacted_message_id
        self.reaction_utc = reaction_utc
        self.reaction_emoji = reaction_emoji


@bot.command(name="lbset", description="Change setting values")
async def lbset(ctx, setting: discord.Option(autocomplete=discord.utils.basic_autocomplete(lbsetCommandList)), value):
    if bot_admin_role in ctx.author.roles:
        print(f'Received command from {ctx.author.display_name}, executing command...')
        global LobbyCooldown
        global LobbyCooldownSeconds
        global PingRemovalTimer
        global PingRemovalTimerSeconds
        global NaptimeRemainingSeconds
        if setting.casefold() == "botgame":
            global BotGame
            BotGame = value
            await ctx.respond(f'BotGame has been set to "{BotGame}"')
            print(f'BotGame changed to {BotGame} by {ctx.author.display_name}')
            if LobbyActive:
                await bot.change_presence(status=discord.Status.idle, activity=discord.Game(f"{BotGame}"))
                print(f'Updated discord presence to playing {BotGame}')

        elif setting.casefold() == "lobbymessagetitle":
            global LobbyMessageTitle
            LobbyMessageTitle = value
            await ctx.respond(f'LobbyMessageTitle has been set to "{LobbyMessageTitle}"')
            print(f'LobbyMessageTitle changed to {LobbyMessageTitle} by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        elif setting.casefold() == "lobbymessagecolor":
            global LobbyMessageColor
            LobbyMessageColor = value
            await ctx.respond(f'LobbyMessageColor has been set to "{LobbyMessageColor}"')
            print(f'LobbyMessageColor changed to {LobbyMessageColor} by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        elif setting.casefold() == "nappingmessagecolor":
            global NappingMessageColor
            NappingMessageColor = value
            await ctx.respond(f'NappingMessageColor has been set to "{NappingMessageColor}"')
            print(f'NappingMessageColor changed to {NappingMessageColor} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbythreshold":
            global LobbyThreshold
            LobbyThreshold = value
            await ctx.respond(f'LobbyThreshold has been set to {LobbyThreshold}')
            print(f'LobbyThreshold changed to {LobbyThreshold} by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        elif setting.casefold() == "lobbycooldown":
            LobbyCooldown = value
            LobbyCooldownSeconds = convert_to_seconds(LobbyCooldown)
            NaptimeRemainingSeconds = LobbyCooldownSeconds - PingRemovalTimerSeconds
            await ctx.respond(f'LobbyCooldown has been set to {LobbyCooldown}')
            print(f'LobbyCooldown changed to {LobbyCooldown} ({LobbyCooldownSeconds}s) by {ctx.author.display_name}')

        elif setting.casefold() == "pingremovaltimer":
            PingRemovalTimer = value
            PingRemovalTimerSeconds = convert_to_seconds(PingRemovalTimer)
            NaptimeRemainingSeconds = LobbyCooldownSeconds - PingRemovalTimerSeconds
            await ctx.respond(f'PingRemovalTimer has been set to {PingRemovalTimer}')
            print(f'PingRemovalTimer changed to {PingRemovalTimer} ({PingRemovalTimerSeconds}s) by {ctx.author.display_name}')

        elif setting.casefold() == "nudgemessageenable":
            global NudgeMessageEnable
            NudgeMessageEnable = value
            await ctx.respond(f'NudgeMessageEnable has been set to {NudgeMessageEnable}')
            print(f'NudgeMessageEnable changed to {NudgeMessageEnable} by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        elif setting.casefold() == "nudgecooldown":
            global NudgeCooldown
            global NudgeCooldownSeconds
            NudgeCooldown = value
            NudgeCooldownSeconds = convert_to_seconds(NudgeCooldown)
            await ctx.respond(f'NudgeCooldown has been set to {NudgeCooldown}')
            print(f'NudgeCooldown changed to {NudgeCooldown} ({NudgeCooldownSeconds}s) by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        elif setting.casefold() == "nudgethreshold":
            global NudgeThreshold
            NudgeThreshold = value
            await ctx.respond(f'NudgeThreshold has been set to {NudgeThreshold}')
            print(f'NudgeThreshold changed to {NudgeThreshold} by {ctx.author.display_name}')
            await update_msg(main_lobby_message)

        else:
            await ctx.respond("I don't have that setting, please try again")
            print(f'Received command from {ctx.author.display_name} but I did not understand it :(')
    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received command from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.command(name="lbcfg", description="Sends a DM with current configuration settings")
async def lbcfg(ctx):
    if bot_admin_role in ctx.author.roles:
        print(f'Received cfg request from {ctx.author.display_name}, sending them a message...')
        await ctx.author.send(f'Current configuration:\n'
                              f'Version: {version}\n'
                              f'BotTimezone: {BotTimezone}\n'
                              f'BotGame: {BotGame}\n'
                              f'BotAdminRole : {BotAdminRole}\n'
                              f'LobbyChannelName: {LobbyChannelName}\n'
                              f'LobbyRole: {LobbyRole}\n'
                              f'LobbyMessageTitle: {LobbyMessageTitle}\n'
                              f'LobbyMessageColor: {LobbyMessageColor}\n'
                              f'NappingMessageColor: {NappingMessageColor}\n'
                              f'NudgeMessageEnable: {NudgeMessageEnable}\n'
                              f'NudgeCooldown: {NudgeCooldown}\n'
                              f'NudgeThreshold: {NudgeThreshold}\n'
                              f'NudgeChannelName: {NudgeChannelName}\n'
                              f'LobbyThreshold: {LobbyThreshold}\n'
                              f'LobbyCooldown: {LobbyCooldown}\n'
                              f'PingRemovalTimer: {PingRemovalTimer}\n'
                              f'TeamNames: {TeamNames}\n'
                              f'Some settings hidden, please edit config file')
        await ctx.respond('Check your DMs')
        print(f'Sent config readout to {ctx.author.display_name}')

    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received cfg request from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.command(name="lbreset", description="Kick all existing members and reset lobby")
async def lbreset(ctx):
    global LobbyActive
    if bot_admin_role in ctx.author.roles:
        print(f'Received reset request from {ctx.author.display_name}, resetting...')
        for member in lobby_role.members:
            await member.remove_roles(lobby_role)
            print(f'Removed {member.display_name} from {lobby_role.name}')
        if LobbyActive:
            await active_lobby_message.delete()
            LobbyActive = False
        else:
            await main_lobby_message.delete()
        await initialize_lobby_message()
        await update_msg(main_lobby_message)
        await ctx.respond('Lobby reset!', ephemeral=True)
        print(f'Lobby reset via /lbreset by {ctx.author.display_name}')
    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received reset request from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


# run once at bot start
@bot.event
async def on_ready():
    print('------------------------------------------------------')
    print(f'erkston/lobby-bot-dl {version}')
    systemtime = datetime.datetime.now()
    bottime = datetime.datetime.now(ZoneInfo(BotTimezone))
    print(f'System Time: {systemtime.strftime("%Y-%m-%d %H:%M:%S")} Bot Time: {bottime.strftime("%Y-%m-%d %H:%M:%S")} (Timezone: {BotTimezone})')
    print('Config options:')
    print(f'LobbyChannelName: {LobbyChannelName}')
    print(f'LobbyRole: {LobbyRole}')
    print(f'BotGame: {BotGame}')
    print(f'BotAdminRole: {BotAdminRole}')
    print(f'LobbyMessageTitle: {LobbyMessageTitle}')
    print(f'LobbyMessageColor: {LobbyMessageColor}')
    print(f'NappingMessageColor: {NappingMessageColor}')
    print(f'NudgeMessageEnable: {NudgeMessageEnable}')
    print(f'NudgeCooldown: {NudgeCooldown}')
    print(f'NudgeThreshold: {NudgeThreshold}')
    print(f'NudgeChannelName: {NudgeChannelName}')
    print(f'LobbyThreshold: {LobbyThreshold}')
    print(f'LobbyCooldown: {LobbyCooldown}')
    print(f'PingRemovalTimer: {PingRemovalTimer}')
    for i in range(len(TeamNames)):
        print(f'TeamNames[{i}]: {TeamNames[i]}')
    for i in range(len(Servers)):
        print(f'Servers[{i}]: {Servers[i]}')
    for i in range(len(NudgeMessages)):
        print(f'NudgeMessages[{i}]: {NudgeMessages[i]}')
    print('------------------------------------------------------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'{bot.user} is connected to the following guild(s):')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')

    global lobby_channel
    global nudge_channel
    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.name == LobbyChannelName:
                lobby_channel = channel
                print(f'Lobby Channel found: #{lobby_channel.name} (ID: {lobby_channel.id})')
            if channel.name == NudgeChannelName:
                nudge_channel = channel
                print(f'Nudge Channel found: #{nudge_channel.name} (ID: {nudge_channel.id})')

    global lobby_role
    global persistent_lobby_role
    global bot_admin_role
    for guild in bot.guilds:
        for role in guild.roles:
            if role.name == LobbyRole:
                lobby_role = role
                print(f'Lobby Role found: "{lobby_role.name}" (ID: {lobby_role.id})')
            if role.name == BotAdminRole:
                bot_admin_role = role
                print(f'Bot Admin Role found: "{bot_admin_role.name}" (ID: {bot_admin_role.id})')

    print('------------------------------------------------------')
    print('Checking for old lobby messages to delete...')
    async for message in lobby_channel.history(limit=20):
        if message.author == bot.user:
            print(f'Found old message from {bot.user}, deleting it')
            await message.delete()
        else:
            print(f'Found old message from {message.author}, leaving it alone')
    print('Finished checking for old messages')
    print('------------------------------------------------------')

    await initialize_lobby_message()

    await mainloop.start(main_lobby_message)


# force update server info and refresh discord message every minute
@tasks.loop(minutes=1)
async def mainloop(lobby_message):
    await update_msg(lobby_message)


async def initialize_lobby_message():
    print('Initializing lobby message')
    embed = discord.Embed(title='Reticulating Splines...', color=0xb4aba0)
    global main_lobby_message
    main_lobby_message = await lobby_channel.send(embed=embed)
    print(f'Lobby message ID {main_lobby_message.id}')
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f"#{lobby_channel}"))
    print('Updated discord status')


async def is_message_deleted(channel, message_id):
    try:
        await channel.fetch_message(message_id)
        return False
    except discord.errors.NotFound:
        # if a NotFound error appears, the message is either not in this channel or deleted
        return True


async def update_msg(lobby_message):
    if LobbyActive:
        now = datetime.datetime.now(ZoneInfo(BotTimezone))
        print(f'Lobby is active, no need to update message ' + now.strftime("%Y-%m-%d %H:%M:%S"))
        return
    else:
        # needed if the message has changed since first run
        lobby_message = main_lobby_message
        await update_lobby_members()
        # pause a second for members to update
        await asyncio.sleep(1)
        # get lobby members and format into nice string for discord embed
        current_lobby_size = len(CurrentLobbyMembers)
        s = ", "
        lobby_members_string = s.join(CurrentLobbyMembers)
        discorders_required = int(LobbyThreshold) - current_lobby_size
        if not lobby_members_string:
            lobby_members_string = "None"
        # if the threshold is not met AND lobby is not already active, display lobby info in embed
        if current_lobby_size < int(LobbyThreshold) and LobbyActive is False:
            print(
                f'Lobby threshold not met ({current_lobby_size}<{LobbyThreshold}), displaying lobby information')
            embed = discord.Embed(title=f'{LobbyMessageTitle}',
                                  description='Pings will be sent once ' + LobbyThreshold + ' players are ready \nCurrently ' + str(
                                      discorders_required) + ' more needed here!',
                                  color=int(LobbyMessageColor, 16))
            embed.add_field(name='Players in lobby (' + str(current_lobby_size) + "/" + str(
                LobbyThreshold) + '):', value=lobby_members_string,
                            inline=False)
            embed.add_field(name='\u200b', value='\u200b', inline=False)
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text='Last updated')
            await lobby_message.edit(embed=embed, view=LobbyButtons())
            now = datetime.datetime.now(ZoneInfo(BotTimezone))
            print(f'Lobby message updated ' + now.strftime("%Y-%m-%d %H:%M:%S"))
            if int(LobbyThreshold) - current_lobby_size <= int(NudgeThreshold):
                if distutils.util.strtobool(NudgeMessageEnable):
                    print(f'We are below the nudge threshold ({LobbyThreshold}-{current_lobby_size}<={NudgeThreshold}), attempting to nudge')
                    await nudge()
                else:
                    print(f'We are below the nudge threshold but NudgeMessageEnable is {NudgeMessageEnable}, doing nothing')
            else:
                print(f'We need more than {NudgeThreshold} players, not nudging')
        else:
            print(f'Lobby threshold met! ({current_lobby_size}>={LobbyThreshold})')
            await activate_lobby(lobby_message)
        return


# runs when lobby threshold is met
async def activate_lobby(lobby_message):
    global LobbyActive
    global active_lobby_message
    # check if the lobby has previously been launched (to prevent multiple notifications)
    if not LobbyActive:
        LobbyActive = True
        # delete old lobby message and send a new message (can't notify role members in edits)
        await lobby_message.delete()
        print(f'Old lobby message deleted')
        # no mentions allowed in embeds, so this has to be ugly :(
        active_lobby_message = await lobby_channel.send(
            f'\n {lobby_role.mention} \n**TIME TO PLAY**\n\n Check your DMs for connect info',
            allowed_mentions=allowed_mentions)

        print(f'Lobby launched! Message ID: {active_lobby_message.id}')
        await bot.change_presence(status=discord.Status.idle, activity=discord.Game(f"{BotGame}"))
        print(f'Updated discord presence to playing {BotGame}')
        print(f'Sending DMs with team and connect info...')
        connect_string = "".join(["`connect ", str(Servers[0][0]), ":", str(Servers[0][1]), "`"])
        teamsize = int(LobbyThreshold)/2
        i=1
        for member in lobby_role.members:
            if i <= teamsize:
                await member.send(f"Please join {TeamNames[0]} \n {connect_string}")
                i += 1
            else:
                await member.send(f"Please join {TeamNames[1]} \n {connect_string}")
                i += 1

        print(f'Sleeping for {PingRemovalTimer} before removing ping message')
        await asyncio.sleep(PingRemovalTimerSeconds)
        print(f'PingRemovalTimer expired, removing ping message')
        embed = discord.Embed(title='Lobby on cooldown',
                              description=f'{bot.user.display_name} is napping, lobby will return after {LobbyCooldown}',
                              color=int(NappingMessageColor, 16))
        await active_lobby_message.edit(embed=embed, content='')
        print(f'Napping notification sent, sleeping until LobbyCooldown ({LobbyCooldown}) has passed since pings')
        await asyncio.sleep(NaptimeRemainingSeconds)
        print(f'My nap is over! LobbyCooldown ({LobbyCooldown}) has passed since pings were sent. Resetting lobby...')
        print(f'Removing all role members...')
        for member in lobby_role.members:
            await member.remove_roles(lobby_role)
            print(f'Removed {member.display_name} from {lobby_role.name}')

        await active_lobby_message.delete()
        LobbyActive = False
        for member in lobby_role.members:
            print(f'{member.display_name} still had lobby role, removing them...')
            await member.remove_roles(lobby_role)

        await initialize_lobby_message()
        await update_msg(main_lobby_message)
        return
    else:
        # if we are here that means the lobby threshold is met, but notifications have already been sent, do nothing
        print(f'Lobby active but pings have already been sent, doing nothing...')
        return


async def update_lobby_members():
    CurrentLobbyMembers.clear()
    CurrentLobbyMemberIDs.clear()
    for member in lobby_role.members:
        CurrentLobbyMembers.append(str(member.display_name))
        CurrentLobbyMemberIDs.append(member.id)
    if not CurrentLobbyMembers:
        print(f'Lobby is currently empty :(')
    else:
        print(f'Current lobby members are:')
        print(" ".join(CurrentLobbyMembers))


async def nudge():
    global nudge_utc_ts
    global nudge_channel
    global NudgeMessages
    utc = datetime.datetime.now(timezone.utc)
    utc_timestamp = utc.timestamp()
    if utc_timestamp - nudge_utc_ts > NudgeCooldownSeconds:
        print(f'{NudgeCooldown} has passed since last nudge, sending new nudge')
        await nudge_channel.send(f'{random.choice(NudgeMessages)} {lobby_channel.mention}')
        utc = datetime.datetime.now(timezone.utc)
        nudge_utc_ts = utc.timestamp()
    else:
        print(f'{NudgeCooldown} has not passed since last nudge, doing nothing')


class LobbyButtons(discord.ui.View):
    @discord.ui.button(label="Join/Leave Lobby", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        interactor = interaction.user

        if lobby_role not in interactor.roles:
            await interactor.add_roles(lobby_role)
            await interaction.response.send_message("You have been added!", ephemeral=True)
            await update_msg(main_lobby_message)
        else:
            await interactor.remove_roles(lobby_role)
            await interaction.response.send_message("You have been removed!", ephemeral=True)
            await update_msg(main_lobby_message)

bot.run(DiscordBotToken)
