class Lobby:
    def __init__(self, lobby_number, message_id, host, admin_msg_id, server, password, preset, sapp_players, ambr_players,
                 fill_players, sapp_heroes, ambr_heroes, available_heroes, picked_heroes, active, drafting_heroes, waiting_for_pick, drafter,
                 selected_hero, hero_draft_completed, launched, lobby_role, lobby_role_ping, lobby_auto_launch, lobby_auto_reset,
                 lobby_message_title, lobby_message_color, active_message_color, lobby_threshold, lobby_cooldown, sapphire_name,
                 amber_name, either_name, manual_mode, selected_setting, enable_hero_draft, draft_msg, enable_image_send, lobby_channel,
                 enable_player_draft, drafting_players, player_draft_completed, sapp_captain, ambr_captain, player_pool, selected_player,
                 selecting_captains, enable_ready_up, readying, all_players_ready, sapp_players_ready, ambr_players_ready,
                 sapp_ready_msgs, ambr_ready_msgs):
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
        self.available_heroes = available_heroes
        self.picked_heroes = picked_heroes
        self.active = active
        self.drafting_heroes = drafting_heroes
        self.waiting_for_pick = waiting_for_pick
        self.drafter = drafter
        self.selected_hero = selected_hero
        self.hero_draft_completed = hero_draft_completed
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
        self.enable_image_send = enable_image_send
        self.lobby_channel = lobby_channel
        self.enable_player_draft = enable_player_draft
        self.drafting_players = drafting_players
        self.player_draft_completed = player_draft_completed
        self.sapp_captain = sapp_captain
        self.ambr_captain = ambr_captain
        self.player_pool = player_pool
        self.selected_player = selected_player
        self.selecting_captains = selecting_captains
        self.enable_ready_up = enable_ready_up
        self.readying = readying
        self.all_players_ready = all_players_ready
        self.sapp_players_ready = sapp_players_ready
        self.ambr_players_ready = ambr_players_ready
        self.sapp_ready_msgs = sapp_ready_msgs
        self.ambr_ready_msgs = ambr_ready_msgs
