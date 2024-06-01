## lobby-bot-dl
Discord bot designed to place users into a "lobby" that directs players to a server once a set amount have joined. 
Users join by clicking a button in discord.
The bot will then split the lobby members into two teams, and send team assignments and connect info via DM.

![ExampleLobby1](https://i.imgur.com/0UdUNIs.png) ![ExampleLobby2](https://i.imgur.com/VuqXvMy.png)

The bot also supports presets that act as templates to easily create lobbies for different regions, games, team sizes, etc.
The config/presets/ folder has example configs showing which settings are templatable. These settings will override the defaults in config.json when a lobby is created.

### Usage

Start a lobby using ```/startlobby SERVER:PORT PASSWORD PRESET```

![startlobby command](https://i.imgur.com/FFCDylQ.png)

The Preset field is case sensitive, the command discription will tell you what presets are available.
If no presets are added to the /config/presets/ folder, default will be the only available selection.

The bot will also send an admin panel to whoever issues the command to start the lobby:

![Admin Panel](https://i.imgur.com/LyIeob9.png)

- Launch Lobby - Launches the lobby when LobbyAutoLaunch is False. If LobbyAutoLaunch is True this button does nothing
- Reset Lobby - removes all players but keeps the lobby open
- Close Lobby - closes the lobby completely
- Shuffle Teams - Randomizes teams, if there are any fill players it will move them to a team
- Resend Connect Info - resend server address and password to lobby members via DM. Only works after the lobby has launched
- DM Players - opens a modal to send any text to all current lobby players via DM

The bottom dropdown and Change Setting button allows you to change some settings. If the lobby has already filled or launched some settings may be unavailable.

![Settings Dropdown](https://i.imgur.com/6CkYDJl.png)

Select what variable you want to change, then hit the Change Setting button. A window will come up with a text field to set the new value.

![Setting Modal](https://i.imgur.com/fSrP4vR.png)

### Discord set-up
The bot requires the following permissions: Send Messages, Manage Messages, Embed Links. It also requires permission to mention roles (and ability to mention those roles in server settings).
The server should have a dedicated channel (see config below)

### Configuration
Copy config/config_example.json to config/config.json and edit accordingly. 

config.json (along with any changes made via /lbset command) is the 'default' preset that is selected in the /startlobby command.
Any additional presets added (config/presets/NA.json, config/presets/EU.json, etc) are independent and do not affect the default config.
These templates are loaded at /startlobby command execution, so it's possible to edit the configs while the bot is still running.

Settings:
- DiscordBotToken - Your bots token from the Discord Developer Portal
- BotTimezone - Timezone used for timestamps in console output. Will use this timezone instead of system time
- BotGame* - Game the bot should be "Playing" in its Discord presence. Only shows after lobby is launched
- BotAdminRole - Name of the role whose members can use /startlobby and /lbset
- LobbyChannelName - The Channel name the bot should use to send messages
- LobbyRole - Name of the role the bot will @mention when @LobbyRolePing is set to True
- LobbyRolePing* - When True the bot will send a @mention of LobbyRole when a new lobby is opened
- LobbyAutoLaunch* - When True will automatically send connect info to lobby members. When False it will wait for the Admin to press the Launch button on the Admin Panel.
- LobbyAutoReset* - When True the bot will reset and reopen the lobby after LobbyCooldown has passed. When false it will close the lobby completely. Note that using the Admin Panel reset button will ignore this setting.
- LobbyMessageTitle* - Title of the discord message showing the lobby information
- LobbyMessageColor* and ActiveMessageColor* - Hex values used for the discord embed messages
- LobbyThreshold* - The number of players required to launch the lobby. Total number of players (two teams and "either"). Should be even.
- LobbyCooldown* - Time after which the bot will either reset or close the lobby (based on LobbyAutoReset). Must have units attached (30m, 2h, 1d, etc). Note that using the Admin Panel reset button will force the bot to do nothing when the cooldown has passed (lobby can be reset manually via Admin Panel)
- SapphireTeamName*, AmberTeamName*, and EitherTeamName - The team names for the lobby (left, right, and fill teams respectively)

### Slash Command Configuration (/lbset)
Any option listed with an asterisk(*) above can be modified on the fly by using ```/lbset SETTING VALUE```. Tab completion also works for those settings that are settable using the command.
Changing settings via the command has the benefit of not kicking everyone from the current lobby, however not all settings are available this way and some must be changed via config.json with a bot restart. 
Any changes made using the command are also temporary until the next restart. Permanent changes must be made in the config file.

These setting changes will only affect the default config and not any other presets (config/presets/NA.json, config/presets/EU.json, etc)

Examples:
- ```/lbset LobbyThreshold 14```
- ```/lbset LobbyCooldown 2h```
- ```/lbset LobbyMessageTitle 6v6 Playtest```
- ```/lbset AmberTeamName Teen Girl Squad```

Setting names are not case-sensitive, however the setting values need to follow the same format as in the config or things will start breaking.
Cooldown needs to have units (s, m, or h), colors are in hex, thresholds are integers, and Enable options are true/false.

Depending on the current state of the lobby and which setting you are changing it may update the lobby message immediately, or it may not be visible other than the bot's reply to your command.

### Other Commands (/lbcom)

- ```/lbcom ReloadPresets```
  - Reloads presets in config/presets/ folder. Note that the /startlobby command hint that shows the available presets tends to update slowly, so it may not immediately reflect the latest information. The bots response to the ReloadPresets command will show you what presets are actually available.
- ```/lbcom GetCfg```
  -  Sends you a DM with most of the current default configuration settings

### Docker Images
See [Dockerhub](https://hub.docker.com/r/erkston/lobby-bot-dl)