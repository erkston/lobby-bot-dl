## lobby-bot-dl
Discord bot designed to place users into a "lobby" that directs players to a server once a set amount have joined. 
Users join by clicking a button in discord.
The bot will then split the lobby members into two teams, and send team assignments and connect info via DM.

![Example lobby](https://i.imgur.com/irE9DGl.png)

### Usage

Start a lobby using /startlobby SERVER PASSWORD

![startlobby command](https://i.imgur.com/t24JErN.png)

The bot will also send an admin panel to whoever issues the command to start the lobby:

![Admin Panel](https://i.imgur.com/tFmk2Wf.png)

- Reset Lobby - removes all players but keeps the lobby open
- Close Lobby - closes the lobby completely
- Resend Connect Info - resend server address and password to lobby members via DM. Only works after the lobby has launched
- DM Players - opens a modal to send any text to all current lobby players via DM


### Discord set-up
The bot requires the following permissions: Send Messages, Manage Messages, Embed Links. It also requires the "Members" Privileged Gateway Intent, and permission to mention roles.
The server should have a dedicated channel and role as well (see config below)

### Configuration
- DiscordBotToken - Your bots token from the Discord Developer Portal
- BotTimezone - Timezone used for timestamps in console output. Will use this timezone instead of system time
- BotGame* - Game the bot should be "Playing" in its Discord presence. Only shows after lobby is launched
- BotAdminRole - Name of the role whose members can use /startlobby and /lbset
- LobbyChannelName - The Channel name the bot should use to send messages
- LobbyRole - Name of the role the bot will @mention when @LobbyRolePing is set to True
- LobbyRolePing* - When True the bot will send a @mention of LobbyRole when a new lobby is opened
- LobbyAutoReset* - When True the bot will reset and reopen the lobby after LobbyCooldown has passed. When false it will close the lobby completely.
- LobbyMessageTitle* - Title of the discord message showing the lobby information
- LobbyMessageColor* and ActiveMessageColor* - Hex values used for the discord embed messages
- LobbyThreshold* - The number of players required to launch the lobby. Total number of players (two teams and "either"). Should be even.
- LobbyCooldown* - Time after which the bot will either reset or close the lobby (based on LobbyAutoReset). Must have units attached (30m, 2h, 1d, etc) 
- TeamNames - The two team names the bot will split lobby members into

### Slash Command Configuration (/lbset)
Any option listed with an asterisk(*) above can be modified on the fly by using "/lbset SETTING VALUE". Tab completion also works for those settings that are settable using the command.
Changing settings via the command has the benifit of not kicking everyone from the current lobby, however not all settings are available this way and some must be changed via config.json with a bot restart. Any changes made using the command are also temporary until the next restart. Permanent changes must be made in the config file.

Examples:
- /lbset LobbyThreshold 14
- /lbset LobbyCooldown 2h
- /lbset LobbyMessageTitle Cool Guys

Setting names are not case-sensitive, however the setting values need to follow the same format as in the config or things will start breaking.
Cooldown needs to have units (s, m, or h), colors are in hex, thresholds are integers, and Enable options are true/false.

Depending on the current state of the lobby and which setting you are changing it may update the lobby message immediately, or it may not be visible other than the bot's reply to your command.

/lbset getcfg ANYVALUE will send you a DM with most of the current configuration settings (BotAdminRole still required)

### Docker Images
See [Dockerhub](https://hub.docker.com/r/erkston/lobby-bot-dl)