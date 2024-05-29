## lobby-bot-dl
This is a discord bot designed to place users into a "lobby" that directs players to a server once a set amount have joined. 
Users join the lobby by clicking a button in discord.
The bot will then split the lobby members into two teams, and send team assignments and connect info via DM.

![Example lobby](https://i.imgur.com/mf8fbxC.png)

It will also send a discord ping to a specific role. The goal is to only send pings that people actively want by having them join the lobby specifically to be alerted.
Based on lobby-bot, adapted for an upcoming multiplayer game.
## Discord set-up
The bot requires the following permissions: Manage Roles, Send Messages, Manage Messages, Embed Links. It also requires the "Members" Privileged Gateway Intent, and permission to mention roles.
The server should have a dedicated channel and role as well (see config below)
## Configuration
- DiscordBotToken - Your bots token from the Discord Developer Portal
- BotTimezone - Timezone used for timestamps in console output. Will use this timezone instead of system time
- BotGame* - Game the bot should be "Playing" in its Discord presence. Only shows after lobby is launched
- BotAdminRole - Name of the role whose members can change config options via /lbset
- LobbyChannelName - The Channel name the bot should use to send messages
- LobbyRole - The Role name the bot should use to alert people once the lobby is full. This should be a role dedicated for bot use, all members are removed from the role after pings are sent.
- LobbyMessageTitle* - Title of the discord message showing the lobby information
- LobbyMessageColor* and NappingMessageColor* - Hex values used for the discord embed messages
- NudgeMessageEnable* - Enables or disables a "nudge" message in a text channel to alert other users that the lobby is almost full
- NudgeCooldown* - Cooldown for nudge messages to prevent spamming too much
- NudgeThreshold* - The number of players needed to send a nudge message. As the lobby is filling, if the number of additional people needed reaches this number (or less) it will send a nudge message
- NudgeChannelName - Name of the text channel to use for the nudge messages
- LobbyThreshold* - The number of players the bot should wait for before sending discord pings. This is total players including any already on the server
- LobbyCooldown* - Time that the bot will sleep for after sending discord pings. After this time is up it will start checking the server player count against LobbyRestartThreshold. Must have units attached (30m, 2h, 1d, etc) 
- PingRemovalTimer* - The bot will remove the message with the Role pings after this amount of time has passed. Must have units attached (10m, 30m, 1h, etc) 
- TeamNames - The two team names the bot will split lobby members into
- Servers - List of servers to check, can be any number of servers as long as the syntax is preserved. The bot will check current playercount for all servers in the list and select the one with the most players to direct lobby members to. 
- NudgeMessages - The text of the nudge messages. The bot selects from this list at random and adds a link to LobbyChannel
## Slash Command Configuration (/lbset, /lbcfg, /lbreset)
Any option listed with an asterisk(*) above can be modified on the fly by using "/lbset SETTING VALUE". Tab completion also works for those settings that are settable using the command.
Changing settings via the command has the benifit of not kicking everyone from the current lobby, however not all settings are available this way and some must be changed via config.json with a bot restart. Any changes made using the command are also temporary until the next restart. Permanent changes must be made in the config file.

Examples:
- /lbset LobbyThreshold 14
- /lbset LobbyCooldown 2h
- /lbset NudgeMessageEnable False
- /lbset NudgeCooldown 1h

Setting names are not case-sensitive, however the setting values need to follow the same format as in the config or things will start breaking.
Cooldowns/timers need to have units (s, m, or h), colors are in hex, thresholds are integers, and Enable options are true/false.

Depending on the current state of the lobby and which setting you are changing it may update the lobby message immediately, or it may not be visible other than the bot's reply to your command.

/lbcfg will send you a DM with most of the current configuration settings (BotAdminRole still required)

/lbreset will reset the lobby completely and remove all existing members.

## Docker Images
See Dockerhub