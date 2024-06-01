# lobby-bot-dl
import asyncio
import datetime
from datetime import timezone
import distutils
from distutils import util
import random
from zoneinfo import ZoneInfo
import discord
import json
import re
import os
from datetime import timedelta
import classes

with open("config/config.json", "r") as jsonfile:
    config = json.load(jsonfile)
DiscordBotToken = config['DiscordBotToken']
BotTimezone = config['BotTimezone']
BotGame = config['BotGame']
BotAdminRole = config['BotAdminRole']
LobbyChannelName = config['LobbyChannelName']
LobbyRole = config['LobbyRole']
LobbyRolePing = config['LobbyRolePing']
LobbyAutoLaunch = config['LobbyAutoLaunch']
LobbyAutoReset = config['LobbyAutoReset']
LobbyMessageTitle = config['LobbyMessageTitle']
LobbyMessageColor = config['LobbyMessageColor']
ActiveMessageColor = config['ActiveMessageColor']
LobbyThreshold = config['LobbyThreshold']
LobbyCooldown = config['LobbyCooldown']
TeamNames = config['TeamNames']

version = "v0.0.5"
Units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
utc = datetime.datetime.now(timezone.utc)
Lobbies = []
Presets = []
presets_string = ""
LobbyCount = 0
allowed_mentions = discord.AllowedMentions(roles=True)
lbsetCommandList = ["BotGame", "LobbyAutoReset", "LobbyRolePing", "LobbyAutoLaunch", "LobbyMessageTitle", "LobbyMessageColor", "ActiveMessageColor",
                    "LobbyThreshold", "LobbyCooldown"]
lbcomCommandList = ["GetCfg", "ReloadPresets"]


def load_presets():
    global Presets, presets_string
    Presets = ["default"]
    presets_string = ""
    for file in os.listdir("config/presets/"):
        if file.endswith(".json"):
            Presets.append(os.path.splitext(file)[0])
        presets_string = ", ".join(Presets)
    print(f'Presets found: {presets_string}')
    return


load_presets()


class Bot(discord.Bot):
    async def cleanup(self):
        print('------------------------------------------------------')
        print(f'Shutting down {bot.user}...')
        print("Cleaning up messages...")
        while len(Lobbies) > 1:
            if not await is_message_deleted(lobby_channel, Lobbies[1].message_id):
                lobby_message = await lobby_channel.fetch_message(Lobbies[1].message_id)
                await lobby_message.delete()
            if not await is_message_deleted(Lobbies[1].host.dm_channel, Lobbies[1].admin_msg_id):
                admin_message = await Lobbies[1].host.dm_channel.fetch_message(Lobbies[1].admin_msg_id)
                await admin_message.delete()
            Lobbies.pop(1)
        async for message in lobby_channel.history(limit=50):
            if message.author == bot.user:
                print(f'Found old message from {bot.user}, deleting it')
                await message.delete()

    async def close(self):
        await self.cleanup()
        print("Goodbye...")
        await super().close()


intents = discord.Intents.default()
bot = Bot(intents=intents)


