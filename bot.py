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
SapphireTeamName = config['SapphireTeamName']
AmberTeamName = config['AmberTeamName']
EitherTeamName = config['EitherTeamName']
EnableHeroDraft = config['EnableHeroDraft']

with open("config/heroes.json", "r") as heroesjsonfile:
    heroesjson = json.load(heroesjsonfile)
Heroes = heroesjson['Heroes']

version = "v0.1.0"
Units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
utc = datetime.datetime.now(timezone.utc)
Lobbies = []
Bans = []
Presets = []
presets_string = ""
LobbyCount = 0
allowed_mentions = discord.AllowedMentions(roles=True)
lbsetCommandList = ["BotGame", "LobbyAutoReset", "LobbyRolePing", "LobbyAutoLaunch", "LobbyMessageTitle", "LobbyMessageColor", "ActiveMessageColor",
                    "LobbyThreshold", "LobbyCooldown", "SapphireTeamName", "AmberTeamName", "EitherTeamName", "EnableHeroDraft"]
lbcomCommandList = ["GetCfg", "ReloadPresets"]

with open("bans.json", "r") as bansjsonfile:
    JSONBans = json.load(bansjsonfile)
i = 0
for ban in JSONBans:
    Bans.append([ban[0], ban[1], ban[2]])


def load_presets():
    global Presets, presets_string
    Presets = ["default"]
    presets_string = ""
    for file in os.listdir("config/presets/"):
        if file.endswith(".json"):
            Presets.append(os.path.splitext(file)[0])
        presets_string = ", ".join(Presets)
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
            if not await is_message_deleted(Lobbies[1].drafter.dm_channel, Lobbies[1].draft_msg.id):
                draft_message = await Lobbies[1].drafter.dm_channel.fetch_message(Lobbies[1].draft_msg.id)
                await draft_message.delete()
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
intents.members = True
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

        elif setting.casefold() == "lobbymessagecolor":
            global LobbyMessageColor
            LobbyMessageColor = value
            await ctx.respond(f'LobbyMessageColor has been set to "{LobbyMessageColor}"', ephemeral=True)
            print(f'LobbyMessageColor changed to {LobbyMessageColor} by {ctx.author.display_name}')

        elif setting.casefold() == "activemessagecolor":
            global ActiveMessageColor
            ActiveMessageColor = value
            await ctx.respond(f'ActiveMessageColor has been set to "{ActiveMessageColor}"', ephemeral=True)
            print(f'ActiveMessageColor changed to {ActiveMessageColor} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbythreshold":
            global LobbyThreshold
            LobbyThreshold = value
            await ctx.respond(f'LobbyThreshold has been set to {LobbyThreshold}', ephemeral=True)
            print(f'LobbyThreshold changed to {LobbyThreshold} by {ctx.author.display_name}')

        elif setting.casefold() == "lobbycooldown":
            LobbyCooldown = value
            LobbyCooldownSeconds = convert_to_seconds(LobbyCooldown)
            await ctx.respond(f'LobbyCooldown has been set to {LobbyCooldown}', ephemeral=True)
            print(f'LobbyCooldown changed to {LobbyCooldown} ({LobbyCooldownSeconds}s) by {ctx.author.display_name}')

        elif setting.casefold() == "sapphireteamname":
            global SapphireTeamName
            SapphireTeamName = value
            await ctx.respond(f'SapphireTeamName has been set to {SapphireTeamName}', ephemeral=True)
            print(f'SapphireTeamName changed to {SapphireTeamName} by {ctx.author.display_name}')

        elif setting.casefold() == "amberteamname":
            global AmberTeamName
            AmberTeamName = value
            await ctx.respond(f'AmberTeamName has been set to {AmberTeamName}', ephemeral=True)
            print(f'AmberTeamName changed to {AmberTeamName} by {ctx.author.display_name}')

        elif setting.casefold() == "eitherteamname":
            global EitherTeamName
            EitherTeamName = value
            await ctx.respond(f'EitherTeamName has been set to {EitherTeamName}', ephemeral=True)
            print(f'EitherTeamName changed to {EitherTeamName} by {ctx.author.display_name}')

        elif setting.casefold() == "enableherodraft":
            global EnableHeroDraft
            EnableHeroDraft = value
            await ctx.respond(f'EnableHeroDraft has been set to {EnableHeroDraft}', ephemeral=True)
            print(f'EnableHeroDraft changed to {EnableHeroDraft} by {ctx.author.display_name}')

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
                                  f'SapphireTeamName: {SapphireTeamName}\n'
                                  f'AmberTeamName: {AmberTeamName}\n'
                                  f'EitherTeamName: {EitherTeamName}\n'
                                  f'EnableHeroDraft: {EnableHeroDraft}\n'
                                  f'Heroes: {Heroes}\n'
                                  f'Some settings hidden, please edit config file\n'
                                  f'Available presets: {presets_string}\n'
                                  f'Presets will override the above settings')

            await ctx.respond('Check your DMs', ephemeral=True)
            print(f'Sent default config readout to {ctx.author.display_name}')

        elif command.casefold() == "reloadpresets":
            load_presets()
            await ctx.respond(f'Presets reloaded. Available: {presets_string}', ephemeral=True)
            print(f'{ctx.author.display_name} reloaded presets. Available: {presets_string}')
        else:
            await ctx.respond(f'Command not found', ephemeral=True)
    else:
        await ctx.respond('You do not have appropriate permissions! Leave me alone!!')
        print(f'Received command from {ctx.author.display_name} who does not have admin role "{bot_admin_role}"!')


