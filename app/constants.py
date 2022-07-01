import os
import wx

# generate a (probably) unique hash to append to the
# backup folders' names to give each folder a unique name
def gen_hash():
    import hashlib
    import time

    hash = hashlib.sha1()
    hash.update(str(time.time()).encode("utf-8"))

    return hash.hexdigest()[:15]

dd = os.path.expanduser('~/.tf2-crosshair-switcher/')

defaults = {
    "folder_path": "",
    "backup_scripts": False,
    "weapon_display_type": False
}

cn = {
    "constants": {
        "defaults": defaults,
        "backup_folder_path": "{}/backup_" + gen_hash(),
        "font_size": 8,
        "data_dir": dd,
        "data_file_path": "{}/.data.txt".format(dd),
        "logs_path": "xhs_logs.txt",
        "xhair_preview_path": "{}/preview/"  # Format with materials directory
    },

    "options": defaults.copy(),

    ##########################
    #           UI           #
    ##########################

    "ui": {
        "btn_apply": "Apply",
        "btn_apply_class": "Apply to all weapons of this class",
        "btn_apply_slot": "Apply to all weapons of this slot",
        "btn_apply_all": "Apply to all weapons",
        "btn_change_folders": "Change scanned folders",
        "chk_display_toggle": "Toggle display type",
        "chk_backup_scripts": "Backup scripts before modifying",
        "invalid_folder_msg": "Either scripts or thumbnails folder is missing or invalid\nPlease indicate their location below",
        "parse_error_msg": "Error parsing some crosshair scripts. \n Error in file {} \n Please double check that your scripts are valid",
        "generate_config_msg": "Will generate scripts/ and /materials/vgui/replay/thumbnail folders within the folder you select and populate them with sample weapon configs and crosshair files",
        "add_custom_xhairs_msg": "Will add custom crosshairs to the available list of crosshairs in the dropdown. Ensure the folder you select contains two sub-folders:\n\n/crosshairs -- for the crosshair vtf/vmts\n/display -- for the crosshair display .pngs.\n\nNAMES MUST MATCH BETWEEN THESE TWO FOLDERS",
        "gen_xhair_config_frame_title": "Generate Sample Crosshair Config",    
        "about_msg": "Made by Max M/laz",

        "menubar_file_open_text": "Open Folder",
        "menubar_file_open_description": "Open Crosshair Folder",
        "menubar_file_opts_text": "Options",
        "menubar_file_opts_description": "Options",
        "menubar_file_gen_xhairs_text": "Generate Config",
        "menubar_file_gen_xhairs_description": "Generate Sample Crosshair Config",
        "menubar_file_quit_text": "Quit",
        "menubar_file_quit_description": "Quit application",
        "menubar_about_about_text": "About",
        "menubar_about_about_description": "About",

        "window_size": (950, 600),
        "window_size_options": (500, 150),
        "window_size_min": (900, 500),
        "window_size_options_frame": (500, 135),
        "window_size_info_frame": (500, 135),
        "window_size_crosshair_image_frame": (500, 135),
        "window_size_about_frame": (500, 135),

        "xhair_preview_background_color": wx.Colour(150, 150, 150)
    },
    
    "default_crosshair_data": {
                            #x,y,width,height of default crosshair for each weapon script
                            "_32_32_32_32": ["tf_weapon_bat","tf_weapon_bat_fish","tf_weapon_bat_giftwrap","tf_weapon_bat_wood","tf_weapon_bottle","tf_weapon_buff_item","tf_weapon_cannon","tf_weapon_cleaver","tf_weapon_club","tf_weapon_fists",
                                        "tf_weapon_flamethrower","tf_weapon_grenadelauncher","tf_weapon_katana","tf_weapon_parachute","tf_weapon_parachute_primary","tf_weapon_parachute_secondary","tf_weapon_particle_cannon",
                                        "tf_weapon_passtime_gun","tf_weapon_pipebomblauncher","tf_weapon_robot_arm","tf_weapon_rocketlauncher","tf_weapon_rocketlauncher_airstrike","tf_weapon_rocketlauncher_directhit",
                                        "tf_weapon_shotgun_building_rescue","tf_weapon_shovel","tf_weapon_spellbook","tf_weapon_stickbomb","tf_weapon_sword","tf_weapon_wrench"
                                        ],
        
                            "_64_64_64_64": ["tf_weapon_minigun"],
        
                            "_0_0_32_32": ["tf_weapon_charged_smg","tf_weapon_compound_bow","tf_weapon_crossbow","tf_weapon_drg_pomson","tf_weapon_flaregun","tf_weapon_flaregun_revenge","tf_weapon_grapplinghook",
                                           "tf_weapon_handgun_scout_primary","tf_weapon_handgun_scout_secondary","tf_weapon_mechanical_arm","tf_weapon_pep_brawler_blaster","tf_weapon_pistol","tf_weapon_pistol_scout",
                                           "tf_weapon_raygun","tf_weapon_scattergun","tf_weapon_sentry_revenge","tf_weapon_shotgun_hwg","tf_weapon_shotgun_primary","tf_weapon_shotgun_pyro","tf_weapon_shotgun_soldier",
                                           "tf_weapon_smg","tf_weapon_soda_popper","tf_weapon_syringegun_medic"
                                           ],
        
                            "_64_0_32_32": ["tf_weapon_bonesaw","tf_weapon_fireaxe","tf_weapon_knife","tf_weapon_laser_pointer","tf_weapon_revolver","tf_weapon_sniperrifle","tf_weapon_sniperrifle_classic",
                                           "tf_weapon_sniperrifle_decap"
                                           ],
        
                            "_0_64_32_32": ["tf_weapon_medigun"],
        
                            "_0_48_24_24": ["tf_weapon_builder","tf_weapon_invis","tf_weapon_jar","tf_weapon_jar_milk","tf_weapon_lunchbox","tf_weapon_lunchbox_drink","tf_weapon_objectselection",
                                            "tf_weapon_pda_engineer_build","tf_weapon_pda_engineer_destroy","tf_weapon_pda_spy","tf_weapon_sapper"
                                            ]
    }
    
    
}