@bot.command(name="lbset", description="Change default setting values")
async def lbset(ctx, setting: discord.Option(description="Setting name", autocomplete=discord.utils.basic_autocomplete(lbsetCommandList)), value: discord.Option(description="New setting value")):
    if bot_admin_role in ctx.author.roles:
        print(f'Received lbset command from {ctx.author.display_name}, executing command...')
        global LobbyCooldown
        global LobbyCooldownSeconds
        if setting.casefold() == "botgame":
            global BotGame
            BotGame = value
            await ctx.respond(f'BotGame has been set to "{BotGame}"', ephemeral=True)
            print(f'BotGame changed to {BotGame} by {ctx.author.display_name}')
            await bot.change_presence(status=discord.Status.idle, activity=discord.Game(f"{BotGame}"))
            print(f'Updated discord presence to playing {BotGame}')

        elif setting.casefold() == "lobbyroleping":
            global LobbyRolePing
            LobbyRolePing = value
            await ctx.respond(f'LobbyRolePing has been set to "{LobbyRolePing}"', ephemeral=True)
            print(f'LobbyRolePing changed to {LobbyRolePing} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbyautolaunch":
            global LobbyAutoLaunch
            LobbyAutoLaunch = value
            await ctx.respond(f'LobbyAutoLaunch has been set to "{LobbyAutoLaunch}"', ephemeral=True)
            print(f'LobbyAutoLaunch changed to {LobbyAutoLaunch} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbyautoreset":
            global LobbyAutoReset
            LobbyAutoReset = value
            await ctx.respond(f'LobbyAutoReset has been set to "{LobbyAutoReset}"', ephemeral=True)
            print(f'LobbyAutoReset changed to {LobbyAutoReset} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbymessagetitle":
            global LobbyMessageTitle
            LobbyMessageTitle = value
            await ctx.respond(f'LobbyMessageTitle has been set to "{LobbyMessageTitle}"', ephemeral=True)
            print(f'LobbyMessageTitle changed to {LobbyMessageTitle} by {ctx.author.display_name}')
            await update_all_lobby_messages()

        elif setting.casefold() == "lobbymessagecolor":
            global LobbyMessageColor
            LobbyMessageColor = value
            await ctx.respond(f'LobbyMessageColor has been set to "{LobbyMessageColor}"', ephemeral=True)
            print(f'LobbyMessageColor changed to {LobbyMessageColor} by {ctx.author.display_name}')
            await update_all_lobby_messages()

        elif setting.casefold() == "activemessagecolor":
            global ActiveMessageColor
            ActiveMessageColor = value
            await ctx.respond(f'ActiveMessageColor has been set to "{ActiveMessageColor}"', ephemeral=True)
            print(f'ActiveMessageColor changed to {ActiveMessageColor} by {ctx.author.display_name}')
            await update_all_lobby_messages()

        elif setting.casefold() == "lobbythreshold":
            global LobbyThreshold
            LobbyThreshold = value
            await ctx.respond(f'LobbyThreshold has been set to {LobbyThreshold}', ephemeral=True)
            print(f'LobbyThreshold changed to {LobbyThreshold} by {ctx.author.display_name}')
            await update_all_lobby_messages()

        elif setting.casefold() == "lobbycooldown":
            LobbyCooldown = value
            LobbyCooldownSeconds = convert_to_seconds(LobbyCooldown)
            await ctx.respond(f'LobbyCooldown has been set to {LobbyCooldown}', ephemeral=True)
            print(f'LobbyCooldown changed to {LobbyCooldown} ({LobbyCooldownSeconds}s) by {ctx.author.display_name}')

        else:
            await ctx.respond("I don't have that setting, please try again", ephemeral=True)
            print(f'Received command from {ctx.author.display_name} but I did not understand it :(')
    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received command from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.command(name="lbcom", description="Send command")
async def lbcom(ctx, command: discord.Option(description="Command to execute", autocomplete=discord.utils.basic_autocomplete(lbcomCommandList))):
    if bot_admin_role in ctx.author.roles:
        global presets_string
        print(f'Received lbcom command from {ctx.author.display_name}, executing command...')
        if command.casefold() == "getcfg":
            await ctx.author.send(f'Current default configuration:\n'
                                  f'Version: {version}\n'
                                  f'BotTimezone: {BotTimezone}\n'
                                  f'BotGame: {BotGame}\n'
                                  f'BotAdminRole : {BotAdminRole}\n'
                                  f'LobbyChannelName: {LobbyChannelName}\n'
                                  f'LobbyRole: {LobbyRole}\n'
                                  f'LobbyRolePing: {LobbyRolePing}\n'
                                  f'LobbyAutoLaunch: {LobbyAutoLaunch}\n'
                                  f'LobbyAutoReset: {LobbyAutoReset}\n'
                                  f'LobbyMessageTitle: {LobbyMessageTitle}\n'
                                  f'LobbyMessageColor: {LobbyMessageColor}\n'
                                  f'ActiveMessageColor: {ActiveMessageColor}\n'
                                  f'LobbyThreshold: {LobbyThreshold}\n'
                                  f'LobbyCooldown: {LobbyCooldown}\n'
                                  f'TeamNames: {TeamNames}\n'
                                  f'Some settings hidden, please edit config file\n'
                                  f'Available presets: {presets_string}')
            await ctx.respond('Check your DMs', ephemeral=True)
            print(f'Sent default config readout to {ctx.author.display_name}')

        elif command.casefold() == "reloadpresets":
            load_presets()
            await ctx.respond(f'Presets reloaded. Available: {presets_string}', ephemeral=True)
            print(f'{ctx.author.display_name} reloaded presets. Available: {presets_string}')

    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received command from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.command(name="startlobby", description="Start a lobby")
async def startlobby(ctx, server: discord.Option(str, description="Enter the servers address and port (address:port) "),
                     password: discord.Option(str, description="Enter the servers password"),
                     preset: discord.Option(str, description=f"Available presets: {presets_string} (Case sensitive)")):
    if bot_admin_role in ctx.author.roles:
        global lobby_role, LobbyRolePing, LobbyAutoLaunch
        selected_preset = preset
        if selected_preset in Presets:
            print(f"startlobby: Found Selected preset: {selected_preset}")
        else:
            print(f"startlobby: Could not find selected preset: {selected_preset}, aborting command")
            await ctx.respond("Could not find that preset, please try again", ephemeral=True)
            return
        global LobbyCount, Lobbies
        LobbyCount += 1
        lobby_number = LobbyCount
        print(f'lobby{lobby_number}: Received lobby request from {ctx.author.display_name}, starting Lobby #{lobby_number}')

        if selected_preset != "default":
            with open(f"config/presets/{selected_preset}.json", "r") as jsonfile:
                tempconfig = json.load(jsonfile)
                TempLobbyRole = tempconfig['LobbyRole']
                for guild in bot.guilds:
                    for role in guild.roles:
                        if role.name == TempLobbyRole:
                            temp_lobby_role = role
                            print(f'lobby{lobby_number}: Lobby Role found: "{temp_lobby_role.name}" (ID: {temp_lobby_role.id})')
                lobby_role_ping = tempconfig['LobbyRolePing']
                lobby_auto_launch = tempconfig['LobbyAutoLaunch']
                lobby_message = await initialize_lobby(lobby_number, temp_lobby_role, distutils.util.strtobool(lobby_role_ping))
        else:
            lobby_message = await initialize_lobby(lobby_number, lobby_role, distutils.util.strtobool(LobbyRolePing))
            lobby_auto_launch = LobbyAutoLaunch

        await ctx.respond(f'Lobby #{lobby_number} started', ephemeral=True)
        if distutils.util.strtobool(lobby_auto_launch):
            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby will launch automatically when full')
        else:
            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='After it fills, lobby will wait until you press the green button to launch')
        embed.add_field(name='Server', value=server, inline=True)
        embed.add_field(name='Password', value=password, inline=True)
        embed.add_field(name='Preset', value=preset, inline=True)
        admin_panel_msg = await ctx.author.send(embed=embed, view=AdminButtons(timeout=None))

        if selected_preset != "default":
            with open(f"config/presets/{selected_preset}.json", "r") as jsonfile:
                tempconfig = json.load(jsonfile)
                Lobbies.append(classes.Lobby(lobby_number, lobby_message.id, ctx.author, admin_panel_msg.id, server, password, [],
                    [], [], 0, temp_lobby_role, tempconfig['LobbyRolePing'], tempconfig['LobbyAutoLaunch'],
                    tempconfig['LobbyAutoReset'], tempconfig['LobbyMessageTitle'], tempconfig['LobbyMessageColor'],
                    tempconfig['ActiveMessageColor'], tempconfig['LobbyThreshold'], tempconfig['LobbyCooldown'], tempconfig['TeamNames'], 0))
                print(f'lobby{lobby_number}: Lobby created with preset {selected_preset}')
        else:
            global LobbyAutoReset, LobbyMessageTitle, LobbyMessageColor, ActiveMessageColor, LobbyThreshold, LobbyCooldown, TeamNames
            Lobbies.append(classes.Lobby(lobby_number, lobby_message.id, ctx.author, admin_panel_msg.id, server, password, [],
                [], [], 0, lobby_role, LobbyRolePing, LobbyAutoLaunch, LobbyAutoReset,
                LobbyMessageTitle, LobbyMessageColor, ActiveMessageColor, LobbyThreshold, LobbyCooldown, TeamNames, 0))
            print(f'lobby{lobby_number}: Lobby created with default config')
        await update_message(lobby_number)

    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received startlobby request from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.event
async def on_ready():
    print('------------------------------------------------------')
    print(f'erkston/lobby-bot-dl {version}')
    systemtime = datetime.datetime.now()
    bottime = datetime.datetime.now(ZoneInfo(BotTimezone))
    print(f'System Time: {systemtime.strftime("%Y-%m-%d %H:%M:%S")} Bot Time: {bottime.strftime("%Y-%m-%d %H:%M:%S")} (Timezone: {BotTimezone})')
    print(f'Available presets: {presets_string}')
    print('Default config options:')
    print(f'BotGame: {BotGame}')
    print(f'BotAdminRole: {BotAdminRole}')
    print(f'LobbyChannelName: {LobbyChannelName}')
    print(f'LobbyRole: {LobbyRole}')
    print(f'LobbyRolePing: {LobbyRolePing}')
    print(f'LobbyAutoLaunch: {LobbyAutoLaunch}')
    print(f'LobbyAutoReset: {LobbyAutoReset}')
    print(f'LobbyMessageTitle: {LobbyMessageTitle}')
    print(f'LobbyMessageColor: {LobbyMessageColor}')
    print(f'ActiveMessageColor: {ActiveMessageColor}')
    print(f'LobbyThreshold: {LobbyThreshold}')
    print(f'LobbyCooldown: {LobbyCooldown}')
    for i in range(len(TeamNames)):
        print(f'TeamNames[{i}]: {TeamNames[i]}')
    print('------------------------------------------------------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'{bot.user} is connected to the following guild(s):')
    for guild in bot.guilds:
        print(f'{guild.name} (id: {guild.id})')

    global lobby_channel
    for guild in bot.guilds:
        for channel in guild.channels:
            if channel.name == LobbyChannelName:
                lobby_channel = channel
                print(f'Lobby Channel found: #{lobby_channel.name} (ID: {lobby_channel.id})')

    global lobby_role
    global bot_admin_role
    for guild in bot.guilds:
        for role in guild.roles:
            if role.name == LobbyRole:
                lobby_role = role
                print(f'Lobby Role found: "{lobby_role.name}" (ID: {lobby_role.id})')
            if role.name == BotAdminRole:
                bot_admin_role = role
                print(f'Bot Admin Role found: "{bot_admin_role.name}" (ID: {bot_admin_role.id})')

    print('Checking for old lobby messages to delete...')
    async for message in lobby_channel.history(limit=50):
        if message.author == bot.user:
            print(f'Found old message from {bot.user}, deleting it')
            await message.delete()
    print('------------------------------------------------------')
    Lobbies.append(classes.Lobby(0, 0, "host", 0, "0.0.0.0", "pass",
                         [], [], [], 0, "role", "True",
                         "True", "True", "Title", "FFFFFF",
                         "FFFFFF", 0, 0, 0, 0))
    print('Startup complete, awaiting command')


async def initialize_lobby(lobby_number, temp_lobby_role, lobby_role_ping):
    print(f'lobby{lobby_number}: Initializing lobby message')
    if lobby_role_ping:
        print(f'lobby{lobby_number}: LobbyRolePing is {lobby_role_ping}, sending ping')
        await lobby_channel.send(f'{temp_lobby_role.mention}')
    embed = discord.Embed(title='Reticulating Splines...', color=0xb4aba0)
    lobby_message = await lobby_channel.send(embed=embed)
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f"#{lobby_channel}"))
    return lobby_message


async def update_message(lobby_number):
    global lobby_channel
    sapp_players = []
    ambr_players = []
    fill_players = []
    for player in Lobbies[lobby_number].sapp_players:
        sapp_players.append(str(player.display_name))
    for player in Lobbies[lobby_number].ambr_players:
        ambr_players.append(str(player.display_name))
    for player in Lobbies[lobby_number].fill_players:
        fill_players.append(str(player.display_name))
    sapp_players_string = "\n".join(sapp_players)
    if not sapp_players_string:
        sapp_players_string = "None"
    ambr_players_string = "\n".join(ambr_players)
    if not ambr_players_string:
        ambr_players_string = "None"
    fill_players_string = ", ".join(fill_players)
    if not fill_players_string:
        fill_players_string = "None"
    current_lobby_size = len(sapp_players) + len(ambr_players) + len(fill_players)

    if current_lobby_size < int(Lobbies[lobby_number].lobby_threshold) and not Lobbies[lobby_number].active:
        print(f'lobby{lobby_number}: Lobby threshold not met ({current_lobby_size}<{Lobbies[lobby_number].lobby_threshold}), displaying lobby information')
        embed = discord.Embed(title=f'{Lobbies[lobby_number].lobby_message_title}',
                              description='Join using buttons below, server info will be sent via DM when the lobby is full. '
                                          'Currently ' + str(current_lobby_size) + '/' + str(Lobbies[lobby_number].lobby_threshold) + ' players',
                              color=int(Lobbies[lobby_number].lobby_message_color, 16))
        embed.add_field(name=Lobbies[lobby_number].team_names[0], value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].team_names[1], value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name='EITHER', value=fill_players_string, inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=LobbyButtons(timeout=None))
    elif current_lobby_size == int(Lobbies[lobby_number].lobby_threshold) and Lobbies[lobby_number].active:
        print(f'lobby{lobby_number}: Lobby activated, displaying final player list')
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            embed = discord.Embed(title=f'Lobby is starting!', description='Check your DMs for connect info', color=int(ActiveMessageColor, 16))
        else:
            embed = discord.Embed(title=f'Lobby is starting!', description='Waiting for host to launch...', color=int(ActiveMessageColor, 16))
        embed.add_field(name=Lobbies[lobby_number].team_names[0], value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].team_names[1], value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=None)

    else:
        print(f'lobby{lobby_number}: Lobby threshold met! ({current_lobby_size}/{Lobbies[lobby_number].lobby_threshold})')
        await activate_lobby(lobby_number)
    return