@bot.command(name="lbban", description="Toggle ban status of a user")
async def lbban(ctx, user_id: discord.Option(description="20 digit User ID of the user to ban or unban")):
    if bot_admin_role in ctx.author.roles:
        print(f'Received lbban command from {ctx.author.display_name}, executing command...')
        player = bot_guild.get_member(int(f"{user_id}"))
        banned = await banunban_player(player)
        if banned:
            await ctx.respond(f"Player {player.display_name} banned", ephemeral=True)
        else:
            await ctx.respond(f"Player {player.display_name} unbanned", ephemeral=True)
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
                lobby_message = await initialize_lobby(lobby_number, temp_lobby_role, distutils.util.strtobool(lobby_role_ping))
        else:
            lobby_message = await initialize_lobby(lobby_number, lobby_role, distutils.util.strtobool(LobbyRolePing))

        await ctx.respond(f'Lobby #{lobby_number} started', ephemeral=True)

        embed = discord.Embed(title=f"Starting Lobby {lobby_number} Admin Panel...")
        admin_panel_msg = await ctx.author.send(embed=embed, view=None)

        if selected_preset != "default":
            with open(f"config/presets/{selected_preset}.json", "r") as jsonfile:
                tempconfig = json.load(jsonfile)
                Lobbies.append(classes.Lobby(lobby_number, lobby_message.id, ctx.author, admin_panel_msg.id, server, password, preset, [],
                                             [], [], [], [], [], 0,
                                             0, 0, "drafter", "hero",0, 0,
                                             temp_lobby_role, tempconfig['LobbyRolePing'], tempconfig['LobbyAutoLaunch'],
                                             tempconfig['LobbyAutoReset'], tempconfig['LobbyMessageTitle'], tempconfig['LobbyMessageColor'],
                                             tempconfig['ActiveMessageColor'], tempconfig['LobbyThreshold'], tempconfig['LobbyCooldown'],
                                             tempconfig['SapphireTeamName'], tempconfig['AmberTeamName'], tempconfig['EitherTeamName'],
                                             0, "none", tempconfig['EnableHeroDraft'], discord.Message))
                print(f'lobby{lobby_number}: Lobby created with preset {selected_preset}')
        else:
            global LobbyAutoReset, LobbyMessageTitle, LobbyMessageColor, ActiveMessageColor, LobbyThreshold, LobbyCooldown, SapphireTeamName, AmberTeamName, EitherTeamName, EnableHeroDraft, Heroes
            Lobbies.append(classes.Lobby(lobby_number, lobby_message.id, ctx.author, admin_panel_msg.id, server, password, preset, [], [],
                                         [], [], [], [], 0,0, 0, "drafter",
                                         "hero", 0, 0, lobby_role, LobbyRolePing, LobbyAutoLaunch, LobbyAutoReset, LobbyMessageTitle,
                                         LobbyMessageColor, ActiveMessageColor, LobbyThreshold,LobbyCooldown, SapphireTeamName, AmberTeamName, EitherTeamName,
                                         0, "none", EnableHeroDraft, discord.Message))
            print(f'lobby{lobby_number}: Lobby created with default config')
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)

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
    print(f'SapphireTeamName: {SapphireTeamName}')
    print(f'AmberTeamName: {AmberTeamName}')
    print(f'EitherTeamName: {EitherTeamName}')
    print(f'EnableHeroDraft: {EnableHeroDraft}')
    print('------------------------------------------------------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'{bot.user} is connected to the following guild(s):')
    global bot_guild
    for guild in bot.guilds:
        bot_guild = guild
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
                                 "preset", [], [], [], [], [], [],
                                 0,  0,  0, "drafter", "none",
                                 0, 0, "role", "True","True",
                                 "True", "Title", "FFFFFF","FFFFFF",
                                 0, 0, 0, 0, 0, 0,
                                 "none", "True", discord.Message))
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


