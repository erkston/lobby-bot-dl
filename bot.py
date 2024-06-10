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


version = "v0.3.12"
Units = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
utc = datetime.datetime.now(timezone.utc)
Lobbies = []
LobbyCount = 0
allowed_mentions = discord.AllowedMentions(roles=True)
lbcomCommandList = ["ReloadPresets", "ReloadHeroes"]


def load_bans():
    global Bans
    Bans = []
    with open("bans.json", "r") as bansjsonfile:
        JSONBans = json.load(bansjsonfile)
    for ban in JSONBans:
        Bans.append([ban[0], ban[1], ban[2]])


def load_presets():
    global Presets, presets_string
    Presets = []
    presets_string = ""
    for file in os.listdir("config/presets/"):
        if file.endswith(".json"):
            Presets.append(os.path.splitext(file)[0])
        presets_string = ", ".join(Presets)
    return


def load_heroes():
    global Heroes, heroes_string
    Heroes = []
    with open("config/heroes.json", "r") as heroesjsonfile:
        heroesjson = json.load(heroesjsonfile)
    Heroes = heroesjson['Heroes']
    heroes_string = ", ".join(Heroes)


load_bans()
load_presets()
load_heroes()


class Bot(discord.Bot):
    async def cleanup(self):
        print('------------------------------------------------------')
        print(f'Shutting down {bot.user}...')
        print("Cleaning up messages...")
        while len(Lobbies) > 1:
            if not await is_message_deleted(Lobbies[1].lobby_channel, Lobbies[1].message_id):
                lobby_message = await Lobbies[1].lobby_channel.fetch_message(Lobbies[1].message_id)
                await lobby_message.delete()
            if not await is_message_deleted(Lobbies[1].host.dm_channel, Lobbies[1].admin_msg_id):
                admin_message = await Lobbies[1].host.dm_channel.fetch_message(Lobbies[1].admin_msg_id)
                await admin_message.delete()
            if not await is_message_deleted(Lobbies[1].drafter.dm_channel, Lobbies[1].draft_msg.id):
                draft_message = await Lobbies[1].drafter.dm_channel.fetch_message(Lobbies[1].draft_msg.id)
                await draft_message.delete()
            async for message in Lobbies[1].lobby_channel.history(limit=25):
                if message.author == bot.user:
                    print(f'Found old message from {bot.user}, deleting it')
                    await message.delete()
            Lobbies.pop(1)

    async def close(self):
        await self.cleanup()
        print("Goodbye...")
        await super().close()


intents = discord.Intents.default()
intents.members = True
bot = Bot(intents=intents)


@bot.command(name="lbcom", description="Send command")
async def lbcom(ctx, command: discord.Option(description="Command to execute", autocomplete=discord.utils.basic_autocomplete(lbcomCommandList))):
    if bot_admin_role in ctx.author.roles:
        global presets_string
        print(f'Received lbcom command from {ctx.author.display_name}, executing command...')
        if command.casefold() == "reloadpresets":
            load_presets()
            await ctx.respond(f'Presets reloaded. Available presets: {presets_string}', ephemeral=True)
            print(f'{ctx.author.display_name} reloaded presets. Available presets: {presets_string}')

        elif command.casefold() == "reloadheroes":
            load_heroes()
            await ctx.respond(f'Heroes reloaded. Available heroes: {heroes_string}', ephemeral=True)
            print(f'{ctx.author.display_name} reloaded heroes. Available heroes: {heroes_string}')

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
                     preset: discord.Option(str, description=f"Available presets: {presets_string} (Case sensitive)"),
                     title: discord.Option(str, description="Override the lobby message title", required=False),
                     description: discord.Option(str, description="Optional lobby description", required=False)):
    if bot_admin_role in ctx.author.roles:
        print(f"startlobby: Received command from {ctx.author.display_name}, starting lobby...")
        selected_preset = preset
        if selected_preset in Presets:
            print(f"startlobby: Found Selected preset: {selected_preset}")
        else:
            print(f"startlobby: Could not find selected preset: {selected_preset}, aborting command")
            await ctx.respond("Could not find that preset, please try again", ephemeral=True)
            return
        global LobbyCount, Lobbies, Heroes
        LobbyCount += 1
        lobby_number = LobbyCount
        print(f'lobby{lobby_number}: Received lobby request from {ctx.author.display_name}, starting Lobby #{lobby_number}')

        with open(f"config/presets/{selected_preset}.json", "r") as presetjsonfile:
            preset = json.load(presetjsonfile)
            if int(preset['LobbyThreshold']) % 2 or int(preset['LobbyThreshold']) == 0:
                print(f"startlobby: Invalid LobbyThreshold ({preset['LobbyThreshold']}), cancelling lobby")
                await ctx.respond(f'LobbyThreshold must be even and non-zero', ephemeral=True)
                LobbyCount -= 1
                return
            LobbyRole = preset['LobbyRole']
            for guild in bot.guilds:
                for role in guild.roles:
                    try:
                        int_role = int(LobbyRole)
                        if role.id == int_role:
                            lobby_role = role
                            print(f'lobby{lobby_number}: Lobby Role found: "{lobby_role.name}"')
                    except ValueError:
                        if role.name == LobbyRole:
                            lobby_role = role
                            print(f'lobby{lobby_number}: Lobby Role found: "{lobby_role.name}"')
            LobbyChannel = preset['LobbyChannel']
            for guild in bot.guilds:
                for channel in guild.channels:
                    try:
                        int_chan = int(LobbyChannel)
                        if channel.id == int_chan:
                            lobby_channel = channel
                            print(f'lobby{lobby_number}: Lobby channel found #{lobby_channel.name}')
                    except ValueError:
                        if channel.name == LobbyChannel:
                            lobby_channel = channel
                            print(f'lobby{lobby_number}: Lobby channel found #{lobby_channel.name}')
        lobby_message = await initialize_lobby(lobby_number, lobby_role, distutils.util.strtobool(preset['LobbyRolePing']), lobby_channel)
        await ctx.respond(f'Lobby #{lobby_number} started', ephemeral=True)

        embed = discord.Embed(title=f"Starting Lobby {lobby_number} Admin Panel...")
        admin_panel_msg = await ctx.author.send(embed=embed, view=None)

        if not title:
            lobby_title = preset['LobbyMessageTitle']
        else:
            lobby_title = title

        with open(f"config/presets/{selected_preset}.json", "r") as presetjsonfile:
            preset = json.load(presetjsonfile)
            Lobbies.append(classes.Lobby(lobby_number, lobby_message.id, ctx.author, admin_panel_msg.id, server, password, selected_preset, description, [],
                                         [], [], [], [], Heroes[:], [], 0,
                                         0, 0, discord.User, "hero", 0, 0,
                                         lobby_role, preset['LobbyRolePing'], preset['LobbyAutoLaunch'], preset['LobbyAutoReset'],
                                         lobby_title, preset['LobbyMessageColor'], preset['ActiveMessageColor'],
                                         preset['LobbyThreshold'], preset['LobbyCooldown'], preset['SapphireTeamName'],
                                         preset['AmberTeamName'], preset['EitherTeamName'], 0, "none",
                                         preset['EnableHeroDraft'], discord.Message, preset['EnableImageSend'], lobby_channel,
                                         preset['EnablePlayerDraft'], 0, 0, discord.User, discord.User,
                                         [], discord.User, 0, preset['EnableReadyUp'], 0, 0,
                                         [], [], [], []))
            print(f'lobby{lobby_number}: Lobby created with preset {selected_preset}')

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
    print('Config:')
    print(f'BotGame: {BotGame}')
    print(f'BotAdminRole: {BotAdminRole}')
    print(f'Heroes: {heroes_string}')
    print(f'Available presets: {presets_string}')
    print('------------------------------------------------------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'{bot.user} is connected to the following guild(s):')
    global bot_guild
    for guild in bot.guilds:
        bot_guild = guild
        print(f'{guild.name} (id: {guild.id})')
    global bot_admin_role
    for guild in bot.guilds:
        for role in guild.roles:
            try:
                int_role = int(BotAdminRole)
                if role.id == int_role:
                    bot_admin_role = role
                    print(f'Bot Admin Role found: "{bot_admin_role.name}"')
            except ValueError:
                if role.name == BotAdminRole:
                    bot_admin_role = role
                    print(f'Bot Admin Role found: "{bot_admin_role.name}"')
    Lobbies.append(classes.Lobby(0, 0, discord.User, 0, "0.0.0.0", "pass",
                                 "preset", "desc", [], [], [], [], [], [], [],
                                 0,  0,  0, discord.User, "none",
                                 0, 0, "role", "True", "True",
                                 "True", "Title", "FFFFFF","FFFFFF",
                                 0, 0, 0, 0, 0, 0,
                                 "none", "True", discord.Message, "False", 0,
                                 0, 0, 0, discord.User, discord.User, [], discord.User, 0,
                                 "True", 0, 0, [], [], [], []))
    print('Startup complete, awaiting command')
    print('------------------------------------------------------')


async def initialize_lobby(lobby_number, lobby_role, lobby_role_ping, lobby_channel):
    print(f'lobby{lobby_number}: Initializing lobby message')
    if lobby_role_ping:
        print(f'lobby{lobby_number}: LobbyRolePing is {lobby_role_ping}, sending ping')
        await lobby_channel.send(f'{lobby_role.mention}')
    embed = discord.Embed(title='Reticulating Splines...', color=0xb4aba0)
    lobby_message = await lobby_channel.send(embed=embed)
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f"#{lobby_channel.name}"))
    return lobby_message