async def activate_lobby(lobby_number):
    if not Lobbies[lobby_number].active:
        Lobbies[lobby_number].active = 1
        await assign_teams(lobby_number)
        await update_message(lobby_number)
        await bot.change_presence(status=discord.Status.idle, activity=discord.Game(f"{BotGame}"))
        if not distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            print(f'lobby{lobby_number}: LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, waiting for admin')
            await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is full and waiting for you to start")
            return
        else:
            await launch_lobby(lobby_number)
    else:
        print(f'lobby{lobby_number}: Lobby was already launched, doing nothing...')
        return


async def launch_lobby(lobby_number):
    await send_lobby_info(lobby_number)
    await asyncio.sleep(convert_to_seconds(Lobbies[lobby_number].lobby_cooldown))
    print(f'lobby{lobby_number}: LobbyCooldown ({Lobbies[lobby_number].lobby_cooldown}) has passed since lobby was started')
    if Lobbies[lobby_number].manual_mode:
        print(f'lobby{lobby_number}: Admin has previously manually reset this lobby, doing nothing')
        return
    if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_reset):
        print(f'lobby{lobby_number}: LobbyAutoReset is {Lobbies[lobby_number].lobby_auto_reset}, resetting...')
        await reset_lobby(lobby_number)
        return
    else:
        print(f'lobby{lobby_number}: LobbyAutoReset is {Lobbies[lobby_number].lobby_auto_reset}, closing lobby...')
        await close_lobby(lobby_number)
        return