async def update_admin_panel(lobby_number):
    if not await is_message_deleted(Lobbies[lobby_number].host.dm_channel, Lobbies[lobby_number].admin_msg_id):
        admin_panel_msg = await Lobbies[lobby_number].host.dm_channel.fetch_message(Lobbies[lobby_number].admin_msg_id)
    else:
        print(f'lobby{lobby_number}: Admin panel message not found')
        return
    if Lobbies[lobby_number].active == 0:
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open and draft will begin automatically when full')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open and will launch automatically when full')
        else:
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open, draft will not begin until you hit Proceed')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open but will not launch until you hit Proceed')
    else:
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                if not Lobbies[lobby_number].drafting_heroes and not Lobbies[lobby_number].draft_complete:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full, hero draft will begin automatically')
                elif Lobbies[lobby_number].drafting_heroes:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft is ongoing and will launch automatically when complete')
                elif Lobbies[lobby_number].draft_complete:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft complete, lobby will launch automaticalls')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full and will launch automatically')
        else:
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                if not Lobbies[lobby_number].drafting_heroes and not Lobbies[lobby_number].draft_complete:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full, hero draft will begin when you hit Proceed')
                elif Lobbies[lobby_number].drafting_heroes:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft is ongoing, lobby will not launch until you hit Proceed')
                elif Lobbies[lobby_number].draft_complete:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft complete but will not launch until you hit Proceed')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full but will not launch until you hit Proceed')

    if Lobbies[lobby_number].launched == 1:
        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is launched! DMs were sent to all players')

    setting_string = "Server\nPassword\nPreset\nLobbyAutoLaunch\nLobbyAutoReset\nLobbyMessageTitle\nSapphireTeamName\nAmberTeamName\nEitherTeamName\nLobbyThreshold\nLobbyCooldown\nEnableHeroDraft"
    value_string = (f"{Lobbies[lobby_number].server}\n{Lobbies[lobby_number].password}\n{Lobbies[lobby_number].preset}\n{Lobbies[lobby_number].lobby_auto_launch}\n"
                    f"{Lobbies[lobby_number].lobby_auto_reset}\n{Lobbies[lobby_number].lobby_message_title}\n{Lobbies[lobby_number].sapphire_name}\n"
                    f"{Lobbies[lobby_number].amber_name}\n{Lobbies[lobby_number].either_name}\n{Lobbies[lobby_number].lobby_threshold}\n"
                    f"{Lobbies[lobby_number].lobby_cooldown}\n{Lobbies[lobby_number].enable_hero_draft}\n")

    embed.add_field(name='Setting', value=setting_string, inline=True)
    embed.add_field(name='Value', value=value_string, inline=True)
    await admin_panel_msg.edit(embed=embed, view=AdminButtons(timeout=None))
    return


async def update_message(lobby_number):
    global lobby_channel
    sapp_players = []
    ambr_players = []
    fill_players = []
    i = 0
    while i < len(Lobbies[lobby_number].sapp_players):
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].draft_complete:
            sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name) + " - " + Lobbies[lobby_number].sapp_heroes[i])
        else:
            sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name))
        i += 1
    i = 0
    while i < len(Lobbies[lobby_number].ambr_players):
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].draft_complete:
            ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name) + " - " + Lobbies[lobby_number].ambr_heroes[i])
        else:
            ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name))
        i += 1

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

    if current_lobby_size < int(Lobbies[lobby_number].lobby_threshold):
        Lobbies[lobby_number].active = 0
        print(f'lobby{lobby_number}: Lobby threshold not met ({current_lobby_size}<{Lobbies[lobby_number].lobby_threshold}), displaying lobby information')
        embed = discord.Embed(title=f'{Lobbies[lobby_number].lobby_message_title}',
                              description='Join using buttons below, server info will be sent via DM when the lobby is full. '
                                          'Currently ' + str(current_lobby_size) + '/' + str(Lobbies[lobby_number].lobby_threshold) + ' players',
                              color=int(Lobbies[lobby_number].lobby_message_color, 16))
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name=Lobbies[lobby_number].either_name, value=fill_players_string, inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=LobbyButtons(timeout=None))
        return
    elif current_lobby_size >= int(Lobbies[lobby_number].lobby_threshold) and Lobbies[lobby_number].active and not Lobbies[lobby_number].launched:
        if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and not Lobbies[lobby_number].draft_complete:
            if not Lobbies[lobby_number].drafting_heroes:
                print(f'lobby{lobby_number}: Lobby is waiting for host to start draft')
                embed = discord.Embed(title=f'Hero draft is about to start', description="Waiting for host...", color=int(ActiveMessageColor, 16))
            else:
                print(f'lobby{lobby_number}: Lobby is in hero draft phase, displaying draft information')
                embed = discord.Embed(title=f'Hero draft is ongoing', description="You will receive a DM when it's your turn to draft", color=int(ActiveMessageColor, 16))
        elif distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and Lobbies[lobby_number].draft_complete:
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                print(f'lobby{lobby_number}: Draft is complete and LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, launching lobby')
                await launch_lobby(lobby_number)
                return
            else:
                print(f'lobby{lobby_number}: Draft is complete and LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, updating title')
                embed = discord.Embed(title=f'Hero draft is complete!', description='Waiting for host...', color=int(ActiveMessageColor, 16))
        elif not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                print(f'lobby{lobby_number}: Draft is not enabled and LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, launching lobby')
                await launch_lobby(lobby_number)
                return
            else:
                print(f'lobby{lobby_number}: Draft is not enabled and LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, updating title')
                embed = discord.Embed(title=f'Lobby is full!', description='Waiting for host...', color=int(ActiveMessageColor, 16))
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)

        if Lobbies[lobby_number].active and not Lobbies[lobby_number].drafting_heroes and not Lobbies[lobby_number].draft_complete and not Lobbies[lobby_number].launched:
            await lobby_message.edit(embed=embed, view=LeaveButton(timeout=None))
            return
        await lobby_message.edit(embed=embed, view=None)
        return

    elif current_lobby_size >= int(Lobbies[lobby_number].lobby_threshold) and Lobbies[lobby_number].active and Lobbies[lobby_number].launched:
        print(f'lobby{lobby_number}: Lobby activated and launched, displaying final player list')
        embed = discord.Embed(title=f'Lobby is starting!', description='Check your DMs for connect info', color=int(ActiveMessageColor, 16))
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=None)
        return
    else:
        print(f'lobby{lobby_number}: Lobby threshold met! ({current_lobby_size}/{Lobbies[lobby_number].lobby_threshold})')
        await activate_lobby(lobby_number)