async def update_admin_panel(lobby_number):
    if not await is_message_deleted(Lobbies[lobby_number].host.dm_channel, Lobbies[lobby_number].admin_msg_id):
        admin_panel_msg = await Lobbies[lobby_number].host.dm_channel.fetch_message(Lobbies[lobby_number].admin_msg_id)
    else:
        print(f'lobby{lobby_number}: Admin panel message not found')
        return
    if Lobbies[lobby_number].active == 0:
        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open, player draft will begin automatically')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open and will for you to begin player draft')
        elif distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open, hero draft will begin automatically')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open and will for you to begin hero draft')
        else:
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open, lobby will launch automatically when full')
            else:
                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is open and will wait for you before launching')
    else:
        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
            if not Lobbies[lobby_number].drafting_players:
                if not Lobbies[lobby_number].player_draft_completed:
                    if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full, player draft will begin automatically')
                    else:
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is full, waiting for you to begin player draft')
                else:
                    if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                        if not Lobbies[lobby_number].drafting_heroes:
                            if not Lobbies[lobby_number].hero_draft_completed:
                                if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel",description='Player draft complete, hero draft will begin automatically')
                                else:
                                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft complete, waiting for you to begin hero draft')
                            else:
                                if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel",description='Hero draft complete, lobby will launch automatically')
                                else:
                                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft complete, waiting for you to start the game')
                        else:
                            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft ongoing, lobby will launch automatically')
                            else:
                                embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft ongoing, lobby will wait for you to launch')
                    else:
                        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft complete, lobby will launch automatically')
                        else:
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft complete, waiting for you to start the game')
            else:
                if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                    if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft ongoing, hero draft will start automatically')
                    else:
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft ongoing, hero draft will wait for you to start')
                else:
                    if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft ongoing, lobby will launch automatically')
                    else:
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Player draft ongoing, lobby will wait for you to launch')
        else:
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                if not Lobbies[lobby_number].drafting_heroes:
                    if not Lobbies[lobby_number].hero_draft_completed:
                        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby full, hero draft will begin automatically')
                        else:
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby full, waiting for you to begin hero draft')
                    else:
                        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft complete, lobby will launch automatically')
                        else:
                            embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft complete, waiting for you to start the game')
                else:
                    if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft ongoing, lobby will launch automatically')
                    else:
                        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Hero draft ongoing, lobby will wait for you to launch')
            else:
                if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby full, lobby will launch automatically')
                else:
                    embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby full, waiting for you to start the game')

    if Lobbies[lobby_number].readying:
        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Players are readying up, game will start automatically')
    if Lobbies[lobby_number].launched == 1:
        embed = discord.Embed(title=f"Lobby {lobby_number} Admin Panel", description='Lobby is launched! DMs were sent to all players')

    setting_string = "Server\nPassword\nPreset\nLobbyAutoLaunch\nLobbyAutoReset\nLobbyMessageTitle\nSapphireTeamName\nAmberTeamName\nEitherTeamName\nEnableImageSend\nLobbyThreshold\nLobbyCooldown\nEnableHeroDraft\nEnablePlayerDraft\nEnableReadyUp"
    value_string = (f"{Lobbies[lobby_number].server}\n{Lobbies[lobby_number].password}\n{Lobbies[lobby_number].preset}\n{Lobbies[lobby_number].lobby_auto_launch}\n"
                    f"{Lobbies[lobby_number].lobby_auto_reset}\n{Lobbies[lobby_number].lobby_message_title}\n{Lobbies[lobby_number].sapphire_name}\n"
                    f"{Lobbies[lobby_number].amber_name}\n{Lobbies[lobby_number].either_name}\n{Lobbies[lobby_number].enable_image_send}\n{Lobbies[lobby_number].lobby_threshold}\n"
                    f"{Lobbies[lobby_number].lobby_cooldown}\n{Lobbies[lobby_number].enable_hero_draft}\n{Lobbies[lobby_number].enable_player_draft}\n{Lobbies[lobby_number].enable_ready_up}")

    embed.add_field(name='Setting', value=setting_string, inline=True)
    embed.add_field(name='Value', value=value_string, inline=True)
    await admin_panel_msg.edit(embed=embed, view=AdminButtons(lobby_number))
    return