async def get_lobby_number(interaction):
    global Lobbies
    i = 0
    while i < len(Lobbies):
        if interaction.message.id == Lobbies[i].message_id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received lobby button press from {interaction.user.display_name}')
        i += 1
    i = 0
    while i < len(Lobbies):
        if interaction.message.id == Lobbies[i].admin_msg_id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received admin button press from {interaction.user.display_name}')
        i += 1
    return lobby_number


async def assign_teams(lobby_number):
    print(f'lobby{lobby_number}: Assigning fill players to teams')
    random.shuffle(Lobbies[lobby_number].fill_players)
    for player in Lobbies[lobby_number].fill_players:
        if len(Lobbies[lobby_number].sapp_players) < int(Lobbies[lobby_number].lobby_threshold)/2:
            Lobbies[lobby_number].sapp_players.append(player)
        else:
            Lobbies[lobby_number].ambr_players.append(player)
    Lobbies[lobby_number].fill_players.clear()


async def shuffle_teams(lobby_number):
    print(f'lobby{lobby_number}: Shuffling teams')
    player_list = []
    for player in Lobbies[lobby_number].sapp_players:
        player_list.append(player)
    for player in Lobbies[lobby_number].ambr_players:
        player_list.append(player)
    for player in Lobbies[lobby_number].fill_players:
        player_list.append(player)
    Lobbies[lobby_number].sapp_players.clear()
    Lobbies[lobby_number].ambr_players.clear()
    Lobbies[lobby_number].fill_players.clear()
    random.shuffle(player_list)
    i = 0
    while i < len(player_list)/2:
        Lobbies[lobby_number].sapp_players.append(player_list[i])
        i += 1
    while i < len(player_list):
        Lobbies[lobby_number].ambr_players.append(player_list[i])
        i += 1
    await update_message(lobby_number)