async def activate_lobby(lobby_number):
    if not Lobbies[lobby_number].active:
        Lobbies[lobby_number].active = 1
        await assign_teams(lobby_number)
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)
        if not distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            if not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                print(f'lobby{lobby_number}: LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, waiting for host to launch')
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is full and waiting for you to launch the lobby (Click Proceed)")
                return
            else:
                print(f'lobby{lobby_number}: LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, waiting for host to start draft')
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is full and waiting for you to start the hero draft (Click Proceed)")
                return
        else:
            if not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                print(f'lobby{lobby_number}: LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, launching lobby')
                await launch_lobby(lobby_number)
                return
            else:
                print(f'lobby{lobby_number}: LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, launching lobby')
                await draft_heroes(lobby_number)
                return
    else:
        print(f'lobby{lobby_number}: Lobby was already started, doing nothing...')
        return


async def launch_lobby(lobby_number):
    if not Lobbies[lobby_number].launched:
        await bot.change_presence(status=discord.Status.idle, activity=discord.Game(f"{BotGame}"))
        Lobbies[lobby_number].launched = 1
        await send_lobby_info(lobby_number)
        await update_admin_panel(lobby_number)
        await update_message(lobby_number)
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
    else:
        print(f'lobby{lobby_number}: Lobby was already launched, doing nothing...')
        return


async def draft_heroes(lobby_number):
    if Lobbies[lobby_number].drafting_heroes:
        print(f'lobby{lobby_number}: Draft was already started!')
        return
    else:
        Lobbies[lobby_number].drafting_heroes = 1
        print(f'lobby{lobby_number}: Beginning hero draft...')
        random.shuffle(Lobbies[lobby_number].sapp_players)
        random.shuffle(Lobbies[lobby_number].ambr_players)
        Lobbies[lobby_number].sapp_heroes.clear()
        Lobbies[lobby_number].ambr_heroes.clear()
        Lobbies[lobby_number].picked_heroes.clear()
        i = 0
        while i < len(Lobbies[lobby_number].sapp_players):
            Lobbies[lobby_number].sapp_heroes.append("not drafted")
            Lobbies[lobby_number].ambr_heroes.append("not drafted")
            i += 1
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)
        i = 0
        while i < len(Lobbies[lobby_number].sapp_players):
            Lobbies[lobby_number].waiting_for_pick = 1
            Lobbies[lobby_number].drafter = Lobbies[lobby_number].sapp_players[i]
            await get_player_pick(lobby_number, Lobbies[lobby_number].sapp_players[i])
            while Lobbies[lobby_number].waiting_for_pick:
                await asyncio.sleep(1)
            Lobbies[lobby_number].sapp_heroes[i] = Lobbies[lobby_number].selected_hero
            Lobbies[lobby_number].picked_heroes.append(Lobbies[lobby_number].selected_hero)
            await update_message(lobby_number)

            Lobbies[lobby_number].waiting_for_pick = 1
            Lobbies[lobby_number].drafter = Lobbies[lobby_number].ambr_players[i]
            await get_player_pick(lobby_number, Lobbies[lobby_number].ambr_players[i])
            while Lobbies[lobby_number].waiting_for_pick:
                await asyncio.sleep(1)
            Lobbies[lobby_number].ambr_heroes[i] = Lobbies[lobby_number].selected_hero
            Lobbies[lobby_number].picked_heroes.append(Lobbies[lobby_number].selected_hero)
            await update_message(lobby_number)
            i += 1
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            Lobbies[lobby_number].drafting_heroes = 0
            Lobbies[lobby_number].draft_complete = 1
            await launch_lobby(lobby_number)
        else:
            Lobbies[lobby_number].drafting_heroes = 0
            Lobbies[lobby_number].draft_complete = 1
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} hero draft is complete and waiting for you to launch the lobby (Click Proceed)")


