#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Title  : WineLocale
Version: 0.7.0
Author : Derrick Sobodash <derrick@cinnamonpirate.com>
Web    : http://code.google.com/p/winelocale/
License: BSD License

Copyright (c) 2007-2009, Derrick Sobodash
All rights reserved

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of Derrick Sobodash nor the names of his contributors
  may be used to endorse or promote products derived from this software
  without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
'''

import sys
import os
import subprocess
import pango
import configparser
import gi

from pathlib import Path
from struct import pack, unpack
from gnome import url_show         # handle URL clicks in GUI

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

'''
-------------------------------------------------------------------------------
Program information
-------------------------------------------------------------------------------
'''
PROGRAM = "WineLocale"
AUTHOR = "Derrick Sobodash"
COPY = "Copyright © 2007-2009 " + AUTHOR
VERSION = "0.7.0"
LICENSE = "BSD"
DESCRIP = "WineLocale clones the functionality of Microsoft AppLocale in " + \
          "Wine. It is used to manage global locale settings and font " + \
          "settings in the Wine registry to ensure proper display of " + \
          "non-Latin type in pre-Unicode portable executables."
WEBSITE = "http://code.google.com/p/winelocale/"
CONFIG = Path(os.environ["HOME"]) / ".winelocalerc"
I18N = "i18n"
ICON = "winelocale.svg"
TEMP = Path("/tmp/")
LICENSE = "LICENSE"
APP_ID = "com.google.code.winelocale"

'''
-------------------------------------------------------------------------------
Pull in the translation that matches our locale
-------------------------------------------------------------------------------
'''
# Pull in strings
if(os.environ["LANG"][0:5] != "en_US"):
    try:
        file = open(I18N + "/" + os.environ["LANG"][0:5] + ".lang")
    except IOError:
        print("Unable to find a language file for " + os.environ["LANG"][0:5] +
              ", using en_US")
        I18N_FILE = I18N + "/en_US.lang"
    else:
        I18N_FILE = I18N + "/" + os.environ["LANG"][0:5] + ".lang"
else:
    I18N_FILE = I18N + "/en_US.lang"
STRINGSFP = open(I18N_FILE, 'r')
STRINGS = configparser.ConfigParser()
STRINGS.readfp(STRINGSFP)
STRINGSFP.close()

'''
-------------------------------------------------------------------------------
Pango gotchas
-------------------------------------------------------------------------------
'''
PANGO_SCALE = 1024   # Why isn't this set in Python's pango module?
WINE_MENUBAR = 0      # Need to hack this to match

# 96dpi table (default)
# Pango sizes do not match up to the sizes at which Wine draws
# the menubar. We need to hack the Pango size to the Wine font
# size and make the menubar match up.
# Hope a beta tester can help if someone needs another dpi!
# And no, this has NOTHING to do with the Wine dpi setting.

GTKTABLE_96 = {
    6: (9, 15),
    7: (10, 17),
    8: (11, 18),
    9: (13, 20),
    10: (14, 22),
    11: (15, 23),
    12: (16, 24),
    13: (18, 27),
    14: (20, 28),
    16: (22, 31)
}

'''
-------------------------------------------------------------------------------
LOGFONT-related constants

Microsoft defines all these, and so should we.
-------------------------------------------------------------------------------
'''
# Font weights
FW_DONTCARE = 0
FW_THIN = 100
FW_EXTRALIGHT = 200
FW_LIGHT = 300
FW_NORMAL = 400
FW_MEDIUM = 500
FW_SEMIBOLD = 600
FW_BOLD = 700
FW_EXTRABOLD = 800
FW_HEAVY = 900

# Locale character sets
ANSI_CHARSET = 0
DEFAULT_CHARSET = 1
SYMBOL_CHARSET = 2
SHIFTJIS_CHARSET = 128
HANGUL_CHARSET = 129
JOHAB_CHARSET = 130
GB2312_CHARSET = 134
CHINESEBIG5_CHARSET = 136
GREEK_CHARSET = 161
TURKISH_CHARSET = 162
VIETNAMESE_CHARSET = 163
BALTIC_CHARSET = 186
RUSSIAN_CHARSET = 204
EASTEUROPE_CHARSET = 238
OEM_CHARSET = 255

# Display precision (usually 0)
OUT_DEFAULT_PRECIS = 0
OUT_STRING_PRECIS = 1
OUT_CHARACTER_PRECIS = 2
OUT_STROKE_PRECIS = 3
OUT_TT_PRECIS = 4
OUT_DEVICE_PRECIS = 5
OUT_RASTER_PRECIS = 6
OUT_TT_ONLY_PRECIS = 7
OUT_OUTLINE_PRECIS = 8
OUT_PS_ONLY_PRECIS = 10

# Clipping precision (usually 0)
CLIP_DEFAULT_PRECIS = 0
CLIP_CHARACTER_PRECIS = 1
CLIP_STROKE_PRECIS = 2
CLIP_LH_ANGLES = 1 << 4
CLIP_TT_ALWAYS = 2 << 4
CLIP_DFA_DISABLE = 4 << 4
CLIP_EMBEDDED = 8 << 4

# Font smoothing
DEFAULT_QUALITY = 0
DRAFT_QUALITY = 1
PROOF_QUALITY = 2
NONANTIALIASED_QUALITY = 3
ANTIALIASED_QUALITY = 4
CLEARTYPE_QUALITY = 5

# Font spacing
DEFAULT_PITCH = 0
FIXED_PITCH = 1
VARIABLE_PITCH = 2

# Font style
FF_DONTCARE = 0 << 4
FF_ROMAN = 1 << 4
FF_SWISS = 2 << 4
FF_MODERN = 3 << 4
FF_SCRIPT = 4 << 4
FF_DECORATIVE = 5 << 4

'''
-------------------------------------------------------------------------------
Registry patches

