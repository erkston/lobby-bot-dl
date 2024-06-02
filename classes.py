class Lobby:
    def __init__(self, lobby_number, message_id, host, admin_msg_id, server, password, preset, sapp_players, ambr_players,
                 fill_players, sapp_heroes, ambr_heroes, picked_heroes, active, start_draft, drafting_heroes, waiting_for_pick, drafter,
                 selected_hero, draft_complete, launched, lobby_role, lobby_role_ping, lobby_auto_launch, lobby_auto_reset,
                 lobby_message_title, lobby_message_color, active_message_color, lobby_threshold, lobby_cooldown, sapphire_name,
                 amber_name, either_name, manual_mode, selected_setting, enable_hero_draft, draft_msg):
        self.number = lobby_number
        self.message_id = message_id
        self.host = host
        self.admin_msg_id = admin_msg_id
        self.server = server
        self.password = password
        self.preset = preset
        self.sapp_players = sapp_players
        self.ambr_players = ambr_players
        self.fill_players = fill_players
        self.sapp_heroes = sapp_heroes
        self.ambr_heroes = ambr_heroes
        self.picked_heroes = picked_heroes
        self.active = active
        self.start_draft = start_draft
        self.drafting_heroes = drafting_heroes
        self.waiting_for_pick = waiting_for_pick
        self.drafter = drafter
        self.selected_hero = selected_hero
        self.draft_complete = draft_complete
        self.launched = launched
        self.lobby_role = lobby_role
        self.lobby_role_ping = lobby_role_ping
        self.lobby_auto_launch = lobby_auto_launch
        self.lobby_auto_reset = lobby_auto_reset
        self.lobby_message_title = lobby_message_title
        self.lobby_message_color = lobby_message_color
        self.active_message_color = active_message_color
        self.lobby_threshold = lobby_threshold
        self.lobby_cooldown = lobby_cooldown
        self.sapphire_name = sapphire_name
        self.amber_name = amber_name
        self.either_name = either_name
        self.manual_mode = manual_mode
        self.selected_setting = selected_setting
        self.enable_hero_draft = enable_hero_draft
        self.draft_msg = draft_msg