async def get_player_pick(lobby_number, player):
    Lobbies[lobby_number].selected_hero = ""
    picked_heroes_string = "\n".join(Lobbies[lobby_number].picked_heroes)
    if not picked_heroes_string:
        picked_heroes_string = "None"
    draft_msg = await player.send(f"Please select a hero\nHeroes already picked: {picked_heroes_string}", view=HeroSelect(timeout=None))
    Lobbies[lobby_number].draft_msg = draft_msg


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
    i = 0
    while i < len(Lobbies):
        if interaction.message.id == Lobbies[i].draft_msg.id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received draft button press from {interaction.user.display_name}')
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
            f"\nPlease join {Lobbies[lobby_number].sapphire_name}\n{connect_string}\nPassword: {Lobbies[lobby_number].password}")
    for player in Lobbies[lobby_number].ambr_players:
        await player.send(
            f"\nPlease join {Lobbies[lobby_number].amber_name}\n{connect_string}\nPassword: {Lobbies[lobby_number].password}")


async def update_all_lobby_messages():
    lobby_number = 1
    while lobby_number < len(Lobbies):
        if not await is_message_deleted(lobby_channel, Lobbies[lobby_number].message_id):
            await update_message(lobby_number)
            lobby_number += 1


async def reset_lobby(lobby_number):
    Lobbies[lobby_number].active = 0
    Lobbies[lobby_number].drafting_heroes = 0
    Lobbies[lobby_number].waiting_for_pick = 0
    Lobbies[lobby_number].draft_complete = 0
    Lobbies[lobby_number].launched = 0
    Lobbies[lobby_number].drafter = 0
    Lobbies[lobby_number].sapp_players.clear()
    Lobbies[lobby_number].ambr_players.clear()
    Lobbies[lobby_number].fill_players.clear()
    Lobbies[lobby_number].sapp_heroes.clear()
    Lobbies[lobby_number].ambr_heroes.clear()
    Lobbies[lobby_number].picked_heroes.clear()
    await update_message(lobby_number)
    await update_admin_panel(lobby_number)
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f"#{lobby_channel}"))


async def close_lobby(lobby_number):
    if not await is_message_deleted(lobby_channel, Lobbies[lobby_number].message_id):
        lobby_message = await lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.delete()
    if not await is_message_deleted(Lobbies[1].host.dm_channel, Lobbies[lobby_number].admin_msg_id):
        admin_message = await Lobbies[1].host.dm_channel.fetch_message(Lobbies[lobby_number].admin_msg_id)
        await admin_message.delete()


async def kick_player(lobby_number, user_id):
    if Lobbies[lobby_number].launched:
        return 0
    player = bot_guild.get_member(int(f"{user_id}"))
    i = 0
    while i < len(Lobbies[lobby_number].sapp_players):
        if Lobbies[lobby_number].sapp_players[i].id == player.id:
            Lobbies[lobby_number].sapp_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
        i += 1
    i = 0
    while i < len(Lobbies[lobby_number].ambr_players):
        if Lobbies[lobby_number].ambr_players[i].id == player.id:
            Lobbies[lobby_number].ambr_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
        i += 1
    i = 0
    while i < len(Lobbies[lobby_number].fill_players):
        if Lobbies[lobby_number].fill_players[i].id == player.id:
            Lobbies[lobby_number].fill_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
        i += 1
    return 0


async def banunban_player(player):
    i = 0
    for existing_ban in Bans:
        if player.id == existing_ban[2]:
            Bans.pop(i)
            print(f'Player {player.display_name} unbanned')
            await write_bans_to_file()
            return 0
        i += 1
    i = 1
    while i < len(Lobbies):
        await kick_player(i, player.id)
        i += 1
    Bans.append([player.display_name, player.name, player.id])
    print(f'Player {player.display_name} banned')
    await write_bans_to_file()
    return 1


async def write_bans_to_file():
    bans_json_object = json.dumps(Bans, indent=4)
    with open("bans.json", "w") as bansjsonfile:
        bansjsonfile.write(bans_json_object)


async def is_message_deleted(channel, message_id):
    try:
        await channel.fetch_message(message_id)
        return False
    except discord.errors.NotFound:
        return True


def convert_to_seconds(s):
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


class KickModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="User ID", style=discord.InputTextStyle.short))

    async def callback(self, interaction):
        lobby_number = await get_lobby_number(interaction)
        userid = self.children[0].value
        player = bot_guild.get_member(int(f"{userid}"))
        kicked = await kick_player(lobby_number, player.id)
        if kicked:
            await interaction.response.send_message(f"Player {player.display_name} kicked", ephemeral=True)
            return
        else:
            await interaction.response.send_message(f"Player {player.display_name} not found or could not be kicked", ephemeral=True)
            return


class BanModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="User ID", style=discord.InputTextStyle.short))

    async def callback(self, interaction):
        userid = self.children[0].value
        player = bot_guild.get_member(int(f"{userid}"))
        banned = await banunban_player(player)
        if banned:
            await interaction.response.send_message(f"Player {player.display_name} banned", ephemeral=True)
        else:
            await interaction.response.send_message(f"Player {player.display_name} unbanned", ephemeral=True)


class SettingModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="New Value", style=discord.InputTextStyle.short))

    async def callback(self, interaction):
        lobby_number = await get_lobby_number(interaction)
        value = self.children[0].value
        if Lobbies[lobby_number].selected_setting == "none":
            await interaction.response.send_message(f"Please select a setting in the dropdown", ephemeral=True)
            return
        elif Lobbies[lobby_number].selected_setting == "Server":
            if Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby is already launched, can't change Server right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].server = value
                await interaction.response.send_message(f"Lobby {lobby_number} Server changed to {Lobbies[lobby_number].server}", ephemeral=True)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "Password":
            if Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby was already launched, can't change Password right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].password = value
                await interaction.response.send_message(f"Lobby {lobby_number} Password changed to {Lobbies[lobby_number].password}", ephemeral=True)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "LobbyAutoLaunch":
            if Lobbies[lobby_number].active or Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby is either full or already launched, can't change LobbyAutoLaunch right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].lobby_auto_launch = value
                await interaction.response.send_message(f"Lobby {lobby_number} LobbyAutoLaunch changed to {Lobbies[lobby_number].lobby_auto_launch}", ephemeral=True)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "LobbyAutoReset":
            if Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby was already launched, can't change LobbyAutoReset right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].lobby_auto_reset = value
                await interaction.response.send_message(f"Lobby {lobby_number} LobbyAutoReset changed to {Lobbies[lobby_number].lobby_auto_reset}", ephemeral=True)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "LobbyMessageTitle":
            Lobbies[lobby_number].lobby_message_title = value
            await interaction.response.send_message(f"Lobby {lobby_number} LobbyMessageTitle changed to {Lobbies[lobby_number].lobby_message_title}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "SapphireTeamName":
            Lobbies[lobby_number].sapphire_name = value
            await interaction.response.send_message(f"Lobby {lobby_number} SapphireTeamName changed to {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "AmberTeamName":
            Lobbies[lobby_number].amber_name = value
            await interaction.response.send_message(f"Lobby {lobby_number} AmberTeamName changed to {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "EitherTeamName":
            Lobbies[lobby_number].either_name = value
            await interaction.response.send_message(f"Lobby {lobby_number} EitherTeamName changed to {Lobbies[lobby_number].either_name}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "LobbyThreshold":
            if Lobbies[lobby_number].active or Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby is either full or already launched, can't change LobbyThreshold right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].lobby_threshold = value
                await interaction.response.send_message(f"Lobby {lobby_number} LobbyThreshold changed to {Lobbies[lobby_number].lobby_threshold}", ephemeral=True)
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "LobbyCooldown":
            if Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby was already launched, can't change LobbyCooldown right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].lobby_cooldown = value
                await interaction.response.send_message(f"Lobby {lobby_number} LobbyCooldown changed to {Lobbies[lobby_number].lobby_cooldown}", ephemeral=True)
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "EnableHeroDraft":
            if Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"Lobby was already launched, can't change EnableHeroDraft right now", ephemeral=True)
                return
            else:
                Lobbies[lobby_number].enable_hero_draft = value
                await interaction.response.send_message(f"Lobby {lobby_number} EnableHeroDraft changed to {Lobbies[lobby_number].enable_hero_draft}", ephemeral=True)
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                return
        else:
            await interaction.response.send_message(f"Setting not found!", ephemeral=True)


class LobbyButtons(discord.ui.View):
    @discord.ui.button(label="Sapphire", style=discord.ButtonStyle.blurple)
    async def sapp_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        for existing_ban in Bans:
            if interactor.id == existing_ban[2]:
                print(f'lobby{lobby_number}: Banned user {interactor.display_name} tried to join')
                await interaction.response.send_message(f"You are banned from this lobby", ephemeral=True)
                return
        if interactor in Lobbies[lobby_number].ambr_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].amber_name}", ephemeral=True)
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
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            await update_message(lobby_number)
            return

        if len(Lobbies[lobby_number].sapp_players) == int(Lobbies[lobby_number].lobby_threshold)/2:
            await interaction.response.send_message(f"{Lobbies[lobby_number].sapphire_name} is full, please join a different team", ephemeral=True)
            return
        elif interactor not in Lobbies[lobby_number].sapp_players:
            Lobbies[lobby_number].sapp_players.append(interactor)
            await interaction.response.send_message(f"Added to {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            await update_message(lobby_number)

    @discord.ui.button(label="Amber", style=discord.ButtonStyle.red)
    async def ambr_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        for existing_ban in Bans:
            if interactor.id == existing_ban[2]:
                print(f'lobby{lobby_number}: Banned user {interactor.display_name} tried to join')
                await interaction.response.send_message(f"You are banned from this lobby", ephemeral=True)
                return
        if interactor in Lobbies[lobby_number].sapp_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
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
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)
            return

        if len(Lobbies[lobby_number].ambr_players) == int(Lobbies[lobby_number].lobby_threshold)/2:
            await interaction.response.send_message(f"{Lobbies[lobby_number].amber_name} is full, please join a different team", ephemeral=True)
            return
        if interactor not in Lobbies[lobby_number].ambr_players:
            Lobbies[lobby_number].ambr_players.append(interactor)
            await interaction.response.send_message(f"Added to {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)
        else:
            i = 0
            while i < len(Lobbies[lobby_number].ambr_players):
                if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                    del Lobbies[lobby_number].ambr_players[i]
                i += 1
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)

    @discord.ui.button(label="Either", style=discord.ButtonStyle.green)
    async def fill_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        for existing_ban in Bans:
            if interactor.id == existing_ban[2]:
                print(f'lobby{lobby_number}: Banned user {interactor.display_name} tried to join')
                await interaction.response.send_message(f"You are banned from this lobby", ephemeral=True)
                return
        if interactor in Lobbies[lobby_number].sapp_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            return
        if interactor in Lobbies[lobby_number].ambr_players:
            await interaction.response.send_message(f"You are already on {Lobbies[lobby_number].amber_name}", ephemeral=True)
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


class HeroSelect(discord.ui.View):
    @discord.ui.select(placeholder="Select a hero", row=0, min_values=1, max_values=1, options=[discord.SelectOption(label=hero) for hero in Heroes])
    async def hero_select_callback(self, hero_select, interaction):
        lobby_number = await get_lobby_number(interaction)
        if interaction.user.id == Lobbies[lobby_number].drafter.id:
            picked_hero = hero_select.values[0]
            if picked_hero not in Lobbies[lobby_number].picked_heroes:
                Lobbies[lobby_number].selected_hero = picked_hero
                print(f"lobby{lobby_number}: Hero {Lobbies[lobby_number].selected_hero} has been picked")
                await Lobbies[lobby_number].draft_msg.edit(f"You have selected {Lobbies[lobby_number].selected_hero}", view=None)
                await interaction.response.defer()
                Lobbies[lobby_number].waiting_for_pick = 0
            else:
                await interaction.respond(f"{picked_hero} was already drafted, please pick a different hero", ephemeral=True)
        else:
            await interaction.respond(f"It is not your turn to draft", ephemeral=True)


class LeaveButton(discord.ui.View):
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.secondary, row=0)
    async def leave_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        print(f'lobby{lobby_number}: Received leave command from {interaction.user.display_name}')
        if interactor in Lobbies[lobby_number].sapp_players:
            i = 0
            while i < len(Lobbies[lobby_number].sapp_players):
                if interactor.id == Lobbies[lobby_number].sapp_players[i].id:
                    del Lobbies[lobby_number].sapp_players[i]
                i += 1
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            await update_message(lobby_number)
            return
        elif interactor in Lobbies[lobby_number].ambr_players:
            i = 0
            while i < len(Lobbies[lobby_number].ambr_players):
                if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                    del Lobbies[lobby_number].ambr_players[i]
                i += 1
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)
            return
        else:
            await interaction.response.send_message(f"You're not in this lobby", ephemeral=True)