async def update_message(lobby_number):
    sapp_players = []
    ambr_players = []
    fill_players = []
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed:
            sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name) + " - " + Lobbies[lobby_number].sapp_heroes[i])
        else:
            sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name))
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed:
            ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name) + " - " + Lobbies[lobby_number].ambr_heroes[i])
        else:
            ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name))

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

    if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
        player_pool = []
        for i in range(len(Lobbies[lobby_number].player_pool)):
            player_pool.append(str(Lobbies[lobby_number].player_pool[i].display_name))
        player_pool_string = "\n".join(player_pool)
        if not player_pool_string:
            player_pool_string = "None"
        current_lobby_size = len(player_pool) + len(sapp_players) + len(ambr_players)

    if current_lobby_size < int(Lobbies[lobby_number].lobby_threshold):
        Lobbies[lobby_number].active = 0
        print(f'lobby{lobby_number}: Lobby threshold not met ({current_lobby_size}<{Lobbies[lobby_number].lobby_threshold}), displaying lobby information')

        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
            embed = discord.Embed(title=f'{Lobbies[lobby_number].lobby_message_title}',
                                  description='Captains Mode, player draft will start when the lobby is full. '
                                              'Currently ' + str(current_lobby_size) + '/' + str(Lobbies[lobby_number].lobby_threshold) + ' players',
                                  color=int(Lobbies[lobby_number].lobby_message_color, 16))
            if Lobbies[lobby_number].description:
                embed.add_field(name="", value=Lobbies[lobby_number].description, inline=False)
            embed.add_field(name="Players", value=player_pool_string, inline=True)
            embed.add_field(name='\u200b', value='\u200b', inline=False)
            embed.timestamp = datetime.datetime.now()
            embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
            lobby_message = await Lobbies[lobby_number].lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
            await lobby_message.edit(embed=embed, view=CMButton(timeout=None))
            return

        embed = discord.Embed(title=f'{Lobbies[lobby_number].lobby_message_title}',
                              description='Join using buttons below, server info will be sent via DM when the lobby is full. '
                                          'Currently ' + str(current_lobby_size) + '/' + str(Lobbies[lobby_number].lobby_threshold) + ' players',
                              color=int(Lobbies[lobby_number].lobby_message_color, 16))
        if Lobbies[lobby_number].description:
            embed.add_field(name="", value=Lobbies[lobby_number].description, inline=False)
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.add_field(name=Lobbies[lobby_number].either_name, value=fill_players_string, inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await Lobbies[lobby_number].lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=LobbyButtons(lobby_number))
        return
    elif current_lobby_size >= int(Lobbies[lobby_number].lobby_threshold) and Lobbies[lobby_number].active and not Lobbies[lobby_number].launched:

        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft) and not Lobbies[lobby_number].player_draft_completed:
            if not Lobbies[lobby_number].drafting_players:
                embed = discord.Embed(title=f'Player draft is about to start', description="Waiting for host...", color=int(Lobbies[lobby_number].active_message_color, 16))
            else:
                if Lobbies[lobby_number].selecting_captains:
                    embed = discord.Embed(title=f'Player draft is ongoing', description="Host is selecting captains", color=int(Lobbies[lobby_number].active_message_color, 16))
                else:
                    embed = discord.Embed(title=f'Player draft is ongoing', description=f"Captains are {Lobbies[lobby_number].sapp_captain.display_name} and {Lobbies[lobby_number].ambr_captain.display_name}", color=int(Lobbies[lobby_number].active_message_color, 16))

        elif distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and not Lobbies[lobby_number].hero_draft_completed:
            if not Lobbies[lobby_number].drafting_heroes:
                embed = discord.Embed(title=f'Hero draft is about to start', description="Waiting for host...", color=int(Lobbies[lobby_number].active_message_color, 16))
            else:
                embed = discord.Embed(title=f'Hero draft is ongoing', description=f"Currently drafting: {Lobbies[lobby_number].drafter.display_name} \n You will receive a DM when it's your turn to draft", color=int(Lobbies[lobby_number].active_message_color, 16))
        elif distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and Lobbies[lobby_number].hero_draft_completed:
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                embed = discord.Embed(title=f'Hero draft is complete!', description='Lobby is launching...', color=int(Lobbies[lobby_number].active_message_color, 16))
            else:
                embed = discord.Embed(title=f'Hero draft is complete!', description='Waiting for host...', color=int(Lobbies[lobby_number].active_message_color, 16))
        elif not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                embed = discord.Embed(title=f'Lobby is full!', description='Lobby is launching...', color=int(Lobbies[lobby_number].active_message_color, 16))
            else:
                embed = discord.Embed(title=f'Lobby is full!', description='Waiting for host...', color=int(Lobbies[lobby_number].active_message_color, 16))

        if Lobbies[lobby_number].readying:
            not_ready = []
            for i in range(len(Lobbies[lobby_number].sapp_players)):
                if not Lobbies[lobby_number].sapp_players_ready[i]:
                    not_ready.append(str(Lobbies[lobby_number].sapp_players[i].display_name))
            for i in range(len(Lobbies[lobby_number].ambr_players)):
                if not Lobbies[lobby_number].ambr_players_ready[i]:
                    not_ready.append(str(Lobbies[lobby_number].ambr_players[i].display_name))
            not_ready_string = ", ".join(not_ready)
            if not not_ready_string:
                not_ready_string = "None"
            embed = discord.Embed(title=f"Ready up! Check your DMs", description=f'Not ready: {not_ready_string}')
        if Lobbies[lobby_number].description:
            embed.add_field(name="", value=Lobbies[lobby_number].description, inline=False)
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft) and not Lobbies[lobby_number].player_draft_completed:
            embed.add_field(name="Player Pool", value=player_pool_string, inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await Lobbies[lobby_number].lobby_channel.fetch_message(Lobbies[lobby_number].message_id)

        if Lobbies[lobby_number].active and not Lobbies[lobby_number].readying and not Lobbies[lobby_number].drafting_heroes and not Lobbies[lobby_number].hero_draft_completed and not Lobbies[lobby_number].drafting_players and not Lobbies[lobby_number].player_draft_completed and not Lobbies[lobby_number].launched:
            await lobby_message.edit(embed=embed, view=LeaveButton(timeout=None))
            return
        await lobby_message.edit(embed=embed, view=None)
        return

    elif current_lobby_size >= int(Lobbies[lobby_number].lobby_threshold) and Lobbies[lobby_number].active and Lobbies[lobby_number].launched:
        print(f'lobby{lobby_number}: Lobby activated and launched, displaying final player list')
        embed = discord.Embed(title=f'Lobby has started!', description='Check your DMs for connect info', color=int(Lobbies[lobby_number].active_message_color, 16))
        if Lobbies[lobby_number].description:
            embed.add_field(name="", value=Lobbies[lobby_number].description, inline=False)
        embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
        embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f'Lobby {lobby_number} • Hosted by {Lobbies[lobby_number].host.display_name} • Last updated')
        lobby_message = await Lobbies[lobby_number].lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.edit(embed=embed, view=None)
        return
    else:
        print(f'lobby{lobby_number}: Lobby threshold met! ({current_lobby_size}/{Lobbies[lobby_number].lobby_threshold})')
        await activate_lobby(lobby_number)


async def activate_lobby(lobby_number):
    if not Lobbies[lobby_number].active:
        Lobbies[lobby_number].active = 1
        await update_message(lobby_number)
        if not distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
            await assign_teams(lobby_number)
        await size_lobby(lobby_number)
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)

        if distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
            if not distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                print(f'lobby{lobby_number}: EnablePlayerDraft is {Lobbies[lobby_number].enable_player_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, waiting for host to start player draft')
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is waiting for you to start the player draft")
                return
            else:
                print(f'lobby{lobby_number}: EnablePlayerDraft is {Lobbies[lobby_number].enable_player_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, starting player draft')
                await draft_players(lobby_number)
                return
        elif distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
            if not distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                print(f'lobby{lobby_number}: EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, waiting for host to start hero draft')
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is waiting for you to start the hero draft")
                return
            else:
                print(f'lobby{lobby_number}: EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, starting player draft')
                await draft_heroes(lobby_number)
                return
        else:
            if not distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                print(f'lobby{lobby_number}: EnablePlayerDraft is {Lobbies[lobby_number].enable_player_draft}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, waiting for host to launch')
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} is waiting for you to start the game")
                return
            else:
                print(f'lobby{lobby_number}: EnablePlayerDraft is {Lobbies[lobby_number].enable_player_draft}, EnableHeroDraft is {Lobbies[lobby_number].enable_hero_draft}, LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, launching lobby')
                await launch_lobby(lobby_number)
                return
    else:
        print(f'lobby{lobby_number}: Lobby was already started, doing nothing...')
        return


async def launch_lobby(lobby_number):
    if not Lobbies[lobby_number].launched:
        if distutils.util.strtobool(Lobbies[lobby_number].enable_ready_up):
            await ready_up(lobby_number)
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


async def draft_players(lobby_number):
    if Lobbies[lobby_number].drafting_players or Lobbies[lobby_number].player_draft_completed:
        print(f'lobby{lobby_number}: Player draft was already started!')
        return
    else:
        Lobbies[lobby_number].drafting_players = 1
        print(f'lobby{lobby_number}: Beginning player draft...')
        random.shuffle(Lobbies[lobby_number].player_pool)
        await get_captains(lobby_number)
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)
        team_size = int(Lobbies[lobby_number].lobby_threshold) / 2
        if team_size >= 6:
            draft_range = team_size - 2
        else:
            draft_range = team_size
        first_pick = random.choice(["sapp", "ambr"])
        for i in range(int(draft_range)-1):
            if first_pick == "sapp":
                await start_captain_pick(lobby_number, "sapp")
                await start_captain_pick(lobby_number, "ambr")
            else:
                await start_captain_pick(lobby_number, "ambr")
                await start_captain_pick(lobby_number, "sapp")

        await assign_teams(lobby_number)
        Lobbies[lobby_number].player_pool.clear()
        Lobbies[lobby_number].drafting_players = 0
        Lobbies[lobby_number].player_draft_completed = 1
        print(f'lobby{lobby_number}: Player draft completed!')
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                await draft_heroes(lobby_number)
            else:
                await launch_lobby(lobby_number)
        else:
            if distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} player draft is complete and waiting for you to start hero draft")
            else:
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} player draft is complete and waiting for you to launch the lobby")


