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

![Admin Panel](https://i.imgur.com/L70ApmK.png)

### Usage

Start a lobby using ```/startlobby SERVER:PORT PASSWORD PRESET```

![startlobby command](https://i.imgur.com/MFh1dV4.png)

The Preset field is case sensitive, the command discription will tell you what presets are available.
If no presets are added to the /config/presets/ folder, default will be the only available selection.

When a lobby is started you will receive a DM with the Admin Panel.

Admin panel functions:

- Waiting/Begin Hero Draft/Launch Lobby - when LobbyAutoLaunch is False the lobby will wait for the host to press this button to both begin the hero draft and to launch the lobby. If LobbyAutoLaunch is true, those steps will happen automatically and this button will not appear on the panel.
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

Any settings changed this way are only for that single lobby and will not change the settings in the preset .json files.

The last two buttons:
- Reload Presets - Loads all preset .json files in config/presets/. Useful if you want to create new configs without restarting the bot completely
- Reload Heroes - Reloads heroes from config/heroes.json

### Discord set-up
The bot requires the following permissions: Send Messages, Manage Messages, Embed Links. It also requires the "Members" Privileged Gateway Intent, permission to mention roles, and the ability to mention those roles in server settings.
The server should have a dedicated channel so the lobby is always visible at the bottom of a channel (see config below)

### Configuration
Copy config/config_example.json to config/config.json and edit accordingly. This is for your Discord Bot Token and a few other bot-wide settings.

To start a lobby you must make at least one "preset" config, examples are in config/presets/. These house the lobby-specific settings.

Heroes are configured in config/heroes.json but are limited to 25. You can also change the images the bot sends with EnableImageSend by editing config/banner_ambr.png and config/banner_sapp.png

Bot Settings (config/config.json):
- DiscordBotToken - Your bots token from the Discord Developer Portal
- BotTimezone - Timezone used for timestamps in console output. Will use this timezone instead of system time
- BotGame - Game the bot should be "Playing" in its Discord presence. Only shows after lobby is launched
- BotAdminRole* - Name of the role whose members can use /startlobby and /lbset
Preset Settings (config/presets/*.json):
- LobbyRole* - Name of the role the bot will @mention when LobbyRolePing is set to True
- LobbyRolePing - When True the bot will send a @mention of LobbyRole when a new lobby is opened
- LobbyChannel* - The Channel name where the bot will put its lobby messages
- LobbyAutoLaunch - When True will automatically start hero draft (if enabled) and send connect info to players. When False it will wait for the Admin to press the Proceed button on the Admin Panel. Setting this False allows time to shuffle teams, make sure the server is set up, etc.
- LobbyAutoReset - When True the bot will reset and reopen the lobby after LobbyCooldown has passed. When false it will close the lobby completely. Note that using the Admin Panel reset button will cause future possible resets to ignore this setting.
- LobbyMessageTitle - Title of the discord message showing the lobby information
- LobbyMessageColor and ActiveMessageColor - Hex values used for the discord embed messages
- LobbyThreshold - The number of players required to launch the lobby. Total number of players (two teams and "either"). Must be even.
- LobbyCooldown - Time after which the bot will either reset or close the lobby (based on LobbyAutoReset). Must have units attached (30m, 2h, 1d, etc). Note that using the Admin Panel reset button will force the bot to do nothing when the cooldown has passed (lobby can be reset manually via Admin Panel)
- SapphireTeamName, AmberTeamName, and EitherTeamName - The team names for the lobby (left, right, and fill teams respectively)
- EnableHeroDraft - Enables hero draft once the lobby fills up. Heroes are set in config/heroes.json but limited to 25.
- EnableImageSend - Enables the bot to send an image when it sends team assignments and connect info. Can help to make sure players know what team they're on.

(*) Role and Channel settings accept either their name or the discord ID (right click > Copy ID if you have Discord developer mode enabled)

### Other Commands (/lbcom and /lbban)

- ```/lbcom ReloadPresets```
  - Reloads presets in config/presets/ folder. Note that the /startlobby command hint that shows the available presets tends to update slowly, so it may not immediately reflect the latest information. The bots response to the ReloadPresets command will show you what presets are actually available.
- ```/lbcom ReloadHeroes```
  - Reloads heroes from config/heroes.json. Will apply to any open lobbies
- ```/lbban USERID```
  - Toggles ban status on a user. USERID must be a 20 digit Discord User ID

### Docker Images
See [Dockerhub](https://hub.docker.com/r/erkston/lobby-bot-dl)