class AdminButtons(discord.ui.View):
    @discord.ui.button(label="Proceed", style=discord.ButtonStyle.green, row=0)
    async def launch_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received proceed command from {interaction.user.display_name}')
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            await interaction.response.send_message(f"LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, this button does nothing", ephemeral=True)
            return
        if not Lobbies[lobby_number].active:
            await interaction.response.send_message(f"Can't launch yet, lobby is not full", ephemeral=True)
            return
        if Lobbies[lobby_number].active and distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and not Lobbies[lobby_number].draft_complete:
            await interaction.response.send_message(f"Starting hero draft for Lobby {lobby_number}", ephemeral=True)
            await draft_heroes(lobby_number)
            return
        if Lobbies[lobby_number].active and distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and Lobbies[lobby_number].draft_complete:
            await interaction.response.send_message(f"Launching Lobby {lobby_number}", ephemeral=True)
            await launch_lobby(lobby_number)
        if Lobbies[lobby_number].active and not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
            await interaction.response.send_message(f"Launching Lobby {lobby_number}", ephemeral=True)
            await launch_lobby(lobby_number)

    @discord.ui.button(label="Reset Lobby", style=discord.ButtonStyle.blurple, row=0)
    async def reset_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received lobby reset command from {interaction.user.display_name}')
        Lobbies[lobby_number].manual_mode = 1
        await reset_lobby(lobby_number)
        await interaction.response.send_message(f"Lobby {lobby_number} reset", ephemeral=True)

    @discord.ui.button(label="Close Lobby", style=discord.ButtonStyle.red, row=0)
    async def close_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received lobby close command from {interaction.user.display_name}')
        await close_lobby(lobby_number)
        await interaction.response.send_message(f"Lobby {lobby_number} closed", ephemeral=True)

    @discord.ui.button(label="Shuffle Teams", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received shuffle command from {interaction.user.display_name}')
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].draft_complete or Lobbies[lobby_number].launched:
            await interaction.response.send_message(f"It's too late to shuffle teams", ephemeral=True)
        else:
            await shuffle_teams(lobby_number)
            await interaction.response.send_message(f"Teams have been shuffled", ephemeral=True)

    @discord.ui.button(label="Resend connect info", style=discord.ButtonStyle.secondary, row=1)
    async def resend_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received resend info command from {interaction.user.display_name}')
        if Lobbies[lobby_number].active:
            await send_lobby_info(lobby_number)
            await interaction.response.send_message(f"Connect info resent", ephemeral=True)
        else:
            await interaction.response.send_message(f"Lobby is not active, sent nothing", ephemeral=True)

    @discord.ui.button(label="DM Players", style=discord.ButtonStyle.secondary, row=1)
    async def dm_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received player dm command from {interaction.user.display_name}')
        await interaction.response.send_modal(DMmodal(title=f"DM Lobby {lobby_number} Players"))

    @discord.ui.button(label="Kick Player", style=discord.ButtonStyle.red, row=2)
    async def kick_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received player kick command from {interaction.user.display_name}')
        await interaction.response.send_modal(KickModal(title=f"Kick Player"))

    @discord.ui.button(label="Ban/Unban Player", style=discord.ButtonStyle.red, row=2)
    async def ban_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received player ban command from {interaction.user.display_name}')
        await interaction.response.send_modal(BanModal(title=f"Ban/Unban Player"))

    @discord.ui.select(placeholder="Select a setting to change", row=3, min_values=1, max_values=1,
                       options=[
                           discord.SelectOption(
                               label="Server",
                               description="Change server address and port"
                           ),
                           discord.SelectOption(
                               label="Password",
                               description="Change server password"
                           ),
                           discord.SelectOption(
                               label="LobbyAutoLaunch",
                               description="Change auto-launch behavior"
                           ),
                           discord.SelectOption(
                               label="LobbyAutoReset",
                               description="Change auto-reset behavior"
                           ),
                           discord.SelectOption(
                               label="LobbyMessageTitle",
                               description="Change the title of the lobby message"
                           ),
                           discord.SelectOption(
                               label="SapphireTeamName",
                               description="Change the Sapphire team name"
                           ),
                           discord.SelectOption(
                               label="AmberTeamName",
                               description="Change the Amber team name"
                           ),
                           discord.SelectOption(
                               label="EitherTeamName",
                               description="Change name for fill players"
                           ),
                           discord.SelectOption(
                               label="LobbyThreshold",
                               description="Change the lobby player threshold"
                           ),
                           discord.SelectOption(
                               label="LobbyCooldown",
                               description="Change reset cooldown if LobbyAutoReset is True"
                           ),
                           discord.SelectOption(
                               label="EnableHeroDraft",
                               description="When true, teams will draft heros when lobby is full"
                           )
                       ]
                       )
    async def select_callback(self, select, interaction):
        lobby_number = await get_lobby_number(interaction)
        Lobbies[lobby_number].selected_setting = select.values[0]
        print(f"lobby{lobby_number}: Lobbies[lobby_number].selected_setting = {Lobbies[lobby_number].selected_setting}")
        await interaction.response.defer()

    @discord.ui.button(label="Change Setting", style=discord.ButtonStyle.blurple, row=4)
    async def setting_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received change setting command from {interaction.user.display_name}')
        if Lobbies[lobby_number].selected_setting == "none":
            await interaction.response.send_message(f"Please select a setting in the dropdown", ephemeral=True)
            return
        else:
            await interaction.response.send_modal(SettingModal(title=f"Change {Lobbies[lobby_number].selected_setting} Setting"))


bot.run(DiscordBotToken)
