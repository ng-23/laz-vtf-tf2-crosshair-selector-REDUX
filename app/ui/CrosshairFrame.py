
import wx
import wx.lib.mixins.listctrl
import os
import shutil
import datetime
import re

from app.utils import (
    get_crosshairs, 
    prepare_entries, 
    sort_entries, 
    get_scripts_path, 
    get_xhairs_path,
    persist_options,
    format_path_by_os,
    get_xhair_display_path,
    reconstruct_cfg,
    write_cfg,
    resource_path,
    initialize_local_storage
)
from app.constants import cn
from app.associations import weapon_associations
from app.ui.OptionsFrame import OptionsFrame
from app.ui.InfoFrame import InfoFrame
from app import vtf_convert

def make_frame():
    return CrosshairFrame(None, "VTF Crosshair Changer", cn["ui"]["window_size"])

# mixin to ensure columns cannot be resized past the viewport
class FixedWidthListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(0)


# Main GUI frame
class CrosshairFrame(wx.Frame):

    def on_close(self, e):
        # Clearing folder(s) that store preview PNGs to save space
        exe_pngs_filepath = format_path_by_os(cn["constants"]["data_dir"] + "display") #this seems to be created automatically even when running .py script, still checking if exists just to be sure
        # py_script_pngs_filepath = format_path_by_os(os.getcwd() + "/assets/display")
        if os.path.isdir(exe_pngs_filepath):
            if len(os.listdir(exe_pngs_filepath)) > 0:
                for file_name in os.listdir(exe_pngs_filepath):
                    file_path = os.path.join(exe_pngs_filepath, file_name)
                    os.remove(file_path)
                    
        # if os.path.isdir(py_script_pngs_filepath):            
            # if len(os.listdir(py_script_pngs_filepath)) > 0:
                # for file_name in os.listdir(py_script_pngs_filepath):
                    # file_path = os.path.join(py_script_pngs_filepath, file_name)
                    # os.remove(file_path)
                   
        for child in self.GetChildren():
            child.Destroy()

        self.Destroy()


    def init_log(self):
        if os.path.isdir(get_scripts_path()):
            display_path = format_path_by_os(os.path.abspath(get_scripts_path()))
            self.logs_add("Scripts being read from {}".format(display_path))

        if os.path.isdir(get_xhairs_path()):
            display_path = format_path_by_os(os.path.abspath(get_xhairs_path()))
            self.logs_add("Crosshairs being read from {}".format(display_path))

        if len(self.entries) == 0:
            self.logs_add("Error loading scripts. Does the folder you selected have a scripts/ folder?")

        if len(self.xhairs) == 0:
            self.logs_add("Error loading crosshairs. Does the folder you selected have a materials/vgui/replay/thumbnails/ folder?")


    def setup_menu_bar(self):
        self.menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        about_menu = wx.Menu()

        file_open_item = file_menu.Append(wx.ID_OPEN, cn["ui"]["menubar_file_open_text"], cn["ui"]["menubar_file_open_description"])
        file_opts_item = file_menu.Append(wx.ID_PROPERTIES, cn["ui"]["menubar_file_opts_text"], cn["ui"]["menubar_file_opts_description"])
        file_gen_xhairs_item = file_menu.Append(wx.Window.NewControlId(), cn["ui"]["menubar_file_gen_xhairs_text"], cn["ui"]["menubar_file_gen_xhairs_description"])
        file_quit_item = file_menu.Append(wx.ID_EXIT, cn["ui"]["menubar_file_quit_text"], cn["ui"]["menubar_file_quit_description"])

        about_about_item = about_menu.Append(wx.Window.NewControlId(), cn["ui"]["menubar_about_about_text"], cn["ui"]["menubar_about_about_description"])

        self.menu_bar.Append(file_menu, 'File')
        self.menu_bar.Append(about_menu, 'About')

        def change_folders_dialog(func):
            def _func(e, parent=None):
                folder_dialog = wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE)

                folder_path = ""
                status = folder_dialog.ShowModal()
                
                if parent is not None:
                    parent.Destroy()

                if status == wx.ID_OK:
                    folder_path = folder_dialog.GetPath()
                    folder_dialog.Destroy()
                    func(folder_path)
                    
            return _func


        def open_new_folder(path):
            cn["options"]["folder_path"] = path
            persist_options()
            self.Destroy()
            make_frame()



        def generate_config(path):
            shutil.copytree(resource_path("assets/sample-xhair-config/materials"), "{}/materials".format(path))
            shutil.copytree(resource_path("assets/sample-xhair-config/scripts"), "{}/scripts".format(path))

            cn["options"]["folder_path"] = path
            persist_options()

            self.Destroy()
            newframe = make_frame()

            newframe.logs_add("Generated sample config at {}".format(path))


        def add_custom_xhairs(path):
            cn["options"]["addional_xhairs_path"] = path
            persist_options()

            self.Destroy()
            make_frame()


        self.Bind(wx.EVT_MENU, change_folders_dialog(open_new_folder), file_open_item)
        self.Bind(wx.EVT_MENU, lambda _: OptionsFrame(self, "Options", cn["ui"]["window_size_options_frame"]), file_opts_item)
        self.Bind(wx.EVT_MENU, lambda _: self.Close(), file_quit_item)

        def gen_xhairs_item_action(_):
            InfoFrame(
                self, 
                title="Generate Sample Crosshair Config", 
                size=cn["ui"]["window_size_info_frame"],
                info_text=cn["ui"]["generate_config_msg"],
                btn_text="Select a folder",
                btn_func=change_folders_dialog(generate_config)
            )
        self.Bind(wx.EVT_MENU, gen_xhairs_item_action, file_gen_xhairs_item)


        


        self.Bind(
            wx.EVT_MENU, 
            lambda _: InfoFrame(
                self, "About", cn["ui"]["window_size_about_frame"],
                info_text=cn["ui"]["about_msg"], 
                btn_text="Close",
                btn_func=lambda _, frame: frame.Close() 
            ), 
            about_about_item)


        self.SetMenuBar(self.menu_bar)

    def setup_panels(self):
        
        # Top/bottom layout, divides the weapon list & weapon info from the log viewer & options
        box_main = wx.BoxSizer(wx.VERTICAL)

        # Left/right layout, divides the weapon list from the weapon info (nested inside box_tb)
        box_weapon = wx.BoxSizer(wx.HORIZONTAL)

        # Vertical layout within weapon info panel to arrange the info text with the xhair combo box, apply buttons, and xhair preview
        box_weapon_info = wx.BoxSizer(wx.VERTICAL)

        # Separates the xhair selector/buttons from the xhair preview
        box_controls = wx.BoxSizer(wx.HORIZONTAL)

        # Contains xhair selector/buttons
        box_buttons = wx.BoxSizer(wx.VERTICAL)

        # Horizontal layout for bottom panel (log viewer & options)
        box_bottom = wx.BoxSizer(wx.HORIZONTAL)

        # Initialize controls for top layout

        # Top-left weapon list panel
        self.weapon_list = FixedWidthListCtrl(self.main_panel, -1, size=(500, -1), style=wx.LC_REPORT)

        self.weapon_list.SetFont(wx.Font(cn["constants"]["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))
        self.weapon_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_select)
        self.weapon_list.Bind(wx.EVT_LIST_COL_CLICK, self.col_click)
        self.weapon_list_sort = [1, 0]
        self.last_selection = 0

        self.populate_list()

        # Top-right weapon info text panel
        self.text = wx.TextCtrl(self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.text.Bind(wx.EVT_KEY_DOWN, lambda e: e.Skip())
        self.text.SetFont(wx.Font(cn["constants"]["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.NORMAL))

        # Actions in right panel under info (xhair select, buttons)
        self.xhair_choice = wx.Choice(self.main_panel, choices=self.xhairs)
        self.btn_apply = wx.Button(self.main_panel, label=cn["ui"]["btn_apply"])
        self.btn_apply_class = wx.Button(self.main_panel, label=cn["ui"]["btn_apply_class"])
        self.btn_apply_slot = wx.Button(self.main_panel, label=cn["ui"]["btn_apply_slot"])
        self.btn_apply_all = wx.Button(self.main_panel, label=cn["ui"]["btn_apply_all"])

        # Called to when clicking a crosshair option
        # Crosshair PNGs to only exist as-needed
        # So display folders will be empty to start
        # But when user clicks a crosshair option
        # This should (1)try to create a PNG and save it to either .exe/.py display folder if it doesn't already exist
        # and (2)set_image(xhair_display_path)
        def xhair_chosen(evt):
            choice = self.xhair_choice.GetStringSelection() # name of the crosshair, converted to string
            xhair_display_path = get_xhair_display_path(choice) # full path to the crosshair file in the assets folder
            
            if choice != "crosshairs": # if user isn't trying to choose the default crosshair
            
                # display_path != xhair_path
                # xhair_path is the path to the folder with all VTFs
                # display_path points to display folder
                if xhair_display_path is None:
                    vtf_file = get_xhairs_path() + "/%s.vtf" % (choice)
                    vtf_header_bytes_hex = open(vtf_file,'rb').read(80)
                
                    if vtf_convert.validate_vtf_header(vtf_header_bytes_hex):
                        vtf_png = vtf_convert.vtf2png(vtf_file)
                    
                        if vtf_png == None:
                            self.logs_add("Could not convert %s.vtf to PNG. Please ensure VTF high-res image format is RGBA32, BGRA32, ABRG32, or DXT5." % (choice))
                            self.set_image("")
                        
                        else:
                            self.logs_add("Successfully converted %s.vtf to PNG!" % (choice))
                            #assuming user only has 2 ways to run program: Either .py script or .exe file
                            #can use either display path from .exe or .py (which is a subfolder of assets)
                            #since user is more likely to be using .exe, try saving to there first
                            #otherwise, save to py_script_pngs_filepath
                            #since .exe display path is created regardlesss, may just be better to save there no matter what
                            exe_pngs_filepath = format_path_by_os(cn["constants"]["data_dir"] + "display")
                            # py_script_pngs_filepath = format_path_by_os(os.getcwd() + "/assets/display")
                        
                            if os.path.isdir(exe_pngs_filepath):
                                self.logs_add("Temporarily saving %s.png to %s" % (choice,exe_pngs_filepath))
                                vtf_png.save(exe_pngs_filepath + "/%s.png" % (choice))
                            else:
                                self.logs_add("Couldn't find %s. Recreating..." % (exe_pngs_filepath))
                                initialize_local_storage()
                                self.logs_add("Temporarily saving %s.png to %s" % (choice,exe_pngs_filepath))
                                vtf_png.save(exe_pngs_filepath + "/%s.png" % (choice))
                            
                            # if os.path.isdir(py_script_pngs_filepath):                                 
                                # self.logs_add("Temporarily saving %s.png to %s" % (choice,py_script_pngs_filepath))
                                # vtf_png.save(py_script_pngs_filepath + "/%s.png" % (choice))
                            
                            self.set_image(get_xhair_display_path(choice))
                        
                    else:
                        self.logs_add("Could not convert %s.vtf to PNG. Please ensure file header is untampered." % (choice))
                        self.set_image("")
                    
                else:
                    # this is if crosshair already exists as a PNG in assets folder
                    # should user delete a PNG from display folder, the first if condition will replace it
                    self.logs_add("Reading %s.png from %s" % (choice,format_path_by_os(xhair_display_path)))
                    self.set_image(xhair_display_path)
                    
            else:
                self.logs_add("Notice: 'crosshairs' option is the game's default crosshair for a weapon. There should not be a VTF of the same name.")
                self.set_image("")

        self.xhair_choice.Bind(wx.EVT_CHOICE, xhair_chosen)
        self.btn_apply.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_class.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_slot.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.btn_apply_clicked)

        box_buttons.Add(self.xhair_choice, wx.SizerFlags().Border(wx.TOP, 10))
        box_buttons.Add(self.btn_apply)
        box_buttons.Add(self.btn_apply_class)
        box_buttons.Add(self.btn_apply_slot)
        box_buttons.Add(self.btn_apply_all)

        self.xhair_preview = wx.StaticBitmap(self.main_panel, -1)
        self.xhair_preview.SetBackgroundColour(cn["ui"]["xhair_preview_background_color"])


        box_controls.Add(box_buttons, wx.SizerFlags().Expand().Proportion(50))
        box_controls.Add(self.xhair_preview, wx.SizerFlags().Expand().Proportion(50))

        box_weapon_info.Add(self.text, wx.SizerFlags().Expand().Proportion(50))
        box_weapon_info.Add(box_controls, wx.SizerFlags().Expand().Proportion(50))

        box_weapon.Add(self.weapon_list, wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))
        box_weapon.Add(box_weapon_info, wx.SizerFlags().Expand().Proportion(50).Border(wx.ALL, 10))

        # Bottom-left logging panel
        self.logger = wx.TextCtrl(self.main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.logger.AppendText("LOGS:\n")
        self.logger.SetFont(wx.Font(cn["constants"]["font_size"], wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.BOLD))
        self.logger.Bind(wx.EVT_KEY_DOWN, lambda e: e.Skip())

        self.logs = []

        box_bottom.Add(self.logger, wx.SizerFlags().Expand().Proportion(100).Border(wx.ALL, 10))

        box_main.Add(box_weapon, wx.SizerFlags().Expand().Proportion(70))
        box_main.Add(box_bottom, wx.SizerFlags().Expand().Proportion(30).Border(wx.TOP, 10))

        self.main_panel.SetSizer(box_main)
        self.main_panel.Fit()


    # Called to when clicking a weapon script or a crosshair
    def set_image(self, crosshair_filepath):
        bitmap = wx.NullBitmap

        if os.path.exists(crosshair_filepath):
            bitmap = wx.Bitmap(crosshair_filepath)
            

        self.xhair_preview.SetBitmap(bitmap)
        self.main_panel.Layout()
        

    # Logs

    # Add a log with a timestamp and show in logger
    def logs_add(self, item):
        now = datetime.datetime.now()
        time = [now.hour, now.minute, now.second]

        def pad(n):
            out = str(n)
            return "0" + out if len(out) == 1 else out

        self.logs.append([time, item])
        self.logger.AppendText("[{}:{}:{}] {}\n".format(
            pad(time[0]), pad(time[1]), pad(time[2]), item))

    # Clear logs
    def logs_clear(self):
        self.logs = []
        self.logger.SetValue("LOGS:\n")

    

    # Toggle controls depending on if a list box option is selected
    def toggle_controls(self, on):
        if on:
            self.xhair_choice.Enable()
            self.btn_apply.Enable()
            self.btn_apply_class.Enable()
            self.btn_apply_slot.Enable()
            self.btn_apply_all.Enable()
        else:
            self.xhair_choice.Disable()
            self.btn_apply.Disable()
            self.btn_apply_class.Disable()
            self.btn_apply_slot.Disable()
            self.btn_apply_all.Disable()


    # Populate list box with weapon
    def populate_list(self):
        sort_entries(self.entries, self.weapon_list_sort)

        self.weapon_list.ClearAll()
        self.weapon_list.InsertColumn(0, "Weapon", width=200)
        self.weapon_list.InsertColumn(1, "Crosshair", wx.LIST_FORMAT_RIGHT, width=200)

        for x in self.entries:
            label = x["name"] if cn["options"]["weapon_display_type"] else "{}: {}".format(weapon_associations[x["name"]]["class"], weapon_associations[x["name"]]["display"])

            self.weapon_list.Append([label, x["xhair"]])

        self.weapon_list.EnsureVisible(self.last_selection)

    # copy all script files to the backup folder
    def backup_scripts(self):
        scripts_path = get_scripts_path()
        backup_path = cn["constants"]["backup_folder_path"].format(scripts_path)

        if os.path.isdir(backup_path) or not os.path.isdir(scripts_path):
            return

        os.mkdir(backup_path)

        files = [f for f in os.listdir(scripts_path) if os.path.isfile(os.path.join(scripts_path, f))]
        re_weapon = "^(tf_weapon_[a-zA-Z_]+)\.txt$"

        for file in files:
            if not re.search(re_weapon, file):
                continue

            shutil.copyfile("{}/{}".format(scripts_path, file), "{}/{}".format(backup_path, file))
            self.logs_add("Backed up {} to folder {}".format(file, format_path_by_os(cn["constants"]["backup_folder_path"].format(scripts_path))))

    # on-click for the 4 apply buttons
    def btn_apply_clicked(self, event):
        label = event.GetEventObject().GetLabel()

        if len(self.cur_entries) == 0:
            return

        cur_xhair = self.xhair_choice.GetString(self.xhair_choice.GetSelection())

        def change_entry(entry):
            fname = entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"]
            old_xhair = fname.split("/")[-1]

            if old_xhair == cur_xhair:
                self.logs_add("Skipped {} (was already {})".format(
                    entry["name"], old_xhair))
            else:
                entry["cfg"]["WeaponData"]["TextureData"]["\"crosshair\""]["file"] = "/".join(fname.split("/")[:-1]) + "/" + cur_xhair
                entry["xhair"] = cur_xhair

                out = reconstruct_cfg(entry["cfg"])
                write_cfg(entry["path"], out)
                self.logs_add("{} changed from {} to {}".format(entry["name"], old_xhair, cur_xhair))

        if cn["options"]["backup_scripts"]:
            self.backup_scripts()

        if label == cn["ui"]["btn_apply"]:
            for entry in self.cur_entries:
                change_entry(entry)

        elif label == cn["ui"]["btn_apply_class"]:
            # filter out weapons with different classes
            class_name = weapon_associations[self.cur_entries[0]["name"]]["class"]
            included_names = {k: v for (k, v) in weapon_associations.items() if v["class"] == class_name}.keys()
            included_entries = filter(lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == cn["ui"]["btn_apply_slot"]:
            # filter out entries with different slots
            slot = weapon_associations[self.cur_entries[0]["name"]]["slot"]
            included_names = {k: v for (k, v) in weapon_associations.items() if v["slot"] == slot}.keys()
            included_entries = filter(lambda x: x["name"] in included_names, self.entries)

            for entry in included_entries:
                change_entry(entry)
        elif label == cn["ui"]["btn_apply_all"]:
            for entry in self.entries:
                change_entry(entry)

        self.populate_list()

    def on_list_select(self, event):
        self.weapon_list.setResizeColumn(0)

        display = {"classes": [], "weapons": [],
                   "categories": [], "affected": []}

        def get_selected_items():
            s = []
            it = -1
            while (True):
                nxt = self.weapon_list.GetNextSelected(it)
                if nxt == -1:
                    return s

                s.append(nxt)
                it = nxt

        selected = get_selected_items()
        self.cur_entries = []

        for i in selected:
            entry = self.entries[i]
            asc = weapon_associations[entry["name"]]

            asc["class"] not in display["classes"] and display["classes"].append(asc["class"])
            display["weapons"].append(entry["name"])
            asc["display"] not in display["categories"] and display["categories"].append(asc["display"])

            for item in asc["all"]:
                item not in display["affected"] and display["affected"].append(item)

            self.cur_entries.append(list(filter(lambda x: x["name"] == entry["name"], self.entries))[0])
            cur_xhair = self.cur_entries[-1]["xhair"]

            self.xhair_choice.SetSelection(self.xhairs.index(cur_xhair))
            self.toggle_controls(True)

        def addText(text, color):
            self.text.SetDefaultStyle(wx.TextAttr(color))
            self.text.AppendText(text)

        self.text.SetValue("")

        # if only 1 weapon script selected
        if len(selected) == 1:
            xhair = self.entries[selected[0]]["xhair"] # gets the current crosshair's PNG filepath (assets folder)
            xhair_display_path = get_xhair_display_path(xhair)
            
            # if crosshair for selected weapon script doesn't have a pre-existing PNG in the assets folder
            if xhair_display_path is None:
                self.set_image("") # display a blank image
            else:
                self.set_image(xhair_display_path)
        # if more than 1 weapon script selected
        else:
            self.set_image("")

        if len(selected) > 1:
            addText("<multiple>\n", wx.BLACK)

        addText("Class{}: ".format("es" if len(display["classes"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["classes"])), wx.BLACK)

        addText("Weapon Class{}: ".format("es" if len(display["weapons"]) > 1 else ""), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["weapons"])), wx.BLACK)

        addText("Categor{}: ".format("ies" if len(display["categories"]) > 1 else "y"), wx.BLUE)
        addText("{}\n\n".format(", ".join(display["categories"])), wx.BLACK)

        addText("Slot: ", wx.BLUE)

        if len(selected) > 1:
            addText("<multiple>\n\n", wx.BLACK)
        else:
            addText("{}\n\n".format({1: "Primary", 2: "Secondary", 3: "Melee", 4: "PDA"}[weapon_associations[self.cur_entries[0]["name"]]["slot"]]), wx.BLACK)

        addText("Affected Weapons:\n", wx.BLUE)
        addText("\n".join(display["affected"]), wx.BLACK)

        if len(self.cur_entries) > 0:
            def entries_homogeneous(field):
                fil = filter(lambda x: weapon_associations[x["name"]][field] == weapon_associations[self.cur_entries[0]["name"]][field], self.cur_entries)
                return len(list(fil)) == len(self.cur_entries)

            if entries_homogeneous("class"):
                self.btn_apply_class.Enable()
            else:
                self.btn_apply_class.Disable()

            if entries_homogeneous("slot"):
                self.btn_apply_slot.Enable()
            else:
                self.btn_apply_slot.Disable()

            self.last_selection = selected[0]

        self.text.ScrollPages(-100) # hacky way to scroll to the top of the text control

    # column header on click
    def col_click(self, event):
        col = event.GetColumn()
        cur = self.weapon_list_sort[col]
        self.weapon_list_sort[col] = 1 if cur == 0 else cur * -1
        self.weapon_list_sort[1 if col == 0 else 0] = 0

        self.populate_list()



    def __init__(self, parent, title, size):
        super(CrosshairFrame, self).__init__(parent, title=title, size=size, style=wx.DEFAULT_FRAME_STYLE)
        
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetIcon(wx.Icon(resource_path("xhair.ico")))

        self.entries = prepare_entries()
        self.cur_entries = []
        self.cur_xhair = ""
        self.xhairs = get_crosshairs()
        self.SetMinSize(cn["ui"]["window_size_min"])

        # Main panel
        self.main_panel = wx.Panel(self)

        self.setup_menu_bar()
        self.setup_panels()
        self.init_log()

        self.Centre()
        self.Show(True)

        self.toggle_controls(False)
