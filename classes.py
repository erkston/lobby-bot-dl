class Lobby:
    def __init__(self, lobby_number, message_id, host, admin_msg_id, server, password, sapp_players, ambr_players, fill_players,
                 active, lobby_role, lobby_role_ping, lobby_auto_launch, lobby_auto_reset, lobby_message_title, lobby_message_color,
                 active_message_color, lobby_threshold, lobby_cooldown, team_names, manual_mode):
        self.number = lobby_number
        self.message_id = message_id
        self.host = host
        self.admin_msg_id = admin_msg_id
        self.server = server
        self.password = password
        self.sapp_players = sapp_players
        self.ambr_players = ambr_players
        self.fill_players = fill_players
        self.active = active
        self.lobby_role = lobby_role
        self.lobby_role_ping = lobby_role_ping
        self.lobby_auto_launch = lobby_auto_launch
        self.lobby_auto_reset = lobby_auto_reset
        self.lobby_message_title = lobby_message_title
        self.lobby_message_color = lobby_message_color
        self.active_message_color = active_message_color
        self.lobby_threshold = lobby_threshold
        self.lobby_cooldown = lobby_cooldown
        self.team_names = team_names
        self.manual_mode = manual_mode