async def send_lobby_info(lobby_number):
    print(f'lobby{lobby_number}: Sending DMs with team and connect info...')
    connect_string = "".join(["`connect ", str(Lobbies[lobby_number].server), "`"])
    for player in Lobbies[lobby_number].sapp_players:
        await player.send(
            f"Please join {Lobbies[lobby_number].team_names[0]} \n {connect_string} \n Password: {Lobbies[lobby_number].password}")
    for player in Lobbies[lobby_number].ambr_players:
        await player.send(
            f"Please join {Lobbies[lobby_number].team_names[1]} \n {connect_string} \n Password: {Lobbies[lobby_number].password}")


async def update_all_lobby_messages():
    lobby_number = 1
    while lobby_number < len(Lobbies):
        if not await is_message_deleted(lobby_channel, Lobbies[lobby_number].message_id):
            await update_message(lobby_number)
            lobby_number += 1


async def reset_lobby(lobby_number):
    Lobbies[lobby_number].active = 0
    Lobbies[lobby_number].sapp_players.clear()
    Lobbies[lobby_number].ambr_players.clear()
    Lobbies[lobby_number].fill_players.clear()
    await update_message(lobby_number)


async def close_lobby(lobby_number):
    if not await is_message_deleted(lobby_channel, Lobbies[lobby_number].message_id):
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.delete()
    if not await is_message_deleted(Lobbies[1].host.dm_channel, Lobbies[lobby_number].admin_msg_id):
        admin_message = await Lobbies[1].host.dm_channel.fetch_message(Lobbies[lobby_number].admin_msg_id)
        await admin_message.delete()