Since we are no longer depending on outside files, we store all basic patches
in this file. The program will collect related patches, write a file to /tmp,
and apply it with Wine's regedit.
-------------------------------------------------------------------------------
'''
REGEDIT = "REGEDIT4\n\n"

REG_SET120DPI = "[HKEY_CURRENT_CONFIG\\Software\\Fonts]\n" + \
                "\"LogPixels\"=dword:00000078\n\n"

REG_SET96DPI = "[HKEY_CURRENT_CONFIG\\Software\\Fonts]\n" + \
                "\"LogPixels\"=dword:00000060\n\n"

REG_SMOOTHING = "[HKEY_CURRENT_USER\\Control Panel\\Desktop]\n" + \
                "\"FontSmoothing\"=\"2\"\n" + \
                "\"FontSmoothingGamma\"=dword:00000578\n" + \
                "\"FontSmoothingOrientation\"=dword:00000001\n" + \
                "\"FontSmoothingType\"=dword:00000002\n\n"

REG_FONTLINK = "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\" \
    "CurrentVersion\\FontLink\\SystemLink]\n" + \
    "\"Bitstream Vera Sans\"=hex(7):6b,6f,63,68,69,2d,67,6f,74,68,69,63,2d," \
    "73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69,20,47,6f,74,68,69,63,00," \
    "75,6d,69,6e,67,2e,74,74,63,2c,41,52,20,50,4c,20,55,4d,69,6e,67,00,55," \
    "6e,44,6f,74,75,6d,2e,74,74,66,2c,55,6e,44,6f,74,75,6d,00,00\n" + \
    "\"Bitstream Vera Serif\"=hex(7):6b,6f,63,68,69,2d,6d,69,6e,63,68,6f," \
    "2d,73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69,20,4d,69,6e,63,68,6f," \
    "00,75,6b,61,69,2e,74,74,63,2c,41,52,20,50,4c,20,55,4b,61,69,00,55,6e," \
    "42,61,74,61,6e,67,2e,74,74,66,2c,55,6e,42,61,74,61,6e,67,00,00\n" + \
    "\"Lucida Sans Unicode\"=hex(7):6b,6f,63,68,69,2d,67,6f,74,68,69,63,2d," \
    "73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69,20,47,6f,74,68,69,63,00," \
    "00\n" + \
    "\"Microsoft Sans Serif\"=hex(7):56,65,72,61,53,65,2e,74,74,66,2c,42,69," \
    "74,73,74,72,65,61,6d,20,56,65,72,61,20,53,61,6e,73,00,6b,6f,63,68,69," \
    "2d,67,6f,74,68,69,63,2d,73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69," \
    "20,47,6f,74,68,69,63,00,75,6d,69,6e,67,2e,74,74,63,2c,41,52,20,50,4c," \
    "20,55,4d,69,6e,67,00,55,6e,44,6f,74,75,6d,2e,74,74,66,2c,55,6e,44,6f," \
    "74,75,6d,00,00\n" + \
    "\"MS PGothic\"=hex(7):56,65,72,61,53,65,2e,74,74,66,2c,42,69,74,73,74," \
    "72,65,61,6d,20,56,65,72,61,20,53,61,6e,73,00,00\n" + \
    "\"MS UI Gothic\"=hex(7):56,65,72,61,53,65,2e,74,74,66,2c,42,69,74,73," \
    "74,72,65,61,6d,20,56,65,72,61,20,53,61,6e,73,00,6b,6f,63,68,69,2d,67," \
    "6f,74,68,69,63,2d,73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69,20,47," \
    "6f,74,68,69,63,00,00\n" + \
    "\"Tahoma\"=hex(7):56,65,72,61,53,65,2e,74,74,66,2c,42,69,74,73,74,72," \
    "65,61,6d,20,56,65,72,61,20,53,61,6e,73,00,6b,6f,63,68,69,2d,67,6f,74," \
    "68,69,63,2d,73,75,62,73,74,2e,74,74,66,2c,4b,6f,63,68,69,20,47,6f,74," \
    "68,69,63,00,75,6d,69,6e,67,2e,74,74,63,2c,41,52,20,50,4c,20,55,4d,69," \
    "6e,67,00,55,6e,44,6f,74,75,6d,2e,74,74,66,2c,55,6e,44,6f,74,75,6d,00," \
    "00\n\n"

REG_FONTSUBS = "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\" \
    "CurrentVersion\\FontSubstitutes]\n" + \
    "\"Arial\"=\"Bitstream Vera Sans\"\n" + \
    "\"Batang\"=\"UnBatang\"\n" + \
    "\"BatangChe\"=\"UnBatang\"\n" + \
    "\"Dotum\"=\"UnDotum\"\n" + \
    "\"DotumChe\"=\"UnDotum\"\n" + \
    "\"Gulim\"=\"UnDotum\"\n" + \
    "\"GulimChe\"=\"UnDotum\"\n" + \
    "\"Helvetica\"=\"Bitstream Vera Sans\"\n" + \
    "\"MingLiU\"=\"AR PL UMing TW\"\n" + \
    "\"MS Gothic\"=\"Kochi Gothic\"\n" + \
    "\"MS Mincho\"=\"Kochi Mincho\"\n" + \
    "\"MS PGothic\"=\"Kochi Gothic\"\n" + \
    "\"MS PMincho\"=\"Kochi Mincho\"\n" + \
    "\"MS Shell Dlg 2\"=\"Bitstream Vera Sans\"\n" + \
    "\"MS UI Gothic\"=\"Bitstream Vera Sans\"\n" + \
    "\"PMingLiU\"=\"AR PL UMing TW\"\n" + \
    "\"SimSun\"=\"AR PL UMing CN\"\n" + \
    "\"Songti\"=\"AR PL UMing CN\"\n" + \
    "\"Tahoma\"=\"Bitstream Vera Sans\"\n" + \
    "\"Times\"=\"Bitstream Vera Serif\"\n" + \
    "\"Tms Rmn\"=\"Bitstream Vera Serif\"\n\n"

REG_PATCHDLG = {
    "ANSI":        "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\"
    "CurrentVersion\\FontSubstitutes]\n" +
    "\"MS Shell Dlg\"=\"Bitstream Vera Sans\"\n\n",
    "SHIFTJIS":    "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\"
    "CurrentVersion\\FontSubstitutes]\n" +
    "\"MS Shell Dlg\"=\"Kochi Gothic\"\n\n",
    "HANGUL":      "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\"
    "CurrentVersion\\FontSubstitutes]\n" +
    "\"MS Shell Dlg\"=\"UnDotum\"\n\n",
    "GB2312":      "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\"
    "CurrentVersion\\FontSubstitutes]\n" +
    "\"MS Shell Dlg\"=\"AR PL UMing CN\"\n\n",
    "CHINESEBIG5": "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\"
    "CurrentVersion\\FontSubstitutes]\n" +
    "\"MS Shell Dlg\"=\"AR PL UMing TW\"\n\n"
}

REG_MENUH = "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics]\n" \
    "\"MenuHeight\"="

REG_MENUW = "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\WindowMetrics]\n" \
    "\"MenuWidth\"="

REG_METRICS = {
    "CaptionFont": "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\"
    "WindowMetrics]\n\"CaptionFont\"=",
    "MenuFont": "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\"
    "WindowMetrics]\n\"MenuFont\"=",
    "MessageFont": "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\"
    "WindowMetrics]\n\"MessageFont\"=",
    "SmCaptionFont": "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\"
    "WindowMetrics]\n\"SmCaptionFont\"=",
    "StatusFont": "[HKEY_CURRENT_USER\\Control Panel\\Desktop\\"
    "WindowMetrics]\n\"StatusFont\"="
}

'''
-------------------------------------------------------------------------------
Initialize global variables
-------------------------------------------------------------------------------
'''
HAVE_FONTS = {
  "AR PL UMing CN": False,
  "AR PL UMing TW": False,
  "Kochi Gothic": False,
  "Kochi Mincho": False,
  "UnBatang": False,
  "UnDotum": False
  }

DEFAULT_LOCALE = "en_US"
DEFAULT_EXE = None
USE_SMOOTHING = False
USE_HIDPIFONT = False
USE_SHORTCUT = False

LOGFONT = {
  "lfHeight":         10,
  "lfWidth":          0,
  "lfEscapement":     0,
  "lfOrientation":    0,
  "lfWeight":         400,
  "lfItalic":         0,
  "lfUnderline":      0,
  "lfStrikeOut":      0,
  "lfCharSet":        DEFAULT_CHARSET,
  "lfOutPrecision":   0,
  "lfClipPrecision":  0,
  "lfQuality":        0,
  "lfPitchAndFamily": VARIABLE_PITCH ^ FF_SWISS,
  "lfFaceName":       "Bitstream Vera Sans"
  }

'''
-------------------------------------------------------------------------------
List of locales