async def get_captains(lobby_number):
    Lobbies[lobby_number].selecting_captains = 1
    await update_message(lobby_number)
    embed = discord.Embed(title=f"Pick two players to be captains", color=int("0B6623", 16))
    draft_msg = await Lobbies[lobby_number].host.send(embed=embed, view=CaptainSelect(Lobbies[lobby_number].player_pool))
    Lobbies[lobby_number].draft_msg = draft_msg
    while Lobbies[lobby_number].selecting_captains:
        await asyncio.sleep(1)
    Lobbies[lobby_number].selected_player = Lobbies[lobby_number].sapp_captain
    Lobbies[lobby_number].sapp_players.append(Lobbies[lobby_number].sapp_captain)
    await remove_selected_player(lobby_number)
    Lobbies[lobby_number].selected_player = Lobbies[lobby_number].ambr_captain
    Lobbies[lobby_number].ambr_players.append(Lobbies[lobby_number].ambr_captain)
    await remove_selected_player(lobby_number)
    await update_message(lobby_number)


async def start_captain_pick(lobby_number, team):
    if team == "sapp":
        Lobbies[lobby_number].waiting_for_pick = 1
        await get_captain_pick(lobby_number, team)
        while Lobbies[lobby_number].waiting_for_pick:
            await asyncio.sleep(1)
        Lobbies[lobby_number].sapp_players.append(Lobbies[lobby_number].selected_player)
        await remove_selected_player(lobby_number)
        await update_message(lobby_number)
        return
    else:
        Lobbies[lobby_number].waiting_for_pick = 1
        await get_captain_pick(lobby_number, team)
        while Lobbies[lobby_number].waiting_for_pick:
            await asyncio.sleep(1)
        Lobbies[lobby_number].ambr_players.append(Lobbies[lobby_number].selected_player)
        await remove_selected_player(lobby_number)
        await update_message(lobby_number)


async def get_captain_pick(lobby_number, team):
    sapp_players = []
    ambr_players = []
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name))
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name))
    sapp_players_string = "\n".join(sapp_players)
    ambr_players_string = "\n".join(ambr_players)
    if not sapp_players_string:
        sapp_players_string = "None"
        if not ambr_players_string:
            ambr_players_string = "None"
    if team == "sapp":
        embed = discord.Embed(title=f"It's your turn to pick a player! You are captain of {Lobbies[lobby_number].sapphire_name}", color=int("0F52BA", 16))
        drafter = Lobbies[lobby_number].sapp_captain
    else:
        embed = discord.Embed(title=f"It's your turn to pick a player! You are captain of {Lobbies[lobby_number].amber_name}", color=int("FFBF00", 16))
        drafter = Lobbies[lobby_number].ambr_captain
    embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
    embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)

    draft_msg = await drafter.send(embed=embed, view=PlayerSelect(Lobbies[lobby_number].player_pool))
    Lobbies[lobby_number].draft_msg = draft_msg


async def remove_selected_player(lobby_number):
    for i in range(len(Lobbies[lobby_number].player_pool)):
        if Lobbies[lobby_number].player_pool[i] == Lobbies[lobby_number].selected_player:
            Lobbies[lobby_number].player_pool.pop(i)
            return


async def draft_heroes(lobby_number):
    if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed:
        print(f'lobby{lobby_number}: Hero draft was already started!')
        return
    else:
        Lobbies[lobby_number].drafting_heroes = 1
        print(f'lobby{lobby_number}: Beginning hero draft...')
        random.shuffle(Lobbies[lobby_number].sapp_players)
        random.shuffle(Lobbies[lobby_number].ambr_players)
        Lobbies[lobby_number].sapp_heroes.clear()
        Lobbies[lobby_number].ambr_heroes.clear()
        Lobbies[lobby_number].picked_heroes.clear()
        for i in range(len(Lobbies[lobby_number].sapp_players)):
            Lobbies[lobby_number].sapp_heroes.append("not drafted")
            Lobbies[lobby_number].ambr_heroes.append("not drafted")
        await update_message(lobby_number)
        await update_admin_panel(lobby_number)
        team_size = int(Lobbies[lobby_number].lobby_threshold)/2
        first_pick = random.choice(["sapp", "ambr"])
        for i in range(int(team_size)):
            if first_pick == "sapp":
                await start_player_pick(lobby_number, "sapp", i)
                await start_player_pick(lobby_number, "ambr", i)
            else:
                await start_player_pick(lobby_number, "ambr", i)
                await start_player_pick(lobby_number, "sapp", i)
        Lobbies[lobby_number].drafting_heroes = 0
        Lobbies[lobby_number].hero_draft_completed = 1
        if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
            await launch_lobby(lobby_number)
        else:
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            await Lobbies[lobby_number].host.dm_channel.send(f"Lobby {lobby_number} hero draft is complete and waiting for you to launch the lobby")


async def start_player_pick(lobby_number, team, index):
    if team == "sapp":
        Lobbies[lobby_number].waiting_for_pick = 1
        Lobbies[lobby_number].drafter = Lobbies[lobby_number].sapp_players[index]
        await update_message(lobby_number)
        await get_player_pick(lobby_number, Lobbies[lobby_number].sapp_players[index], team)
        while Lobbies[lobby_number].waiting_for_pick:
            await asyncio.sleep(1)
        Lobbies[lobby_number].sapp_heroes[index] = Lobbies[lobby_number].selected_hero
        Lobbies[lobby_number].picked_heroes.append(Lobbies[lobby_number].selected_hero)
        await remove_selected_hero(lobby_number)
        await update_message(lobby_number)
        return
    else:
        Lobbies[lobby_number].waiting_for_pick = 1
        Lobbies[lobby_number].drafter = Lobbies[lobby_number].ambr_players[index]
        await update_message(lobby_number)
        await get_player_pick(lobby_number, Lobbies[lobby_number].ambr_players[index], team)
        while Lobbies[lobby_number].waiting_for_pick:
            await asyncio.sleep(1)
        Lobbies[lobby_number].ambr_heroes[index] = Lobbies[lobby_number].selected_hero
        Lobbies[lobby_number].picked_heroes.append(Lobbies[lobby_number].selected_hero)
        await remove_selected_hero(lobby_number)
        await update_message(lobby_number)


async def get_player_pick(lobby_number, player, team):
    sapp_players = []
    ambr_players = []
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        sapp_players.append(str(Lobbies[lobby_number].sapp_players[i].display_name) + " - " + Lobbies[lobby_number].sapp_heroes[i])
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        ambr_players.append(str(Lobbies[lobby_number].ambr_players[i].display_name) + " - " + Lobbies[lobby_number].ambr_heroes[i])
    sapp_players_string = "\n".join(sapp_players)
    ambr_players_string = "\n".join(ambr_players)
    if team == "sapp":
        embed = discord.Embed(title=f"It's your turn to pick a hero! You are on {Lobbies[lobby_number].sapphire_name}", color=int("0F52BA", 16))
    else:
        embed = discord.Embed(title=f"It's your turn to pick a hero! You are on {Lobbies[lobby_number].amber_name}",
                              color=int("FFBF00", 16))
    embed.add_field(name=Lobbies[lobby_number].sapphire_name, value=sapp_players_string, inline=True)
    embed.add_field(name=Lobbies[lobby_number].amber_name, value=ambr_players_string, inline=True)

    draft_msg = await player.send(embed=embed, view=HeroSelect(Lobbies[lobby_number].available_heroes))
    Lobbies[lobby_number].draft_msg = draft_msg


async def remove_selected_hero(lobby_number):
    for i in range(len(Lobbies[lobby_number].available_heroes)):
        if Lobbies[lobby_number].available_heroes[i] == Lobbies[lobby_number].selected_hero:
            Lobbies[lobby_number].available_heroes.pop(i)
            return


async def get_lobby_number(interaction):
    global Lobbies
    for i in range (len(Lobbies)):
        if interaction.message.id == Lobbies[i].message_id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received lobby button press from {interaction.user.display_name}')
    for i in range(len(Lobbies)):
        if interaction.message.id == Lobbies[i].admin_msg_id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received admin button press from {interaction.user.display_name}')
    for i in range(len(Lobbies)):
        if interaction.message.id == Lobbies[i].draft_msg.id:
            lobby_number = Lobbies[i].number
            print(f'lobby{lobby_number}: Received draft button press from {interaction.user.display_name}')
    return lobby_number


