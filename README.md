## lobby-bot-dl
A discord bot designed to place users into a lobby that directs players to a server once a set amount have joined. 
Users join the lobby by clicking a button in discord.
Once a threshold is reached the bot will split the lobby members into two teams, and send team assignments and connect info via DM.

#### Key features

- Team selection
  - Players can select whichever team they'd like, or click "Either" to fill any remaining spots
- Full hero draft
  - If enabled, the bot will message all players one by one to draft a hero. Draft information is updated live in the lobby message. Heroes can be set in config/heroes.json
- Preset support
  - Presets can be made to template most available options. Allows you to easily create lobbies for different regions, games, etc.
- Kick/Ban system
  - Bans are persistent across bot restarts and are bot-wide (not specific to a single lobby)
- Private admin panel
  - Shows the lobby state, values of important settings, and allows you to change settings, kick/ban players, and perform other admin functions

#### Screenshots
Example lobby:

![Example Lobby](https://i.imgur.com/bQ32Eq3.png)

Hero draft:

![Hero Draft](https://i.imgur.com/BXHB2yr.png)

Admin panel:

![Admin Panel](https://i.imgur.com/nS9PJg1.png)

### Usage

Start a lobby using ```/startlobby SERVER:PORT PASSWORD PRESET```

![startlobby command](https://i.imgur.com/FFCDylQ.png)

The Preset field is case sensitive, the command discription will tell you what presets are available.
If no presets are added to the /config/presets/ folder, default will be the only available selection.

When a lobby is started you will receive a DM with the Admin Panel.

Admin panel functions:

- Proceed - when LobbyAutoLaunch is False the lobby will wait for the host to press this button before beginning the hero draft or launching the lobby. If LobbyAutoLaunch is True this button does nothing as the lobby will take these steps automatically
- Reset Lobby - removes all players but keeps the lobby open
- Close Lobby - closes the lobby completely
- Shuffle Teams - Randomizes teams, if there are any fill players it will move them to a team. You can shuffle a team up until the hero draft is started
- Resend Connect Info - resend server address and password to lobby members via DM. Only works after the lobby has launched
- DM Players - opens a modal to send any text to all current lobby players via DM
- Kick Player - Kicks a player from the lobby, requires their discord User ID.
- Ban/Unban Players - Bans a player if they're not already banned, or unbans them if they are already banned. Banning a player also kicks them from any open lobbies. Bans are bot-wide and not for a particular lobby and will also persist across bot restarts. Requires discord User ID.

For kick and ban functions the easiest way to get a User ID is to enable Developer Mode in Discord (Settings > Advanced). 
Once enabled you can get someone's User ID by right clicking on them and selecting Copy User ID.

The bottom dropdown and Change Setting button allows you to change some settings. If the lobby has already filled or launched some settings may be unavailable.

![Settings Dropdown](https://i.imgur.com/6CkYDJl.png)

Select what variable you want to change, then hit the Change Setting button. A window will come up with a text field to set the new value.

![Setting Modal](https://i.imgur.com/fSrP4vR.png)

Any settings changed this way are only for that single lobby and will not change any of the default or preset settings.

The last two buttons:
- Get default cfg - Sends you a DM with the current default configuration. This will reflect any changes made with /lbset since the bot was started
- Reload Presets - Loads all preset .json files in config/presets/. Useful if you want to create new configs without restarting the bot completely

### Discord set-up
The bot requires the following permissions: Send Messages, Manage Messages, Embed Links. It also requires the "Members" Privileged Gateway Intent, permission to mention roles, and the ability to mention those roles in server settings.
The server should have a dedicated channel so the lobby is always visible at the bottom of a channel (see config below)

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
- EnableHeroDraft* - Enables hero draft once the lobby fills up. Heroes are set in config/heroes.json but limited to 25. Heroes are set at bot start and can't be reloaded while running

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
- ```/lbset EnableHeroDraft True```

Setting names are not case-sensitive, however the setting values need to follow the same format as in the config or things will start breaking.
Cooldown needs to have units (s, m, or h), colors are in hex, thresholds are integers, and Enable options are true/false.

Depending on the current state of the lobby and which setting you are changing it may update the lobby message immediately, or it may not be visible other than the bot's reply to your command.

### Other Commands (/lbcom and /lbban)

- ```/lbcom ReloadPresets```
  - Reloads presets in config/presets/ folder. Note that the /startlobby command hint that shows the available presets tends to update slowly, so it may not immediately reflect the latest information. The bots response to the ReloadPresets command will show you what presets are actually available.
- ```/lbcom GetCfg```
  -  Sends you a DM with most of the current default configuration settings
- ```/lbban USERID```
  - Toggles ban status on a user. USERID must be a 20 digit Discord User ID

### Docker Images
See [Dockerhub](https://hub.docker.com/r/erkston/lobby-bot-dl)