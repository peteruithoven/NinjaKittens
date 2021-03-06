from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser

from NK.util import profile
from NK.gui import configBase
from NK.gui import alterationPanel
from NK.gui import sceneView
from NK.gui import preferencesDialog
from NK.gui.util import dropTarget

class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='NinjaKittens')

		wx.EVT_CLOSE(self, self.OnClose)

		# allow dropping any file, restrict later
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles))

		self.normalModeOnlyItems = []

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(appName="NinjaKittens",
						localFilename=mruFile,
						style=wx.CONFIG_USE_LOCAL_FILE)

		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, _("Load model file...\tCTRL+L"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		i = self.fileMenu.Append(-1, _("Save model...\tCTRL+S"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveModel(), i)
		i = self.fileMenu.Append(-1, _("Clear platform"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.OnDeleteAll(e), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Print...\tCTRL+P"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showPrintWindow(), i)
		i = self.fileMenu.Append(-1, _("Save GCode..."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveGCode(), i)
		i = self.fileMenu.Append(-1, _("Save Trotec laser file (*.tsf)..."))
		self.Bind(wx.EVT_MENU, self.OnTrotecLaser, i)
		i = self.fileMenu.Append(-1, _("Show slice engine log..."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene._showSliceLog(), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Open Profile..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = self.fileMenu.Append(-1, _("Save Profile..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = self.fileMenu.Append(-1, _("Load Profile from GCode..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Reset Profile to default"))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Preferences...\tCTRL+,"))
		self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		i = self.fileMenu.Append(-1, _("Machine settings..."))
		self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)
		self.fileMenu.AppendSeparator()

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), '&' + _("Recent Model Files"), modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		# Profle MRU list
		profileHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), _("Recent Profile Files"), profileHistoryMenu)
		self.profileFileHistory.UseMenu(profileHistoryMenu)
		self.profileFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnProfileMRU, id=self.ID_MRU_PROFILE1, id2=self.ID_MRU_PROFILE10)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, _("Quit"))
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, '&' + _("File"))

		toolsMenu = wx.Menu()

		i = toolsMenu.Append(-1, _("Copy profile to clipboard"))
		self.Bind(wx.EVT_MENU, self.onCopyProfileClipboard,i)
		self.menubar.Append(toolsMenu, _("Tools"))

		#Machine menu for machine configuration/tooling
		self.machineMenu = wx.Menu()
		self.updateMachineMenu()
		self.menubar.Append(self.machineMenu, _("Machine"))

		#Preset menu for quickly switching pre-made profiles
		self.presetMenu = wx.Menu()
		self.updatePresetMenu()
		self.menubar.Append(self.presetMenu, _("Presets"))

		expertMenu = wx.Menu()

		i = expertMenu.Append(-1, _("Open expert settings...\tCTRL+E"))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)

		self.menubar.Append(expertMenu, _("Expert"))

		helpMenu = wx.Menu()
		i = helpMenu.Append(-1, _("Online documentation..."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/NinjaKittens'), i)
		i = helpMenu.Append(-1, _("Report a problem..."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/NinjaKittens/issues'), i)
		i = helpMenu.Append(-1, _("About NinjaKittens..."))
		self.Bind(wx.EVT_MENU, self.OnAbout, i)
		self.menubar.Append(helpMenu, _("Help"))
		self.SetMenuBar(self.menubar)

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.leftPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.rightPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())

		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.leftPane.SetSizer(self.leftSizer)

		#Preview window
		self.scene = sceneView.SceneView(self.rightPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.rightPane.SetSizer(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		self.updateProfileToAllControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()

		#Timer set; used to check if profile is on the clipboard
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer)
		self.timer.Start(1000)
		self.lastTriedClipboard = profile.getProfileString()

		# Restore the window position, size & state from the preferences file
		try:
			if profile.getPreference('window_maximized') == 'True':
				self.Maximize(True)
			else:
				posx = int(profile.getPreference('window_pos_x'))
				posy = int(profile.getPreference('window_pos_y'))
				width = int(profile.getPreference('window_width'))
				height = int(profile.getPreference('window_height'))
				if posx > 0 or posy > 0:
					self.SetPosition((posx,posy))
				if width > 0 and height > 0:
					self.SetSize((width,height))

			self.normalSashPos = int(profile.getPreference('window_normal_sash'))
		except:
			self.normalSashPos = 0
			self.Maximize(True)
		if self.normalSashPos < self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5:
			self.normalSashPos = self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5

		self.splitter.SplitVertically(self.leftPane, self.rightPane, self.normalSashPos)

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800,600))
			self.Centre()

		self.scene.SetFocus()

	def onTimer(self, e):
		#Check if there is something in the clipboard
		profileString = ""
		try:
			if not wx.TheClipboard.IsOpened():
				if not wx.TheClipboard.Open():
					return
				do = wx.TextDataObject()
				if wx.TheClipboard.GetData(do):
					profileString = do.GetText()
				wx.TheClipboard.Close()

				startTag = "NINJA_PROFILE_STRING:"
				if startTag in profileString:
					#print "Found correct syntax on clipboard"
					profileString = profileString.replace("\n","").strip()
					profileString = profileString[profileString.find(startTag)+len(startTag):]
					if profileString != self.lastTriedClipboard:
						print profileString
						self.lastTriedClipboard = profileString
						profile.setProfileFromString(profileString)
						self.scene.notification.message("Loaded new profile from clipboard.")
						self.updateProfileToAllControls()
		except:
			print "Unable to read from clipboard"

	def OnPreferences(self, e):
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()
		wx.CallAfter(prefDialog.Show)

	def OnMachineSettings(self, e):
		prefDialog = preferencesDialog.machineSettingsDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()

	def OnDropFiles(self, files):
		if len(files) > 0:
			profile.setPluginConfig([])
			self.updateProfileToAllControls()
		self.scene.loadFiles(files)

	def OnModelMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_MODEL1
		path = self.modelFileHistory.GetHistoryFile(fileNum)
		# Update Model MRU
		self.modelFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
		# Load Model
		profile.putPreference('lastFile', path)
		filelist = [ path ]
		self.scene.loadFiles(filelist)

	def addToModelMRU(self, file):
		self.modelFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()

	def OnProfileMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_PROFILE1
		path = self.profileFileHistory.GetHistoryFile(fileNum)
		# Update Profile MRU
		self.profileFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()
		# Load Profile
		profile.loadProfile(path)
		self.updateProfileToAllControls()

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()

	def updateProfileToAllControls(self):
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()

	def updateMachineMenu(self):
		#Remove all items so we can rebuild the menu. Inserting items seems to cause crashes, so this is the safest way.
		for item in self.machineMenu.GetMenuItems():
			self.machineMenu.RemoveItem(item)

		#Add a menu item for each machine configuration.
		for n in xrange(0, profile.getMachineCount()):
			i = self.machineMenu.Append(n + 0x1000, profile.getMachineSetting('machine_name', n).title(), kind=wx.ITEM_RADIO)
			if n == int(profile.getPreferenceFloat('active_machine')):
				i.Check(True)
			self.Bind(wx.EVT_MENU, lambda e: self.OnSelectMachine(e.GetId() - 0x1000), i)

		self.machineMenu.AppendSeparator()

		i = self.machineMenu.Append(-1, _("Machine settings..."))
		self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)

	def updatePresetMenu(self):
		#Remove all items so we can rebuild the menu. Inserting items seems to cause crashes, so this is the safest way.
		for item in self.presetMenu.GetMenuItems():
			self.presetMenu.RemoveItem(item)

		for n in xrange(profile.getPresetCount()):
			i = self.presetMenu.Append(n + 0x2000, profile.getPreset(n)[0])
			self.Bind(wx.EVT_MENU, lambda e: self.OnSelectPreset(e.GetId() - 0x2000), i)

		self.presetMenu.AppendSeparator()

		i = self.presetMenu.Append(-1, _("Save current settings as preset..."))
		self.Bind(wx.EVT_MENU, self.OnPresetSave, i)

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to load"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadProfile(profileFile)
			self.updateProfileToAllControls()

			# Update the Profile MRU
			self.addToProfileMRU(profileFile)
		dlg.Destroy()

	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, _("Select gcode file to load profile from"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*.gcode)|*.gcode;*.g")
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.setProfileFromString(line[line.find(':')+1:].strip())
					hasProfile = True
			if hasProfile:
				self.updateProfileToAllControls()
			else:
				wx.MessageBox(_("No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer."), _("Profile load error"), wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to save"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.saveProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, _("This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?"), _("Profile reset"), wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetProfile()
			self.updateProfileToAllControls()

	def OnSelectMachine(self, index):
		profile.setActiveMachine(index)
		self.reloadSettingPanels()

	def OnSelectPreset(self, index):
		profile.setProfileFromString(profile.getPreset(index)[1])
		self.updateProfileToAllControls()

	def OnPresetSave(self, e):
		dlg = wx.TextEntryDialog(self, _("Name for this preset?"), _("Preset name"), _(""))
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		name = dlg.GetValue()
		dlg.Destroy()
		if name == '':
			return
		profile.savePreset(name)
		self.updatePresetMenu()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow(lambda : self.scene.sceneUpdated())
		ecw.Centre()
		ecw.Show()

	def onCopyProfileClipboard(self, e):
		try:
			if not wx.TheClipboard.IsOpened():
				wx.TheClipboard.Open()
				clipData = wx.TextDataObject()
				self.lastTriedClipboard = profile.getProfileString()
				profileString = profile.insertNewlines("NINJA_PROFILE_STRING:" + self.lastTriedClipboard)
				clipData.SetText(profileString)
				wx.TheClipboard.SetData(clipData)
				wx.TheClipboard.Close()
		except:
			print "Could not write to clipboard, unable to get ownership. Another program is using the clipboard."

	def OnAbout(self, e):
		aboutBox = aboutWindow.aboutWindow()
		aboutBox.Centre()
		aboutBox.Show()

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath())

		# Save the window position, size & state from the preferences file
		profile.putPreference('window_maximized', self.IsMaximized())
		if not self.IsMaximized() and not self.IsIconized():
			(posx, posy) = self.GetPosition()
			profile.putPreference('window_pos_x', posx)
			profile.putPreference('window_pos_y', posy)
			(width, height) = self.GetSize()
			profile.putPreference('window_width', width)
			profile.putPreference('window_height', height)

			# Save normal sash position.  If in normal mode (!simple mode), get last position of sash before saving it...
			profile.putPreference('window_normal_sash', self.normalSashPos)

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which can keep wxWidgets from quiting.
		print "Closing down"
		self.scene.OnPaint = lambda e : e
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

	def OnTrotecLaser(self, e):
		import numpy
		if len(self.scene._scene.engine.resultPoints) < 1:
			return
		dlg=wx.FileDialog(self, "Save Trotec laser file", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard("Trotec (*.tsf)|*.tsf")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()
		cutPolygons = []
		engravePolygons = []
		cutZ = -profile.getProfileSettingFloat('cut_depth')
		engraveZ = -profile.getProfileSettingFloat('engrave_depth')
		curPath = None
		for p in self.scene._scene.engine.resultPoints:
			if abs(p[2] - cutZ) < 0.01:
				if curPath is None:
					curPath = [p]
					cutPolygons.append(curPath)
				else:
					curPath.append(p)
			elif abs(p[2] - engraveZ) < 0.01:
				if curPath is None:
					curPath = [p]
					engravePolygons.append(curPath)
				else:
					curPath.append(p)
			else:
				curPath = None
		minX = 1000000
		maxX =-1000000
		minY = 1000000
		maxY =-1000000
		for poly in cutPolygons:
			for p in poly:
				if p[0] < minX:
					minX = p[0]
				if p[1] < minY:
					minY = p[1]
				if p[0] > maxX:
					maxX = p[0]
				if p[1] > maxY:
					maxY = p[1]
		for poly in engravePolygons:
			for p in poly:
				if p[0] < minX:
					minX = p[0]
				if p[1] < minY:
					minY = p[1]
				if p[0] > maxX:
					maxX = p[0]
				if p[1] > maxY:
					maxY = p[1]

		dpi = 500.0
		f = open(filename, "wb")
		f.write('<!-- Version: 9.4.2.1034>\r\n')
		f.write('<!-- PrintingApplication: ps2tsf.exe>\r\n')
		f.write('<BegGroup: Header>\r\n')
		f.write('<ProcessMode: Standard>\r\n')
		f.write('<Size: %.2f;%.2f>\r\n' % (maxX - minX+1.0, maxY - minY+1.0))
		f.write('<MaterialGroup: Rubber>\r\n')
		f.write('<MaterialName: 2.3 mm>\r\n')
		name = os.path.basename(filename)
		name = os.path.splitext(name)[0]
		f.write('<JobName: %s.eps>\r\n' % (name))
		f.write('<JobNumber: 1>\r\n')
		f.write('<Resolution: %i>\r\n' % (dpi))
		f.write('<Cutline: none>\r\n')
		f.write('<EndGroup: Header>\r\n')
		f.write('<BegGroup: Bitmap>\r\n')
		bmpMagic = """eJztyTEKwkAURdFvJzbBHVimTG3CIAMpg4UuwiaQFWTlwjgDVu5AOOdxqzc9nnndrpdhHFJe9tc5
mlTra3sX8T5GHOqa2/f/VUppAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAPCHpvme1y2dPr1q6Hs="""
		import base64
		import zlib
		f.write(zlib.decompress(base64.decodestring(bmpMagic)))
		f.write('<EndGroup: Bitmap>\r\n')
		f.write('<BegGroup: DrawCommands>\r\n')

		for poly in engravePolygons:
			f.write('<DrawPolygon: %i;0;0;255' % (len(poly)))
			for p in poly:
				f.write(';%i;%i' % (p[0]/25.4*dpi, p[1]/25.4*dpi))
			f.write('>\r\n')
		for poly in cutPolygons:
			f.write('<DrawPolygon: %i;255;0;0' % (len(poly)))
			for p in poly:
				f.write(';%i;%i' % (p[0]/25.4*dpi, p[1]/25.4*dpi))
			f.write('>\r\n')
		f.write('<EndGroup: DrawCommands>\r\n')
		f.close()

class normalSettingsPanel(configBase.configPanelBase):
	"Main user interface window"
	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)

		#Main tabs
		self.nb = wx.Notebook(self)
		self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.GetSizer().Add(self.nb, 1, wx.EXPAND)

		self.printPanel = self.CreateConfigTab(self.nb, 'Basic')
		self._addSettingsToPanel('basic', self.printPanel)

		self.advancedPanel = self.CreateConfigTab(self.nb, 'Advanced')
		self._addSettingsToPanel('advanced', self.advancedPanel)

		#Alteration page
		self.alterationPanel = alterationPanel.alterationPanel(self.nb, callback)
		self.nb.AddPage(self.alterationPanel, "Start/End-GCode")

		self.Bind(wx.EVT_SIZE, self.OnSize)

		self.nb.SetSize(self.GetSize())

	def _addSettingsToPanel(self, category, panel):
		for title in profile.getSubCategoriesFor(category):
			configBase.TitleRow(panel, _(title))
			for s in profile.getSettingsForCategory(category, title):
				configBase.SettingRow(panel, s.getName())

	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, _(title))
			for s in profile.getSettingsForCategory(category, title):
				configBase.SettingRow(p, s.getName())

	def SizeLabelWidths(self, left, right):
		leftWidth = self.getLabelColumnWidth(left)
		rightWidth = self.getLabelColumnWidth(right)
		maxWidth = max(leftWidth, rightWidth)
		self.setLabelColumnWidth(left, maxWidth)
		self.setLabelColumnWidth(right, maxWidth)

	def OnSize(self, e):
		# Make the size of the Notebook control the same size as this control
		self.nb.SetSize(self.GetSize())

		# Propegate the OnSize() event (just in case)
		e.Skip()

	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		if self.alterationPanel is not None:
			self.alterationPanel.updateProfileToControls()