This list is used to populate the drop-down menu and to know which UTF-8
setting to apply to the environment.

Greek/Hebrew/Arabic are currently borked.
-------------------------------------------------------------------------------
'''
LOCALES = {
  # "ar_AR": ("العربية", "ar_SA.UTF-8"),
  # "el_GR": ("Ελληνικά", "el_GR.UTF-8"),
  "en_US": ("English", "en_US.UTF-8"),
  # "he_IL": ("עברית", "he_IL.UTF-8"),
  "ja_JP": ("日本语", "ja_JP.UTF-8"),
  "ko_KR": ("한국어", "ko_KR.UTF-8"),
  "ru_RU": ("Русский", "ru_RU.UTF-8"),
  "zh_CN": ("中文(简体)", "zh_CN.UTF-8"),
  "zh_TW": ("中文(繁體)", "zh_TW.UTF-8"),
  }

LOCALES_LIST = None


class WineLocaleWindow(Gtk.Window):
    "Contains the GUI and all necessary function hooks."
    def __init__(self):
        super().__init__(title=PROGRAM)

        self.set_size_request(400, -1)
        self.set_default_icon_from_file(ICON)

        # Container element
        self.box = Gtk.Box(Gtk.Orientation.VERTICAL, spacing=8)
        self.add(self.box)

        # Row 1
        row1 = Gtk.Box(Gtk.Orientation.VERTICAL)
        lblinstruct1 = Gtk.Label(STRINGS.get("gui", "lblinstruct1"))
        lblinstruct1.set_alignment(0, 0)
        row1.pack_start(lblinstruct1, False, False)
        row1opts = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5)
        self.txtfile = Gtk.Entry()
        row1opts.pack_start(self.txtfile, True, True)
        self.btnfile = Gtk.FileChooserButton("Open",
                                             Gtk.FileChooserAction.OPEN)
        self.btnfile.set_size_request(90, -1)
        self.btnfile.set_label(STRINGS.get("gui", "btnfile"))
        self.btnfile.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_OPEN,
                                                        Gtk.IconSize.MENU))
        row1opts.pack_start(self.btnfile, False, False)
        row1.pack_start(row1opts, False, False)
        self.box.pack_start(row1, False, False)

        # Row 2
        row2 = Gtk.Box(Gtk.Orientation.VERTICAL)
        lblinstruct2 = Gtk.Label(STRINGS.get("gui", "lblinstruct2"))
        lblinstruct2.set_alignment(0, 0)
        row2.pack_start(lblinstruct2, False, False)
        self.cmblocales = Gtk.combo_box_new_text()
        row2.pack_start(self.cmblocales, False, False)
        self.box.pack_start(row2, False, False)

        # Row 3
        row3 = Gtk.Expander(STRINGS.get("gui", "expander"))
        row3rows = Gtk.Box(Gtk.Orientation.VERTICAL)
        self.chksmoothing = Gtk.CheckButton(STRINGS.get("gui", "chksmoothing"))
        row3rows.pack_start(self.chksmoothing, False, False)
        self.chk120dpi = Gtk.CheckButton(STRINGS.get("gui", "chk120dpi"))
        row3rows.pack_start(self.chk120dpi, False, False)
        self.chkshortcut = Gtk.CheckButton(STRINGS.get("gui", "chkshortcut"))
        row3rows.pack_start(self.chkshortcut, False, False)
        row3.add(row3rows)
        self.box.pack_start(row3, True, True)
        row3.connect("activate", self.resize)

        # Row 4
        row4 = Gtk.Box(Gtk.Orientation.HORIZONTAL, spacing=5)
        self.btnhelp = Gtk.Button("Help", Gtk.STOCK_HELP)
        self.btnhelp.set_label(STRINGS.get("gui", "btnhelp"))
        self.btnhelp.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_HELP,
                                                        Gtk.IconSize.MENU))
        self.btnhelp.set_size_request(90, -1)
        row4.pack_start(self.btnhelp, False, False)
        row4.pack_start(Gtk.Label(""), True, True)
        self.btnclose = Gtk.Button("Close", Gtk.STOCK_CLOSE)
        self.btnclose.set_label(STRINGS.get("gui", "btnclose"))
        self.btnclose.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE,
                                                         Gtk.IconSize.MENU))
        self.btnclose.set_size_request(90, -1)
        row4.pack_start(self.btnclose, False, False)
        self.btnexecute = Gtk.Button("Execute", Gtk.STOCK_EXECUTE)
        self.btnexecute.set_label(STRINGS.get("gui", "btnexecute"))
        self.btnexecute.set_image(Gtk.image_new_from_stock(Gtk.STOCK_EXECUTE,
                                                           Gtk.IconSize.MENU))
        self.btnexecute.set_size_request(90, -1)
        row4.pack_start(self.btnexecute, False, False)
        self.box.pack_start(row4, False, False)

        # Check which fonts exist (globals)
        context = self.txtfile.get_pango_context()
        set_fonts(context.list_families())

        # Store our current Gtk font info to a LOGFONT
        set_logfont_from_gtk(context.get_font_description())

        # Populate the locales drop-down
        global LOCALES_LIST
        LOCALES_LIST = get_locales()
        for s in LOCALES_LIST:
            self.cmblocales.append_text(s[0])
        self.cmblocales.set_active(0)

        # Fix the expander to suit work area
        self.expanded = False
        self.flatsize = None
        self.expasize = None

        # Events
        self.btnfile.connect("clicked", self.open)
        self.btnclose.connect("clicked", self.destroy)
        self.btnhelp.connect("clicked", self.about)
        self.btnexecute.connect("clicked", self.execute)
        getBinaryLogFont(locale, logFont)

        # Update settings
        if(USE_SHORTCUT):
            self.chkshortcut.set_active(True)
        if(USE_SMOOTHING):
            self.chksmoothing.set_active(True)
        if(USE_HIDPIFONT):
            self.chk120dpi.set_active(True)
        for i in range(0, len(LOCALES_LIST)):
            if(LOCALES_LIST[i][1][0:5] == DEFAULT_LOCALE):
                self.cmblocales.set_active(i)

        if not isinstance(DEFAULT_EXE, type(None)):
            self.txtfile.set_text(DEFAULT_EXE)
            self.set_focus(self.btnexecute)

        return

    '''
    void resize()

    Fix the expander to suit our work area.
    '''
    def resize(self, widget):
        if isinstance(self.expasize, type(None)) and \
           isinstance(self.flatsize, type(None)):
            self.flatsize = self.window.get_size()
        elif isinstance(self.expasize, type(None)):
            self.expasize = self.window.get_size()
        if not self.expanded and not isinstance(self.expasize, type(None)):
            self.window.set_size_request(self.expasize[0], self.expasize[1])
            self.window.resize(self.expasize[0], self.expasize[1])
            self.expanded = True
        elif self.expanded and not isinstance(self.flatsize, type(None)):
            self.window.set_size_request(self.flatsize[0], self.flatsize[1])
            self.window.resize(self.flatsize[0], self.flatsize[1])
            self.expanded = False
        elif not self.expanded:
            self.expanded = True

    '''
    void open()

    Opens file dialog and sets self.txtfile to the selected file.
    '''
    def open(self, widget, file_name=""):
        buttons = (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL,
                   Gtk.STOCK_OPEN, Gtk.RESPONSE_OK)
        dialog = Gtk.FileChooserDialog(STRINGS.get("file", "title"), None,
                                       Gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
        # Add filters
        filter = Gtk.FileFilter()
        filter.set_name(STRINGS.get("file", "exefilter"))
        filter.add_pattern("*.exe")
        filter.add_pattern("*.EXE")
        dialog.add_filter(filter)
        filter = Gtk.FileFilter()
        filter.set_name(STRINGS.get("file", "allfilter"))
        filter.add_pattern("*")
        dialog.add_filter(filter)
        if dialog.run() == Gtk.RESPONSE_OK:
            self.txtfile.set_text(dialog.get_filename())
        dialog.destroy()

    '''
    void click_website()

    Shells open the default browser to the WineLocale page.
    '''
    def click_website(self, dialog, link, data=None):
        url_show(link)

    '''
    void about()

    Create and display Gtk About dialog.
    '''
    def about(self, widget):
        Gtk.about_dialog_set_url_hook(self.click_website)

        dialog = Gtk.AboutDialog()
        dialog.set_icon_from_file(ICON)
        dialog.set_name(PROGRAM)
        dialog.set_version(VERSION)
        dialog.set_comments(STRINGS.get("about", "comments"))
        dialog.set_copyright(COPY)
        license = open(LICENSE, "r")
        dialog.set_license(license.read())
        dialog.set_logo(Gtk.gdk.pixbuf_new_from_file(ICON))
        dialog.set_website(WEBSITE)
        dialog.run()
        dialog.destroy()

    '''
    void execute()

    Test if everything is set that needs to be for execution. commit all
    settings to the local config file.

    LOADING READY RUN!
    '''
    def execute(self, widget):
        # Should we even be doing this?
        if(self.txtfile.get_text() == ""):
            message = STRINGS.get("dialogs", "noexe1") + "\n\n" + \
                      STRINGS.get("dialogs", "noexe2")
            dialog = Gtk.MessageDialog(None, Gtk.DIALOG_MODAL,
                                       Gtk.MESSAGE_INFO, Gtk.BUTTONS_OK,
                                       message)
            dialog.set_title(STRINGS.get("dialogs", "errortitle"))
            dialog.set_icon_from_file(ICON)
            dialog.run()
            dialog.destroy()
            return(0)

        elif not os.path.exists(self.txtfile.get_text()):
            message = STRINGS.get("dialogs", "exenotfound1") + "\n\n" + \
                      STRINGS.get("dialogs", "exenotfound2")
            dialog = Gtk.MessageDialog(None, Gtk.DIALOG_MODAL,
                                       Gtk.MESSAGE_INFO, Gtk.BUTTONS_OK,
                                       message)
            dialog.set_title(STRINGS.get("dialogs", "errortitle"))
            dialog.set_icon_from_file(ICON)
            dialog.run()
            dialog.destroy()
            return(0)

        self.window.hide()

        # Update settings
        # TODO: fix globals
        global DEFAULT_LOCALE, DEFAULT_EXE, USE_SMOOTHING, USE_HIDPIFONT, USE_SHORTCUT
        if(self.chkshortcut.get_active()):
            USE_SHORTCUT = True
        else:
            USE_SHORTCUT = False
        if(self.chksmoothing.get_active()):
            USE_SMOOTHING = True
        else:
            USE_SMOOTHING = False
        if(self.chk120dpi.get_active()):
            USE_HIDPIFONT = True
        else:
            USE_HIDPIFONT = False
        DEFAULT_LOCALE = LOCALES_LIST[self.cmblocales.get_active()][1][0:5]
        DEFAULT_EXE = self.txtfile.get_text()
        createDeafultConfig()
        configFromFile = loadConfigFromFile()
        shellwine(programPath, locale, configFromFile.logFont)

        Gtk.main_quit()

    '''
    void delete()

    Hook to quit the GUI.
    '''
    def delete(self, widget, event):
        return False


def get_ja():
    "Checks if fonts needed for Japanese support are present."
    if(HAVE_FONTS["Kochi Gothic"] and HAVE_FONTS["Kochi Mincho"]):
        return(True)
    else:
        return(False)


def get_ko():
    "Checks if fonts needed for Korean support are present."
    if(HAVE_FONTS["UnBatang"] and HAVE_FONTS["UnDotum"]):
        return(True)
    else:
        return(False)


def get_cn():
    "Checks if fonts needed for Simplified Chinese support are present."
    if(HAVE_FONTS["AR PL UMing CN"]):
        return(True)
    else:
        return(False)


def get_tw():
    "Checks if fonts needed for Traditional Chinese support are present."
    if(HAVE_FONTS["AR PL UMing TW"]):
        return(True)
    else:
        return(False)


def get_locales():
    "Returns a list of all present locales."
    LOCALE_LIST = [LOCALES["en_US"], LOCALES["ru_RU"]]
    if(get_cn()):
        LOCALE_LIST.append(LOCALES["zh_CN"])
    if(get_tw()):
        LOCALE_LIST.append(LOCALES["zh_TW"])
    if(get_ko()):
        LOCALE_LIST.append(LOCALES["ko_KR"])
    if(get_ja()):
        LOCALE_LIST.append(LOCALES["ja_JP"])
    return(LOCALE_LIST)


def set_fonts(fonts):
    "Updates globals with present system fonts."
    global HAVE_FONTS
    for font in fonts:
        if font.get_name() == 'UnBatang':
            HAVE_FONTS["UnBatang"] = True
        elif font.get_name() == 'UnDotum':
            HAVE_FONTS["UnDotum"] = True
        elif font.get_name() == 'AR PL UMing TW':
            HAVE_FONTS["AR PL UMing TW"] = True
        elif font.get_name() == 'AR PL UMing CN':
            HAVE_FONTS["AR PL UMing CN"] = True
        elif font.get_name() == 'Kochi Gothic':
            HAVE_FONTS["Kochi Gothic"] = True
        elif font.get_name() == 'Kochi Mincho':
            HAVE_FONTS["Kochi Mincho"] = True


def getBinaryLogFont(locale, logFont):
    """string getBinaryLogFont()

Build a binary LOGFONT value to pump into the registry. Wine default is
184 bytes long, so let's stick with that.

typedef struct tagLOGFONT {
  LONG lfHeight;
  LONG lfWidth;
  LONG lfEscapement;     //leave it deafult
  LONG lfOrientation;    //leave it deafult
  LONG lfWeight;
  BYTE lfItalic;
  BYTE lfUnderline;      //bool False
  BYTE lfStrikeOut;      //bool False
  BYTE lfCharSet;
  BYTE lfOutPrecision;   //leave it default
  BYTE lfClipPrecision;  //leave it default
  BYTE lfQuality;        //try for ClearType?
  BYTE lfPitchAndFamily;
  TCHAR lfFaceName[LF_FACESIZE]; //32 chars max including \0
} LOGFONT, *PLOGFONT;
    """
    lfCharSet = logFont["lfCharSet"]
    if(locale == "en_US"):
        lfCharSet = ANSI_CHARSET
    elif(locale == "ru_RU"):
        lfCharSet = ANSI_CHARSET
    elif(locale == "ja_JP"):
        lfCharSet = SHIFTJIS_CHARSET
    elif(locale == "ko_KR"):
        lfCharSet = HANGUL_CHARSET
    elif(locale == "zh_CN"):
        lfCharSet = GB2312_CHARSET
    elif(locale == "zh_TW"):
        lfCharSet = CHINESEBIG5_CHARSET

    # Make sure we don't go over 32 character with the \0
    tempfont = logFont["lfFaceName"]
    tempfon2 = ""
    if(len(tempfont) > 31):
        tempfont = tempfont[0:31]
    # Translate it to shorts
    for i in range(0, len(tempfont)):
        tempfon2 += tempfont[i:i+1] + "\0"
    # Make the binary string
    newstring = pack("<lllllBBBBBBBB",
                     GTKTABLE_96[logFont["lfHeight"]][0] * -1,
                     logFont["lfWidth"],
                     logFont["lfEscapement"],
                     logFont["lfOrientation"],
                     logFont["lfWeight"],
                     logFont["lfItalic"],
                     logFont["lfUnderline"],
                     logFont["lfStrikeOut"],
                     lfCharSet,
                     logFont["lfOutPrecision"],
                     logFont["lfClipPrecision"],
                     logFont["lfQuality"],
                     logFont["lfPitchAndFamily"],
                     ) + tempfon2

    # Convert our LOGFONT to hex
    hexstring = "hex:"
    for i in range(len(newstring)):
        byte = unpack("B", newstring[i:i+1])
        hexnib = hex(byte[0])[2:]
        if len(hexnib) < 2:
            hexnib = "0" + hexnib
        hexstring += hexnib + ","
    while len(hexstring) < 277:
        hexstring += "00,"
    hexstring += "00"
    return hexstring


def set_logfont_from_gtk(pangofont):
    "Populates the global LOGFONT using data from Gtk."
    global LOGFONT, WINE_MENUBAR
    LOGFONT["lfFaceName"] = pangofont.get_family()
    if (pangofont.get_style() & pango.STYLE_ITALIC or pangofont.get_style() &
        pango.STYLE_OBLIQUE):
        LOGFONT["lfItalic"] = 1
    LOGFONT["lfWeight"] = pangofont.get_weight() + 0
    LOGFONT["lfHeight"] = pangofont.get_size() / PANGO_SCALE
    WINE_MENUBAR = GTKTABLE_96[pangofont.get_size() / PANGO_SCALE][1]
    LOGFONT["lfPitchAndFamily"] = VARIABLE_PITCH ^ FF_SWISS


class Config(object):
    pass


def loadConfigFromFile():
    "Populates globals from the config file."
    config = configparser.ConfigParser()
    with open(CONFIG, 'r') as configfp:
        config.readfp(configfp)

    configFromFile = Config()
    logFont = LOGFONT.copy()
    logFont["lfHeight"] = config.getint("settings", "gtkfontsize",
                                        LOGFONT["lfHeight"])
    logFont["lfWeight"] = config.getint("settings", "gtkfontweight",
                                        LOGFONT["lfWeight"])
    logFont["lfItalic"] = config.getboolean("settings", "gtkfontitalic",
                                            LOGFONT["lfItalic"])
    if logFont["lfHeight"] == 1:
        logFont["lfQuality"] = CLEARTYPE_QUALITY
    else:
        logFont["lfQuality"] = DEFAULT_QUALITY
    logFont["lfFaceName"] = config.get("settings", "gtkfontname",
                                       LOGFONT["lfFaceName"])
    configFromFile.logFont = logFont

    haveFonts = HAVE_FONTS.copy()
    haveFonts["AR PL UMing CN"] = \
        config.getboolean("settings", "has_umingc",
                          HAVE_FONTS["AR PL UMing CN"])
    haveFonts["AR PL UMing TW"] = \
        config.getboolean("settings", "has_umingt",
                          HAVE_FONTS["AR PL UMing TW"])
    haveFonts["Kochi Gothic"] = config.getboolean("settings", "has_kgoth",
                                                  HAVE_FONTS["Kochi Gothic"])
    haveFonts["Kochi Mincho"] = config.getboolean("settings", "has_kmin",
                                                  HAVE_FONTS["Kochi Mincho"])
    haveFonts["UnBatang"] = config.getboolean("settings", "has_batang",
                                              HAVE_FONTS["UnBatang"])
    haveFonts["UnDotum"] = config.getboolean("settings", "has_dotum",
                                             HAVE_FONTS["UnDotum"])
    configFromFile.haveFonts = haveFonts

    configFromFile.locale = config.get("settings", "locale")
    configFromFile.useSmoothing = config.getboolean("settings", "smoothing")
    configFromFile.useHiDpiFont = config.getboolean("settings", "hidpifont")
    configFromFile.useShortcut = config.getboolean("settings", "shortcut")
    return configFromFile


def createDeafultConfig():
    "Wipes the config file and populates it with default values."
    config = configparser.ConfigParser()
    config.add_section("settings")
    # Main settings
    config.set("settings", "locale", DEFAULT_LOCALE)
    config.set("settings", "gtkfontname", LOGFONT["lfFaceName"])
    config.set("settings", "gtkfontsize", str(LOGFONT["lfHeight"]))
    config.set("settings", "gtkfontweight", str(LOGFONT["lfWeight"]))
    config.set("settings", "gtkfontitalic", str(int(LOGFONT["lfItalic"])))
    config.set("settings", "shortcut", str(int(USE_SHORTCUT)))
    config.set("settings", "smoothing", str(int(USE_SMOOTHING)))
    config.set("settings", "hidpifont", str(int(USE_HIDPIFONT)))
    config.set("settings", "has_batang", str(int(HAVE_FONTS["UnBatang"])))
    config.set("settings", "has_dotum", str(int(HAVE_FONTS["UnDotum"])))
    config.set("settings", "has_umingt",
               str(int(HAVE_FONTS["AR PL UMing TW"])))
    config.set("settings", "has_umingc",
               str(int(HAVE_FONTS["AR PL UMing CN"])))
    config.set("settings", "has_kgoth", str(int(HAVE_FONTS["Kochi Gothic"])))
    config.set("settings", "has_kmin", str(int(HAVE_FONTS["Kochi Mincho"])))
    with open(CONFIG, 'w') as configfp:
        config.write(configfp)
    return


def generateRegistry(locale, logFont):
    """Create a registry patch based on all config settings in
    /tmp/winelocale.reg."""
    with open(TEMP / "winelocale.reg", "w") as registry:
        # Registry file header
        registry.write(REGEDIT)

        # WineLocale font core
        registry.write(REG_FONTLINK)
        registry.write(REG_FONTSUBS)

        # Write an appropriate Shell Dlg font for the locale
        if(locale == "en_US" or locale == "ru_RU"):
            registry.write(REG_PATCHDLG["ANSI"])
        elif(locale == "ja_JP"):
            registry.write(REG_PATCHDLG["SHIFTJIS"])
        elif(locale == "ko_KR"):
            registry.write(REG_PATCHDLG["HANGUL"])
        elif(locale == "zh_CN"):
            registry.write(REG_PATCHDLG["GB2312"])
        elif(locale == "zh_TW"):
            registry.write(REG_PATCHDLG["CHINESEBIG5"])

        # Write the window metrics fonts
        binLogFont = getBinaryLogFont(locale, logFont)
        registry.write(REG_METRICS["CaptionFont"] + binLogFont + "\n\n")
        registry.write(REG_METRICS["MenuFont"] + binLogFont + "\n\n")
        registry.write(REG_METRICS["MessageFont"] + binLogFont + "\n\n")
        registry.write(REG_METRICS["SmCaptionFont"] + binLogFont + "\n\n")
        registry.write(REG_METRICS["StatusFont"] + binLogFont + "\n\n")

        # Fix the menubar height
        registry.write(REG_MENUH + "\"" +
                       str(GTKTABLE_96[LOGFONT["lfHeight"]][1]) + "\"\n\n")
        registry.write(REG_MENUW + "\"" +
                       str(GTKTABLE_96[LOGFONT["lfHeight"]][1]) + "\"\n\n")

        # Write/remove smoothing

        # Write/remove 120dpi
        if(USE_HIDPIFONT):
            registry.write(REG_SET120DPI)
        else:
            registry.write(REG_SET96DPI)

        registry.close()
    return


def shellwine(programPath, locale, logFont):
    "Prepares the registry and shells Wine."
    initialLang = os.environ['LANG']
    env = os.environ.copy()
    env['WINEDEBUG'] = "-all"
    generateRegistry(locale, logFont)
    try:
        compProc = subprocess.run(["wine", "regedit.exe",
                                   "/tmp/winelocale.reg"], check=True, env=env)
        if compProc.returncode < 0:
            print("Child was terminated by signal", -compProc.returncode,
                  file=sys.stderr)
        else:
            print("Child returned", compProc.returncode, file=sys.stderr)
    except (OSError, subprocess.CalledProcessError) as e:
        print("Execution failed:", e, file=sys.stderr)

    winProgPath = "Z:\\" + programPath.replace("/", "\\")
    env['LANG'] = LOCALES[locale][1]
    subprocess.run(["wine", winProgPath], env=env)
    env['LANG'] = initialLang
    # why would this do anything different than the previous time?
    # or shouldn't it recover the registery?
    try:
        compProc = subprocess.run(["wine", "regedit.exe",
                                   "/tmp/winelocale.reg"], check=True, env=env)
        if compProc.returncode < 0:
            print("Child was terminated by signal", -compProc.returncode,
                  file=sys.stderr)
        else:
            print("Child returned", compProc.returncode, file=sys.stderr)
    except (OSError, subprocess.CalledProcessError) as e:
        print("Execution failed:", e, file=sys.stderr)
    return


def main():
    import argparse

    if not CONFIG.exists():
        createDeafultConfig()
    configFromFile = loadConfigFromFile()

    parser = argparse.ArgumentParser(description=DESCRIP)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument("-l", "--locale", default=configFromFile.locale,
                        help="specify a locale in which to load"
                        " the target executable (ISO 3166 standard)")
    parser.add_argument("exe", default=DEFAULT_EXE, type=Path,
                        help="target executable to run in wine with locale")
    args = parser.parse_args()

    if not isinstance(args.locale, type(None)) and args.exe.exists():
        # What was this test for? CODES.index(options.locale)) != false
        shellwine(args.exe, args.locale, configFromFile.logFont)

    else:
        win = WineLocaleWindow()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
    return


if __name__ == "__main__":
    main()