async def is_message_deleted(channel, message_id):
    try:
        await channel.fetch_message(message_id)
        return False
    except discord.errors.NotFound:
        return True


async def convert_to_seconds(s):
    return int(timedelta(**{
        Units.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())


class DMmodal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Text", style=discord.InputTextStyle.long))

    async def callback(self, interaction):
        lobby_number = await get_lobby_number(interaction)
        text = self.children[0].value
        for player in Lobbies[lobby_number].sapp_players:
            await player.send(f"{text}")
        for player in Lobbies[lobby_number].ambr_players:
            await player.send(f"{text}")
        for player in Lobbies[lobby_number].fill_players:
            await player.send(f"{text}")
        await interaction.response.send_message(f"Sent DM to Lobby {lobby_number} players: \n {text}", ephemeral=True)


class LobbyButtons(discord.ui.View):
    @discord.ui.button(label="Sapphire", style=discord.ButtonStyle.blurple)
    async def sapp_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        if interactor in Lobbies[lobby_number].ambr_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].team_names[1]}", ephemeral=True)
            return
        if interactor in Lobbies[lobby_number].fill_players:
            await interaction.response.send_message(f"You are already filling teams", ephemeral=True)
            return

        i = 0
        interactor_already_here = False
        while i < len(Lobbies[lobby_number].sapp_players):
            if interactor.id == Lobbies[lobby_number].sapp_players[i].id:
                interactor_already_here = True
                del Lobbies[lobby_number].sapp_players[i]
            i += 1
        if interactor_already_here:
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].team_names[0]}", ephemeral=True)
            await update_message(lobby_number)
            return

        if len(Lobbies[lobby_number].sapp_players) == int(Lobbies[lobby_number].lobby_threshold)/2:
            await interaction.response.send_message(f"{Lobbies[lobby_number].team_names[0]} is full, please join a different team", ephemeral=True)
            return
        elif interactor not in Lobbies[lobby_number].sapp_players:
            Lobbies[lobby_number].sapp_players.append(interactor)
            await interaction.response.send_message(f"Added to {Lobbies[lobby_number].team_names[0]}", ephemeral=True)
            await update_message(lobby_number)

    @discord.ui.button(label="Amber", style=discord.ButtonStyle.red)
    async def ambr_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        if interactor in Lobbies[lobby_number].sapp_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].team_names[0]}", ephemeral=True)
            return
        if interactor in Lobbies[lobby_number].fill_players:
            await interaction.response.send_message(f"You are already filling teams", ephemeral=True)
            return

        i = 0
        interactor_already_here = False
        while i < len(Lobbies[lobby_number].ambr_players):
            if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                interactor_already_here = True
                del Lobbies[lobby_number].ambr_players[i]
            i += 1
        if interactor_already_here:
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].team_names[1]}", ephemeral=True)
            await update_message(lobby_number)
            return

        if len(Lobbies[lobby_number].ambr_players) == int(Lobbies[lobby_number].lobby_threshold)/2:
            await interaction.response.send_message(f"{Lobbies[lobby_number].team_names[1]} is full, please join a different team", ephemeral=True)
            return
        if interactor not in Lobbies[lobby_number].ambr_players:
            Lobbies[lobby_number].ambr_players.append(interactor)
            await interaction.response.send_message(f"Added to {Lobbies[lobby_number].team_names[1]}", ephemeral=True)
            await update_message(lobby_number)
        else:
            i = 0
            while i < len(Lobbies[lobby_number].ambr_players):
                if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                    del Lobbies[lobby_number].ambr_players[i]
                i += 1
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].team_names[1]}", ephemeral=True)
            await update_message(lobby_number)

    @discord.ui.button(label="Either", style=discord.ButtonStyle.green)
    async def fill_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        if interactor in Lobbies[lobby_number].sapp_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].team_names[0]}", ephemeral=True)
            return
        if interactor in Lobbies[lobby_number].ambr_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].team_names[1]}", ephemeral=True)
            return
        if interactor not in Lobbies[lobby_number].fill_players:
            Lobbies[lobby_number].fill_players.append(interactor)
            await interaction.response.send_message(f"Added to fill", ephemeral=True)
            await update_message(lobby_number)
        else:
            i = 0
            while i < len(Lobbies[lobby_number].fill_players):
                if interactor.id == Lobbies[lobby_number].fill_players[i].id:
                    del Lobbies[lobby_number].fill_players[i]
                i += 1
            await interaction.response.send_message(f"Removed from fill", ephemeral=True)
            await update_message(lobby_number)