async def assign_teams(lobby_number):
    if not distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
        print(f'lobby{lobby_number}: Assigning fill players to teams')
        random.shuffle(Lobbies[lobby_number].fill_players)
        for player in Lobbies[lobby_number].fill_players:
            if len(Lobbies[lobby_number].sapp_players) < int(Lobbies[lobby_number].lobby_threshold)/2:
                Lobbies[lobby_number].sapp_players.append(player)
            else:
                Lobbies[lobby_number].ambr_players.append(player)
        Lobbies[lobby_number].fill_players.clear()
    else:
        print(f'lobby{lobby_number}: Assigning any remaining players to teams')
        random.shuffle(Lobbies[lobby_number].player_pool)
        for player in Lobbies[lobby_number].player_pool:
            if len(Lobbies[lobby_number].sapp_players) < int(Lobbies[lobby_number].lobby_threshold) / 2:
                Lobbies[lobby_number].sapp_players.append(player)
            else:
                Lobbies[lobby_number].ambr_players.append(player)


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


async def ready_up(lobby_number):
    print(f'lobby{lobby_number}: Beginning ready up...')
    Lobbies[lobby_number].readying = 1
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        Lobbies[lobby_number].sapp_players_ready.append(0)
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        Lobbies[lobby_number].sapp_ready_msgs.append(discord.Message)
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        Lobbies[lobby_number].ambr_players_ready.append(0)
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        Lobbies[lobby_number].ambr_ready_msgs.append(discord.Message)
    await update_message(lobby_number)
    await update_admin_panel(lobby_number)
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        await get_ready_status(Lobbies[lobby_number].sapp_players[i], lobby_number, "sapp", i)
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        await get_ready_status(Lobbies[lobby_number].ambr_players[i], lobby_number, "ambr", i)
    while not Lobbies[lobby_number].all_players_ready:
        await update_message(lobby_number)
        await check_ready_status(lobby_number)
        await asyncio.sleep(5)
    print(f'lobby{lobby_number}: All players are ready! Launching...')


async def get_ready_status(player, lobby_number, team, index):
    embed = discord.Embed(title=f"Ready up!", color=int("0B6623", 16))
    ready_msg = await player.send(embed=embed, view=ReadyUpButton(lobby_number, team, index))
    if team == "sapp":
        Lobbies[lobby_number].sapp_ready_msgs[index] = ready_msg
    else:
        Lobbies[lobby_number].ambr_ready_msgs[index] = ready_msg


async def check_ready_status(lobby_number):
    for ready in Lobbies[lobby_number].sapp_players_ready:
        if not ready:
            return
    for ready in Lobbies[lobby_number].ambr_players_ready:
        if not ready:
            return
    Lobbies[lobby_number].readying = 0
    Lobbies[lobby_number].all_players_ready = 1


async def send_lobby_info(lobby_number):
    print(f'lobby{lobby_number}: Sending DMs with team and connect info...')
    connect_string = "".join(["`connect ", str(Lobbies[lobby_number].server), "; password ", str(Lobbies[lobby_number].password) ,"`"])
    for player in Lobbies[lobby_number].sapp_players:
        with open("config/banner_sapp.png", "rb") as bansa:
            embed = discord.Embed(title=f"You are on team {Lobbies[lobby_number].sapphire_name}", color=int("0F52BA", 16))
            embed.add_field(name='Connect info', value=connect_string, inline=False)
            if distutils.util.strtobool(Lobbies[lobby_number].enable_image_send):
                file = discord.File(bansa, filename="config/banner_sapp.png")
            else:
                file = None
        await player.send(embed=embed, file=file)
    for player in Lobbies[lobby_number].ambr_players:
        with open("config/banner_ambr.png", "rb") as banam:
            embed = discord.Embed(title=f"You are on team {Lobbies[lobby_number].amber_name}",color=int("FFBF00", 16))
            embed.add_field(name='Connect info', value=connect_string, inline=False)
            if distutils.util.strtobool(Lobbies[lobby_number].enable_image_send):
                file = discord.File(banam, filename="config/banner_sapp.png")
            else:
                file = None
        await player.send(embed=embed, file=file)



async def update_all_lobby_messages():
    for i in range(1, len(Lobbies)):
        if not await is_message_deleted(Lobbies[i].lobby_channel, Lobbies[i].message_id):
            await update_message(i)


async def size_lobby(lobby_number):
    if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].drafting_players or Lobbies[lobby_number].hero_draft_completed:
        return
    if not distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft):
        current_lobby_size = len(Lobbies[lobby_number].sapp_players) + len(Lobbies[lobby_number].ambr_players) + len(Lobbies[lobby_number].fill_players)
        if current_lobby_size <= int(Lobbies[lobby_number].lobby_threshold):
            return
        team_size = int(Lobbies[lobby_number].lobby_threshold)/2
        pop_index = int(team_size) - 1
        while len(Lobbies[lobby_number].sapp_players) > team_size:
            print(f'lobby{lobby_number}: {Lobbies[lobby_number].sapphire_name} too big, player {Lobbies[lobby_number].sapp_players[pop_index].display_name} kicked')
            await Lobbies[lobby_number].sapp_players[pop_index].send("Sorry, the lobby was too big and I had to remove you :(")
            Lobbies[lobby_number].sapp_players.pop(pop_index)
        while len(Lobbies[lobby_number].ambr_players) > team_size:
            print(f'lobby{lobby_number}: {Lobbies[lobby_number].amber_name} too big, player {Lobbies[lobby_number].ambr_players[pop_index].display_name} kicked')
            await Lobbies[lobby_number].ambr_players[pop_index].send("Sorry, the lobby was too big and I had to remove you :(")
            Lobbies[lobby_number].ambr_players.pop(pop_index)
    else:
        current_lobby_size = len(Lobbies[lobby_number].player_pool)
        if current_lobby_size <= int(Lobbies[lobby_number].lobby_threshold):
            return
        pop_index = int(Lobbies[lobby_number].lobby_threshold) - 1
        while len(Lobbies[lobby_number].player_pool) > int(Lobbies[lobby_number].lobby_threshold):
            print(f'lobby{lobby_number}: Player pool too big, player {Lobbies[lobby_number].player_pool[pop_index].display_name} kicked')
            await Lobbies[lobby_number].player_pool[pop_index].send("Sorry, the lobby was too big and I had to remove you :(")
            Lobbies[lobby_number].player_pool.pop(pop_index)


async def reset_lobby(lobby_number):
    Lobbies[lobby_number].active = 0
    Lobbies[lobby_number].drafting_heroes = 0
    Lobbies[lobby_number].drafting_players = 0
    Lobbies[lobby_number].waiting_for_pick = 0
    Lobbies[lobby_number].selecting_captains = 0
    Lobbies[lobby_number].hero_draft_completed = 0
    Lobbies[lobby_number].player_draft_completed = 0
    Lobbies[lobby_number].readying = 0
    Lobbies[lobby_number].all_players_ready = 0
    Lobbies[lobby_number].launched = 0
    Lobbies[lobby_number].drafter = discord.User
    Lobbies[lobby_number].sapp_captain = discord.User
    Lobbies[lobby_number].ambr_captain = discord.User
    Lobbies[lobby_number].selected_player = discord.User
    Lobbies[lobby_number].draft_msg = discord.Message
    Lobbies[lobby_number].sapp_players.clear()
    Lobbies[lobby_number].ambr_players.clear()
    Lobbies[lobby_number].fill_players.clear()
    Lobbies[lobby_number].sapp_heroes.clear()
    Lobbies[lobby_number].ambr_heroes.clear()
    Lobbies[lobby_number].player_pool.clear()
    Lobbies[lobby_number].picked_heroes.clear()
    Lobbies[lobby_number].sapp_players_ready.clear()
    Lobbies[lobby_number].ambr_players_ready.clear()
    Lobbies[lobby_number].sapp_ready_msgs.clear()
    Lobbies[lobby_number].ambr_ready_msgs.clear()
    Lobbies[lobby_number].available_heroes = Heroes[:]
    await update_message(lobby_number)
    await update_admin_panel(lobby_number)
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f"#{Lobbies[lobby_number].lobby_channel.name}"))


async def close_lobby(lobby_number):
    if not await is_message_deleted(Lobbies[lobby_number].lobby_channel, Lobbies[lobby_number].message_id):
        lobby_message = await Lobbies[lobby_number].lobby_channel.fetch_message(Lobbies[lobby_number].message_id)
        await lobby_message.delete()
    if not await is_message_deleted(Lobbies[lobby_number].host.dm_channel, Lobbies[lobby_number].admin_msg_id):
        admin_message = await Lobbies[lobby_number].host.dm_channel.fetch_message(Lobbies[lobby_number].admin_msg_id)
        await admin_message.delete()


async def kick_player(lobby_number, user_id):
    if Lobbies[lobby_number].launched:
        return 0
    player = bot_guild.get_member(int(f"{user_id}"))
    for i in range(len(Lobbies[lobby_number].sapp_players)):
        if Lobbies[lobby_number].sapp_players[i].id == player.id:
            Lobbies[lobby_number].sapp_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
    for i in range(len(Lobbies[lobby_number].ambr_players)):
        if Lobbies[lobby_number].ambr_players[i].id == player.id:
            Lobbies[lobby_number].ambr_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
    for i in range(len(Lobbies[lobby_number].fill_players)):
        if Lobbies[lobby_number].fill_players[i].id == player.id:
            Lobbies[lobby_number].fill_players.pop(i)
            await update_message(lobby_number)
            print(f'lobby{lobby_number}: Player {player.display_name} kicked')
            return 1
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
    for i in range(1, len(Lobbies)):
        await kick_player(i, player.id)
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
    except AttributeError:
        return True
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
        await interaction.response.send_message(f"Sending DM to Lobby {lobby_number} players: \n {text}", ephemeral=True)
        for player in Lobbies[lobby_number].sapp_players:
            await player.send(f"{text}")
        for player in Lobbies[lobby_number].ambr_players:
            await player.send(f"{text}")
        for player in Lobbies[lobby_number].fill_players:
            await player.send(f"{text}")
        for player in Lobbies[lobby_number].player_pool:
            await player.send(f"{text}")


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
            if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed or Lobbies[lobby_number].launched:
                await interaction.response.send_message(f"It's too late to change LobbyThreshold right now", ephemeral=True)
                return
            elif int(value) % 2 or int(value) == 0:
                await interaction.response.send_message(f'LobbyThreshold must be even and non-zero', ephemeral=True)
                return
            else:
                Lobbies[lobby_number].lobby_threshold = value
                await interaction.response.send_message(f"Lobby {lobby_number} LobbyThreshold changed to {Lobbies[lobby_number].lobby_threshold}", ephemeral=True)
                await size_lobby(lobby_number)
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
        elif Lobbies[lobby_number].selected_setting == "EnableImageSend":
            Lobbies[lobby_number].enable_image_send = value
            await interaction.response.send_message(f"Lobby {lobby_number} EnableImageSend changed to {Lobbies[lobby_number].enable_image_send}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "EnablePlayerDraft":
            if Lobbies[lobby_number].launched or Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed:
                await interaction.response.send_message(f"It's too late to change EnablePlayerDraft right now", ephemeral=True)
                return
            else:
                existing_value = Lobbies[lobby_number].enable_player_draft
                if distutils.util.strtobool(value) == distutils.util.strtobool(existing_value):
                    await interaction.response.send_message(f"EnablePlayerDraft is already {value}", ephemeral=True)
                    return
                if distutils.util.strtobool(value):
                    Lobbies[lobby_number].enable_player_draft = value
                    for player in Lobbies[lobby_number].sapp_players:
                        Lobbies[lobby_number].player_pool.append(player)
                    for player in Lobbies[lobby_number].ambr_players:
                        Lobbies[lobby_number].player_pool.append(player)
                    for player in Lobbies[lobby_number].fill_players:
                        Lobbies[lobby_number].player_pool.append(player)
                    Lobbies[lobby_number].sapp_players.clear()
                    Lobbies[lobby_number].ambr_players.clear()
                    Lobbies[lobby_number].fill_players.clear()
                else:
                    Lobbies[lobby_number].enable_player_draft = value
                    for player in Lobbies[lobby_number].player_pool:
                        Lobbies[lobby_number].fill_players.append(player)
                    Lobbies[lobby_number].player_pool.clear()

                await interaction.response.send_message(f"Lobby {lobby_number} EnablePlayerDraft changed to {Lobbies[lobby_number].enable_player_draft}", ephemeral=True)
                await update_message(lobby_number)
                await update_admin_panel(lobby_number)
                return
        elif Lobbies[lobby_number].selected_setting == "EnableReadyUp":
            Lobbies[lobby_number].enable_ready_up = value
            await interaction.response.send_message(f"Lobby {lobby_number} EnableReadyUp changed to {Lobbies[lobby_number].enable_ready_up}", ephemeral=True)
            await update_admin_panel(lobby_number)
            return
        elif Lobbies[lobby_number].selected_setting == "LobbyDescription":
            Lobbies[lobby_number].description = value
            await interaction.response.send_message(f"Lobby {lobby_number} description changed to '{Lobbies[lobby_number].description}'", ephemeral=True)
            await update_message(lobby_number)
            return
        else:
            await interaction.response.send_message(f"Setting not found!", ephemeral=True)


class LobbyButtons(discord.ui.View):
    def __init__(self, lobby_number):
        self.lobby_number = lobby_number
        super().__init__(timeout=None)
        self.sapp_button = discord.ui.button()
        self.ambr_button = discord.ui.button()
        self.fill_button = discord.ui.button()
        self.add_sapp_button()
        self.add_ambr_button()
        self.add_fill_button()

    def add_sapp_button(self):
        self.sapp_button = discord.ui.Button(label=f"{Lobbies[self.lobby_number].sapphire_name}", style=discord.ButtonStyle.blurple)

        async def sapp_button_callback(interaction: discord.Interaction):
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

            interactor_already_here = False
            for i in range(len(Lobbies[lobby_number].sapp_players)):
                if interactor.id == Lobbies[lobby_number].sapp_players[i].id:
                    interactor_already_here = True
                    Lobbies[lobby_number].sapp_players.pop(i)
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

        self.sapp_button.callback = sapp_button_callback
        self.add_item(self.sapp_button)

    def add_ambr_button(self):
        self.ambr_button = discord.ui.Button(label=f"{Lobbies[self.lobby_number].amber_name}", style=discord.ButtonStyle.red)

        async def ambr_button_callback(interaction: discord.Interaction):
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

            interactor_already_here = False
            for i in range(len(Lobbies[lobby_number].ambr_players)):
                if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                    interactor_already_here = True
                    Lobbies[lobby_number].ambr_players.pop(i)
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

        self.ambr_button.callback = ambr_button_callback
        self.add_item(self.ambr_button)

    def add_fill_button(self):
        self.fill_button = discord.ui.Button(label=f"{Lobbies[self.lobby_number].either_name}", style=discord.ButtonStyle.green)

        async def fill_button_callback(interaction: discord.Interaction):
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
                for i in range(len(Lobbies[lobby_number].fill_players)):
                    if interactor.id == Lobbies[lobby_number].fill_players[i].id:
                        del Lobbies[lobby_number].fill_players[i]
                await interaction.response.send_message(f"Removed from fill", ephemeral=True)
                await update_message(lobby_number)
        self.fill_button.callback = fill_button_callback
        self.add_item(self.fill_button)


class CaptainSelect(discord.ui.View):
    def __init__(self, player_pool):
        super().__init__(timeout=None)
        self.player_pool = player_pool
        self.player_options = []
        self.parse_options()

        select = discord.ui.Select(placeholder="Select Captains", row=0, min_values=2, max_values=2, options=self.player_options)
        select.callback = self.captain_select_callback
        self.add_item(select)

    def parse_options(self):
        self.player_options = [discord.SelectOption(label=f"{player.global_name}", value=f"{player.id}") for player in self.player_pool]

    async def captain_select_callback(self, interaction: discord.Interaction):
        lobby_number = await get_lobby_number(interaction)
        sapp_captain_id = interaction.data["values"][0]
        ambr_captain_id = interaction.data["values"][1]
        Lobbies[lobby_number].sapp_captain = bot_guild.get_member(int(f"{sapp_captain_id}"))
        Lobbies[lobby_number].ambr_captain = bot_guild.get_member(int(f"{ambr_captain_id}"))
        print(f"lobby{lobby_number}: Captains {Lobbies[lobby_number].sapp_captain.display_name} and {Lobbies[lobby_number].ambr_captain.display_name} have been picked")
        embed = discord.Embed(title=f"You have selected {Lobbies[lobby_number].sapp_captain.display_name} and {Lobbies[lobby_number].ambr_captain.display_name} to be captains", color=int("808080", 16))
        await Lobbies[lobby_number].draft_msg.edit(embed=embed, view=None)
        await interaction.response.defer()
        Lobbies[lobby_number].selecting_captains = 0


class PlayerSelect(discord.ui.View):
    def __init__(self, player_pool):
        super().__init__(timeout=None)
        self.player_pool = player_pool
        self.player_options = []
        self.parse_options()

        select = discord.ui.Select(placeholder="Select a player", row=0, min_values=1, max_values=1, options=self.player_options)
        select.callback = self.player_select_callback
        self.add_item(select)

    def parse_options(self):
        self.player_options = [discord.SelectOption(label=f"{player.global_name}", value=f"{player.id}") for player in self.player_pool]

    async def player_select_callback(self, interaction: discord.Interaction):
        lobby_number = await get_lobby_number(interaction)
        selected_player_id = interaction.data["values"][0]
        Lobbies[lobby_number].selected_player = bot_guild.get_member(int(f"{selected_player_id}"))
        await remove_selected_player(lobby_number)

        print(f"lobby{lobby_number}: Player {Lobbies[lobby_number].selected_player.display_name} has been picked")
        embed = discord.Embed(title=f"You have drafted {Lobbies[lobby_number].selected_player.display_name}", color=int("808080", 16))
        await Lobbies[lobby_number].draft_msg.edit(embed=embed, view=None)
        await interaction.response.defer()
        Lobbies[lobby_number].waiting_for_pick = 0


class HeroSelect(discord.ui.View):
    def __init__(self, avail_heroes):
        super().__init__(timeout=None)
        self.avail_heroes = avail_heroes
        self.hero_options = []
        self.parse_options()

        select = discord.ui.Select(placeholder="Select a hero", row=0, min_values=1, max_values=1, options=self.hero_options)
        select.callback = self.hero_select_callback
        self.add_item(select)

    def parse_options(self):
        self.hero_options = [discord.SelectOption(label=hero) for hero in self.avail_heroes]

    async def hero_select_callback(self, interaction: discord.Interaction):
        lobby_number = await get_lobby_number(interaction)
        if interaction.user.id == Lobbies[lobby_number].drafter.id:
            picked_hero = interaction.data["values"][0]
            if picked_hero not in Lobbies[lobby_number].picked_heroes:
                Lobbies[lobby_number].selected_hero = picked_hero
                print(f"lobby{lobby_number}: Hero {Lobbies[lobby_number].selected_hero} has been picked")
                embed = discord.Embed(title=f"You have selected {Lobbies[lobby_number].selected_hero}", color=int("808080", 16))
                await Lobbies[lobby_number].draft_msg.edit(embed=embed, view=None)
                await interaction.response.defer()
                Lobbies[lobby_number].waiting_for_pick = 0
            else:
                await interaction.response.send_message(f"{picked_hero} was already drafted, please pick a different hero", ephemeral=True)
        else:
            await interaction.response.send_message(f"It is not your turn to draft", ephemeral=True)


class CMButton(discord.ui.View):
    @discord.ui.button(label="Join/Leave", style=discord.ButtonStyle.primary, row=0)
    async def cm_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        print(f'lobby{lobby_number}: Received cm join/leave command from {interaction.user.display_name}')
        if interactor in Lobbies[lobby_number].player_pool:
            for i in range(len(Lobbies[lobby_number].player_pool)):
                if interactor.id == Lobbies[lobby_number].player_pool[i].id:
                    Lobbies[lobby_number].player_pool.pop(i)
            await interaction.response.send_message(f"Removed from lobby", ephemeral=True)
            await update_message(lobby_number)
            return
        else:
            Lobbies[lobby_number].player_pool.append(interactor)
            await interaction.response.send_message(f"Added to lobby", ephemeral=True)
            await update_message(lobby_number)


class LeaveButton(discord.ui.View):
    @discord.ui.button(label="Leave Lobby", style=discord.ButtonStyle.secondary, row=0)
    async def leave_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        interactor = interaction.user
        print(f'lobby{lobby_number}: Received leave command from {interaction.user.display_name}')
        if interactor in Lobbies[lobby_number].sapp_players:
            for i in range(len(Lobbies[lobby_number].sapp_players)):
                if interactor.id == Lobbies[lobby_number].sapp_players[i].id:
                    Lobbies[lobby_number].sapp_players.pop(i)
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].sapphire_name}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif interactor in Lobbies[lobby_number].ambr_players:
            for i in range(len(Lobbies[lobby_number].ambr_players)):
                if interactor.id == Lobbies[lobby_number].ambr_players[i].id:
                    Lobbies[lobby_number].ambr_players.pop(i)
            await interaction.response.send_message(f"Removed from {Lobbies[lobby_number].amber_name}", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        elif interactor in Lobbies[lobby_number].player_pool:
            for i in range(len(Lobbies[lobby_number].player_pool)):
                if interactor.id == Lobbies[lobby_number].player_pool[i].id:
                    Lobbies[lobby_number].player_pool.pop(i)
            await interaction.response.send_message(f"Removed from player pool", ephemeral=True)
            await update_message(lobby_number)
            await update_admin_panel(lobby_number)
            return
        else:
            await interaction.response.send_message(f"You're not in this lobby", ephemeral=True)


class ReadyUpButton(discord.ui.View):
    def __init__(self, lobby_number, team, index):
        self.lobby_number = lobby_number
        self.team = team
        self.index = index
        super().__init__(timeout=None)
        self.ready_button = discord.ui.button()
        self.add_ready_button()

    def add_ready_button(self):
        self.ready_button = discord.ui.Button(label="Ready", style=discord.ButtonStyle.green, row=0)

        async def ready_button_callback(interaction: discord.Interaction):
            if self.team == "sapp":
                Lobbies[self.lobby_number].sapp_players_ready[self.index] = 1
                embed = discord.Embed(title=f"You are ready! Waiting for other players...", color=int("0B6623", 16))
                await Lobbies[self.lobby_number].sapp_ready_msgs[self.index].edit(embed=embed, view=None)
            else:
                Lobbies[self.lobby_number].ambr_players_ready[self.index] = 1
                embed = discord.Embed(title=f"You are ready! Waiting for other players...", color=int("0B6623", 16))
                await Lobbies[self.lobby_number].ambr_ready_msgs[self.index].edit(embed=embed, view=None)
            await interaction.response.defer()

        self.ready_button.callback = ready_button_callback
        self.add_item(self.ready_button)


class AdminButtons(discord.ui.View):
    def __init__(self, lobby_number):
        self.lobby_number = lobby_number
        super().__init__(timeout=None)
        self.launch_button = discord.ui.button()
        self.reset_button = discord.ui.button()
        self.close_button = discord.ui.button()
        self.add_launch_button()
        self.add_reset_button()
        self.add_close_button()

    def add_launch_button(self):
        if distutils.util.strtobool(Lobbies[self.lobby_number].lobby_auto_launch):
            return
        elif Lobbies[self.lobby_number].launched:
            self.launch_button = discord.ui.Button(label="Already launched", style=discord.ButtonStyle.secondary, row=0)
        elif not Lobbies[self.lobby_number].active:
            self.launch_button = discord.ui.Button(label="Waiting to fill", style=discord.ButtonStyle.secondary, row=0)
        elif Lobbies[self.lobby_number].active and distutils.util.strtobool(Lobbies[self.lobby_number].enable_player_draft) and not Lobbies[self.lobby_number].player_draft_completed:
            self.launch_button = discord.ui.Button(label="Begin Player Draft", style=discord.ButtonStyle.green, row=0)
        elif distutils.util.strtobool(Lobbies[self.lobby_number].enable_hero_draft) and not Lobbies[self.lobby_number].drafting_heroes and not Lobbies[self.lobby_number].hero_draft_completed:
            self.launch_button = discord.ui.Button(label="Begin Hero Draft", style=discord.ButtonStyle.green, row=0)
        elif distutils.util.strtobool(Lobbies[self.lobby_number].enable_hero_draft) and Lobbies[self.lobby_number].drafting_heroes or distutils.util.strtobool(Lobbies[self.lobby_number].enable_player_draft) and Lobbies[self.lobby_number].drafting_players:
            self.launch_button = discord.ui.Button(label="Waiting for draft", style=discord.ButtonStyle.secondary, row=0)
        elif (distutils.util.strtobool(Lobbies[self.lobby_number].enable_hero_draft) and Lobbies[self.lobby_number].hero_draft_completed or
              not distutils.util.strtobool(Lobbies[self.lobby_number].enable_hero_draft)):
            self.launch_button = discord.ui.Button(label="Launch Lobby", style=discord.ButtonStyle.green, row=0)

        async def launch_button_callback(interaction: discord.Interaction):
            lobby_number = await get_lobby_number(interaction)
            print(f'lobby{lobby_number}: Received proceed command from {interaction.user.display_name}')
            if distutils.util.strtobool(Lobbies[lobby_number].lobby_auto_launch):
                await interaction.response.send_message(f"LobbyAutoLaunch is {Lobbies[lobby_number].lobby_auto_launch}, this button does nothing", ephemeral=True)
                return
            if not Lobbies[lobby_number].active:
                await interaction.response.send_message(f"Can't launch yet, lobby is not full", ephemeral=True)
                return
            if Lobbies[lobby_number].active and distutils.util.strtobool(Lobbies[lobby_number].enable_player_draft) and not Lobbies[lobby_number].player_draft_completed:
                await interaction.response.send_message(f"Starting player draft for Lobby {lobby_number}", ephemeral=True)
                await draft_players(lobby_number)
                return
            if Lobbies[lobby_number].active and distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and not Lobbies[lobby_number].hero_draft_completed:
                await interaction.response.send_message(f"Starting hero draft for Lobby {lobby_number}", ephemeral=True)
                await draft_heroes(lobby_number)
                return
            if Lobbies[lobby_number].active and distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft) and Lobbies[lobby_number].hero_draft_completed:
                await interaction.response.send_message(f"Launching Lobby {lobby_number}", ephemeral=True)
                await launch_lobby(lobby_number)
                return
            if Lobbies[lobby_number].active and not distutils.util.strtobool(Lobbies[lobby_number].enable_hero_draft):
                await interaction.response.send_message(f"Launching Lobby {lobby_number}", ephemeral=True)
                await launch_lobby(lobby_number)
                return

        self.launch_button.callback = launch_button_callback
        self.add_item(self.launch_button)

    def add_reset_button(self):
        self.reset_button = discord.ui.Button(label="Reset Lobby", style=discord.ButtonStyle.blurple, row=0)

        async def reset_button_callback(interaction: discord.Interaction):
            lobby_number = await get_lobby_number(interaction)
            print(f'lobby{lobby_number}: Received lobby reset command from {interaction.user.display_name}')
            Lobbies[lobby_number].manual_mode = 1
            await reset_lobby(lobby_number)
            await interaction.response.send_message(f"Lobby {lobby_number} reset", ephemeral=True)

        self.reset_button.callback = reset_button_callback
        self.add_item(self.reset_button)

    def add_close_button(self):
        self.close_button = discord.ui.Button(label="Close Lobby", style=discord.ButtonStyle.red, row=0)

        async def close_button_callback(interaction: discord.Interaction):
            lobby_number = await get_lobby_number(interaction)
            print(f'lobby{lobby_number}: Received lobby close command from {interaction.user.display_name}')
            await close_lobby(lobby_number)
            await interaction.response.send_message(f"Lobby {lobby_number} closed", ephemeral=True)

        self.close_button.callback = close_button_callback
        self.add_item(self.close_button)

    @discord.ui.button(label="Shuffle Teams", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received shuffle command from {interaction.user.display_name}')
        if Lobbies[lobby_number].drafting_heroes or Lobbies[lobby_number].hero_draft_completed or Lobbies[lobby_number].launched:
            await interaction.response.send_message(f"It's too late to shuffle teams", ephemeral=True)
        else:
            await shuffle_teams(lobby_number)
            await interaction.response.send_message(f"Teams have been shuffled", ephemeral=True)

    @discord.ui.button(label="Resend connect info", style=discord.ButtonStyle.secondary, row=1)
    async def resend_button_callback(self, button, interaction):
        lobby_number = await get_lobby_number(interaction)
        print(f'lobby{lobby_number}: Received resend info command from {interaction.user.display_name}')
        if Lobbies[lobby_number].launched:
            await send_lobby_info(lobby_number)
            await interaction.response.send_message(f"Connect info resent", ephemeral=True)
        else:
            await interaction.response.send_message(f"Lobby is not launched, sent nothing", ephemeral=True)

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
                           discord.SelectOption(label="Server",
                                                description="Change server address and port"),
                           discord.SelectOption(label="Password",
                                                description="Change server password"),
                           discord.SelectOption(label="LobbyAutoLaunch",
                                                description="Change auto-launch behavior"),
                           discord.SelectOption(label="LobbyAutoReset",
                                                description="Change auto-reset behavior"),
                           discord.SelectOption(label="LobbyMessageTitle",
                                                description="Change the title of the lobby message"),
                           discord.SelectOption(label="LobbyDescription",
                                                description="Change the lobby message description"),
                           discord.SelectOption(label="EnableImageSend",
                                                description="When true will send an image to players with lobby connect info"),
                           discord.SelectOption(label="SapphireTeamName",
                                                description="Change the Sapphire team name"),
                           discord.SelectOption(label="AmberTeamName",
                                                description="Change the Amber team name"),
                           discord.SelectOption(label="EitherTeamName",
                                                description="Change name for fill players"),
                           discord.SelectOption(label="LobbyThreshold",
                                                description="Change the lobby player threshold"),
                           discord.SelectOption(label="LobbyCooldown",
                                                description="Change reset cooldown if LobbyAutoReset is True"),
                           discord.SelectOption(label="EnableHeroDraft",
                                                description="Enable Hero Draft"),
                           discord.SelectOption(label="EnablePlayerDraft",
                                                description="Enable Captains Mode"),
                           discord.SelectOption(label="EnableReadyUp",
                                                description="Enable ready-up phase just before lobby launch")
                       ]
                       )
    async def select_callback(self, select, interaction):
        lobby_number = await get_lobby_number(interaction)
        Lobbies[lobby_number].selected_setting = select.values[0]
        print(f"lobby{lobby_number}: admin setting dropdown set to {Lobbies[lobby_number].selected_setting}")
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

    @discord.ui.button(label="Reload Presets", style=discord.ButtonStyle.secondary, row=4)
    async def preset_button_callback(self, button, interaction):
        print(f'Received reload presets command from {interaction.user.display_name}')
        load_presets()
        await interaction.response.send_message(f"Presets reloaded. Available presets: {presets_string}", ephemeral=True)

    @discord.ui.button(label="Reload Heroes", style=discord.ButtonStyle.secondary, row=4)
    async def heroes_button_callback(self, button, interaction):
        print(f'Received reload heroes command from {interaction.user.display_name}')
        load_heroes()
        for i in range(1, len(Lobbies)):
            if not Lobbies[i].drafting_heroes and not Lobbies[i].hero_draft_completed and not Lobbies[i].launched:
                Lobbies[i].available_heroes = Heroes[:]
        await interaction.response.send_message(f"Heroes reloaded. Available heroes: {heroes_string}", ephemeral=True)


bot.run(DiscordBotToken)