class AdminButtons(discord.ui.View):
    @discord.ui.button(label="Launch Lobby", style=discord.ButtonStyle.green, row=1)
    async def launch_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received launch command from {interaction.user.display_name}')
        if Lobbies[lobby_number].active:
            await interaction.response.send_message(f"Launching Lobby {lobby_number}", ephemeral=True)
            await launch_lobby(lobby_number)
        else:
            await interaction.response.send_message(f"Can't launch yet, lobby is not full", ephemeral=True)

    @discord.ui.button(label="Reset Lobby", style=discord.ButtonStyle.blurple, row=1)
    async def reset_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received lobby reset command from {interaction.user.display_name}')
        Lobbies[lobby_number].manual_mode = 1
        await reset_lobby(lobby_number)
        await interaction.response.send_message(f"Lobby {lobby_number} reset", ephemeral=True)

    @discord.ui.button(label="Close Lobby", style=discord.ButtonStyle.red, row=1)
    async def close_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received lobby close command from {interaction.user.display_name}')
        await close_lobby(lobby_number)
        await interaction.response.send_message(f"Lobby {lobby_number} closed", ephemeral=True)

    @discord.ui.button(label="Shuffle Teams", style=discord.ButtonStyle.secondary, row=2)
    async def shuffle_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received shuffle command from {interaction.user.display_name}')
        await shuffle_teams(lobby_number)
        await interaction.response.send_message(f"Teams have been shuffled", ephemeral=True)

    @discord.ui.button(label="Resend connect info", style=discord.ButtonStyle.secondary, row=2)
    async def resend_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received resend info command from {interaction.user.display_name}')
        if Lobbies[lobby_number].active:
            await send_lobby_info(lobby_number)
            await interaction.response.send_message(f"Connect info resent", ephemeral=True)
        else:
            await interaction.response.send_message(f"Lobby is not active, sent nothing", ephemeral=True)

    @discord.ui.button(label="DM Players", style=discord.ButtonStyle.secondary, row=2)
    async def dm_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received player dm command from {interaction.user.display_name}')
        await interaction.response.send_modal(DMmodal(title=f"DM Lobby {lobby_number} Players"))


bot.run(DiscordBotToken)
