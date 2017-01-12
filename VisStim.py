# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 11:04:42 2016

@author: Jesse Trinity (Coleman Lab)
"""
from psychopy import visual
from psychopy import monitors, logging
from psychopy import event as psyevent
from time import time
import Tkinter as tk
import tkFileDialog
import numpy as np
import csv as csv
import sys

import serial.tools.list_ports
from pyfirmata import Arduino, util, serial

class PhantomController:
    #Simulates Arduino pin functions
    #Used when no cotroller is connected
    def __init__(self):
        pass
    def get_pin(self, s):
        return PhantomPin()
    def exit(self):
        pass

class PhantomPin:
    #Pin for PhantomController class
    def __init__(self):
        pass
    def read(self):
        return 0.0
    def write(self, f):
        pass
        
#Open serial port
ports = list(serial.tools.list_ports.comports())
connected_device = None
for p in ports:
    if 'Arduino' in p[1]:
        try:
            board = Arduino(p[0])
            connected_device = p[1]
            print "Connected to Arduino"
            print connected_device
            break
        except serial.SerialException:
            print "Arduino detected but unable to connect to " + p[0]
if connected_device == None:
    for p in ports:
        if 'ttyACM' in p[0]:
            try:
                board = Arduino(p[0])
                connected_device = p[1]
                print "connected"
                break
            except serial.SerialException:
                pass
            

if connected_device is not None:
    it = util.Iterator(board)
    it.start()
    board.analog[0].enable_reporting()
elif connected_device is None:
    print "No connected Arduino - timestamp data will be text only"
    board = PhantomController()

pin_a = board.get_pin('d:3:p') # low-pass filter with 4.7uF, x resistor btwn pin and (+) of cap (- cap to gnd); OUT @ res-cap+
pin_b = board.get_pin('d:6:p')
trigger = board.get_pin('d:5:p')
pin_a.write(0.0)
pin_b.write(0.0)
trigger.write(0.0)




#-----WIDGETS-----
#Generic window framework
class Window(tk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.bind("<FocusIn>", self.parent.on_focus_in)
        
        if ('title' in kwargs):
            self.title(kwargs['title'])
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    #kill root when this window is closed
    def on_closing(self):
        self.parent.destroy()
        

#Generic *gridded* button framework
class Button(tk.Button):
    def __init__(self, container, text, command, position):
        self.button_text = tk.StringVar()
        self.button_text.set(text)
        button = tk.Button(container, textvariable = self.button_text, command = command)
        button.grid(row = position[0], column = position[1], padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)

class Entry(tk.Frame):
    def __init__(self, parent, label, position, default = ""):
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text = label)
        self.entry = tk.Entry(self)
        self.entry.insert(0, default)
        
        self.label.pack(side = "left")
        self.entry.pack(side = "right")
        
        self.grid(row = position[0], column = position[1], padx = 5, pady = 5, sticky = tk.N+tk.S+tk.E+tk.W)
    
    def get(self):
        return self.entry.get()

class StimBar(tk.Frame):
    def __init__(self, parent, label, position):
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text = label)
        
        self.option = tk.StringVar()
        self.option.set("reversal")
        self.stim_options_menu = tk.OptionMenu(self, self.option, "reversal", "drift", "gray")
        
        self.length_entry = Entry(self, "length", (0,2))
        self.length_entry.entry.insert(0, 10)
        
        
        self.label.grid(row = 0, column = 0)
        self.stim_options_menu.grid(row = 0, column = 1)
        
        self.pack(side = "left")
     
#-----Main Application-----
class MainApp(tk.Tk):
    def __init__(self, master = None, *args, **kwargs):
        tk.Tk.__init__(self, master, *args, **kwargs)
        self.title("Main Window")
        self.refresh_rate= 60
        
        #populate windows by (class, name)
        self.windows = dict()
#        for (C, n) in ((window_one, "window 1"), (window_two,"window 2")):
        for (C, n) in ():
            window = C(self, title = n)
            self.windows[C] = window
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<FocusIn>", self.on_focus_in)
        
        self.anchor_frame = tk.Frame(self)
        self.anchor_frame.pack(side = "top")
        
        self.toolbar_frame = tk.Frame(self.anchor_frame)
        self.toolbar_frame.pack(side = "top")
        
        self.options_frame = tk.Frame(self.anchor_frame)
        self.options_frame.pack(side = "top")
        
        self.phase_reversal_frame = tk.Frame(self.anchor_frame)
        self.phase_reversal_frame.pack(side = "top")
        
        self.drifting_frame = tk.Frame(self.anchor_frame)
        self.drifting_frame.pack(side = "top")
                
        #create windows by name
#        window_names = ("window1", "window2")
#        windows = {name:Window(self.root, title = name) for name in window_names}
        
        #-----begin FLAGS-----
        self.ABORT = False
        
        #-----end FLAGS-----
               
        #-----begin app widgets-----
        #labels
        self.title_frame= tk.Frame(self.toolbar_frame)
        self.title_frame.pack(side = "top")
        
        self.title_label = tk.Label(self.title_frame, text = "PsychoPy Controller")
        self.title_label.grid(row = 0, column = 0)
        
        #Buttons
        self.button_frame = tk.Frame(self.toolbar_frame)
        self.button_frame.pack(side = "top")
        
        self.load_button = Button(self.button_frame, "Load File", self.load, (1, 0))
    
        self.open_screen_button = Button(self.button_frame, "Open Screen", self.open_experiment_window, (1, 1))
        
        self.run_test_grating_button = Button(self.button_frame, "Run Test Grating", self.run_stimulus(self.run_test_grating), (1, 2))
        
        self.abort_run_button = Button(self.button_frame, "Abort Run", self.abort_run, (1, 3))
        self.abort_warning_string = tk.StringVar()
        self.abort_warning_string.set("ready")
        self.abort_warning = tk.Label(self.button_frame, textvariable = self.abort_warning_string)
        self.abort_warning.grid(row = 1, column = 4, padx = 5, pady  = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        
        #Entry Fields
        self.entry_frame = tk.Frame(self.options_frame)
        self.entry_frame.pack(side = "top")
        
        self.monitor_width_entry = Entry(self.entry_frame, "Monitor Width (cm)", (0, 0))
        self.monitor_width_entry.entry.insert(0, 37)
        
        self.monitor_distance_entry = Entry(self.entry_frame, "Monitor Distance (cm)", (1, 0))
        self.monitor_distance_entry.entry.insert(0, 20)
        
        self.horizontal_resolution_entry = Entry(self.entry_frame, "Horiz. Res (px)", (0,1))
        self.horizontal_resolution_entry.entry.insert(0, 1280)
        
        self.vertical_resolution_entry = Entry(self.entry_frame, "Vert. Res (px)", (1,1))
        self.vertical_resolution_entry.entry.insert(0, 1024)
        
        #Stim Options
        self.stim_frame = tk.Frame(self.options_frame)
        self.stim_frame.pack(side = "top")
        
        stim1 = StimBar(self.stim_frame, "block 1", (0,0))
        
        #Standard Phase Reversal
        self.phase_title_frame= tk.Frame(self.phase_reversal_frame)
        self.phase_title_frame.pack(side = "top")
        
        self.phase_options_frame = tk.Frame(self.phase_reversal_frame)
        self.phase_options_frame.pack(side = "top")
        
        self.phase_title = tk.Label(self.phase_title_frame, text = "Quick Phase Reversal")
        self.phase_title.pack(side = "top")
        
        self.phase_sessions = Entry(self.phase_options_frame, "Sessions", (0,0), default = 5)
        self.phase_orientation = Entry(self.phase_options_frame, "Orientation", (0,1), default = 0)
        self.phase_reversals = Entry(self.phase_options_frame, "Reversals", (0,2), default = 10)
        self.phase_frequency = Entry(self.phase_options_frame, "Frequency (hz)", (0,3), default = 2)
        self.phase_relaxation = Entry(self.phase_options_frame, "Inter-session length (s)", (0,4), default = 3)
        self.phase_startdelay = Entry(self.phase_options_frame, "Start Delay (s)", (0,5), default = 5)
        
        self.run_reversal_button = Button(self.phase_options_frame, "Run", self.run_stimulus(self.run_phase_reversal), (0, 6))
        
        #Standard Drifting Grating
        self.drift_title_frame = tk.Frame(self.drifting_frame)
        self.drift_title_frame.pack(side = "top")
        
        self.drift_options_frame = tk.Frame(self.drifting_frame)
        self.drift_options_frame.pack(side = "top")
        
        self.drift_title = tk.Label(self.drift_title_frame, text = "Quick Drifting Grating")
        self.drift_title.pack(side = "top")
        
        self.drift_sessions = Entry(self.drift_options_frame, "Sessions", (0,0), default = 5)
        self.drift_orientation = Entry(self.drift_options_frame, "Orientation", (0,1), default = 0)
        self.drift_duration = Entry(self.drift_options_frame, "Duration (s)", (0,2), default = 3)
        self.drift_rate_entry = Entry(self.drift_options_frame, "Drift Rate (deg)", (0,3), default = 0.01)
        self.drift_relaxation = Entry(self.drift_options_frame, "Inter-session length (s)", (0,4), default = 3)
        self.drift_startdelay = Entry(self.drift_options_frame, "Start Delay (s)", (0,5), default = 5)
        
        self.run_drift_button = Button(self.drift_options_frame, "Run", self.run_stimulus(self.run_drifting_grating), (0, 6))
        

        #-----end app widgets-----
        
        #-----begin psychopy charm-----
        self.experiment_window = 0
        self.hres = 1920
        self.vres = 1080
        self.monitor_width = 37
        self.monitor_distance = 20
        self.Wgamma = 1.793
    
        self.stim_seconds =1
        self.drift_rate = 0.01
        self.gray_level = 2*((0.5)**(1/self.Wgamma))-1
        
        self.Nframes = self.refresh_rate * self.stim_seconds
        
        self.spatial_freq=0.05
        self.number_reversals = 100
        
        self.mon = monitors.Monitor("newmon", distance = self.monitor_distance, width = self.monitor_width)
        self.mon.currentCalib['sizePix'] = [self.hres, self.vres]
        self.mon.saveMon()
        
        print "Monitor details:"
        print self.mon.currentCalib
        
        self.window = None
        self.fixation = None
        self.stim = None
        self.frame_list = list()

        sin = np.sin(np.linspace(0, 2 * np.pi, 256)).astype(np.float64)
        sin = (sin + 1)/2
        sin = sin**(1/self.Wgamma)
        sin = 2* sin -1
        self.texture = np.array([sin for i in range(256)])
        
        
        #-----end psychopy charm-----
        
        #variables
        self.file_list = list()
        self.data = list()
        
        #set root window position (needs to happen last to account for widget sizes)
        self.update()
        self.hpos =  self.winfo_screenwidth()/2 - self.winfo_width()/2
        self.vpos = 0
        self.geometry("+%d+%d" % (self.hpos, self.vpos))
        
        self.mainloop()
    
    #Dummy command function
    def default_onclick(self):
        print "widget pressed"
    
    #Opens the experiment window, closes if already open
    def open_experiment_window(self):
        if self.window is None:
            #build window and draw calibrated gray
            self.window = visual.Window(size=[self.hres,self.vres],monitor=self.mon, fullscr = False ,allowGUI = True, units="deg", screen = self.experiment_window)
            self.window.waitBlanking = False
            self.fixation = visual.GratingStim(win=self.window, size=200, pos=[0,0], sf=0, color=[self.gray_level, self.gray_level, self.gray_level])
            self.fixation.draw()
            self.window.flip()
            self.open_screen_button.button_text.set("Close Window")
        elif self.window is not None:
            self.window.close()
            self.open_screen_button.button_text.set("Open Window")
            self.window = None
    
    #Displays a test grating for predetermined interval
    #Use to check timing
    def run_test_grating(self):
        
        for i in range(2):
            self.build_stim(self.stim, 'drift', 2.0, direction = '-')
            self.build_stim(self.fixation, 'gray', 1.0)
            self.build_stim(self.stim, 'reversal', 4, frequency = 2)
            self.build_stim(self.fixation, 'gray', 1.0)
        for i in range(2):
            self.build_stim(self.stim, 'drift', 2.0, direction = '+')
            self.build_stim(self.fixation, 'gray', 1.0)
            self.build_stim(self.stim, 'reversal', 4, frequency = 2)
            self.build_stim(self.fixation, 'gray', 1.0)
            
    def run_phase_reversal(self):

        start_delay = float(self.phase_startdelay.get())
        sessions = int(self.phase_sessions.get())
        reversals = int(self.phase_reversals.get())
        frequency = float(self.phase_frequency.get())
        relaxation = float(self.phase_relaxation.get())
        orientation = float(self.phase_orientation.get())
        
        self.build_stim(self.fixation, 'gray', start_delay)
        for i in range(sessions):
            self.build_stim(self.stim, 'reversal', reversals, frequency = frequency, orientation = orientation)
            self.build_stim(self.fixation, 'gray', relaxation)
    
    def run_drifting_grating(self):
     
        start_delay = float(self.drift_startdelay.get())
        sessions = int(self.drift_sessions.get())
        relaxation = float(self.drift_relaxation.get())
        orientation = float(self.drift_orientation.get())
        drift_rate = float(self.drift_rate_entry.get())
        duration = float(self.drift_duration.get())
        
        self.build_stim(self.fixation, 'gray', start_delay)
        for i in range(sessions):
            self.build_stim(self.stim, 'drift', duration, drift_rate = drift_rate ,orientation = orientation)
            self.build_stim(self.fixation, 'gray', relaxation)

    
    #length in seconds for static image and drifting, length in number of reversals for phase reversal (2 * num stims)
    #(pin_a, pin_b, draw, setPhase, drift[phase, direction], setOri, orientation)
    def build_stim(self, stim, stim_type, length, **kwargs):
        orientation = 0
        direction = '+'
        drift_rate = self.drift_rate
        if 'orientation' in kwargs:
            orientation = kwargs['orientation']
        if 'direction' in kwargs:
            direction = kwargs['direction']
        if 'drift_rate' in kwargs:
            drift_rate = kwargs['drift_rate']
            
        if stim_type == 'gray':
            for frame in range(int(length * self.refresh_rate)):
                self.frame_list.append((0.0, 0.0,stim.draw, stim.setPhase, tuple((0.0,)), stim.setOri, orientation))
        if stim_type == 'drift':
            for frame in range(int(length * self.refresh_rate)):
                self.frame_list.append((1.0, 1.0, stim.draw, stim.setPhase, tuple((drift_rate,direction)), stim.setOri, orientation))
        if stim_type == 'reversal':
            for reversal in range(length):
                for frame in range(int(self.refresh_rate / kwargs['frequency'])):
                    self.frame_list.append((1.0, 1.0, stim.draw, stim.setPhase, tuple((0.0,)), stim.setOri, orientation))
                for frame in range(int(self.refresh_rate / kwargs['frequency'])):
                    self.frame_list.append((0.0, 1.0, stim.draw, stim.setPhase, tuple((0.5,)), stim.setOri, orientation))
                    
    def run_stimulus(self, stim_function):
        def wrapper():
            self.frame_list = list()
            if self.window is None:
                return
            self.abort_warning_string.set("running")
            self.update()
            self.stim = visual.GratingStim(tex = self.texture, win=self.window, mask=None, size=200, pos=[0,0], sf=self.spatial_freq , ori=135)
            self.window.setRecordFrameIntervals(True)
            self.window._refreshThreshold=1/60.0+0.002
            #set the log module to report warnings to the std output window (default is errors only)
            logging.console.setLevel(logging.WARNING)
            
            current_b = 0.0
            self.build_stim(self.fixation, 'gray', 1)
            
            stim_function()
            
            #ALWAYS GIVE PSYCHOPY TIME TO SPOOL UP AND DOWN OR YOU WILL SEE TIMING ERRORS
            for frame in range(300):
                self.fixation.draw()
                self.window.flip()
            for i in range(len(self.frame_list)):
                if 'escape' in psyevent.getKeys():
                    break
                psyevent.clearEvents()
                
                #Sets value of arduino pin and tells psychopy to write it when the monitor refreshes
                current_b = self.frame_list[i][1]
                self.window.callOnFlip(pin_b.write, current_b)
                
                #calls build stim phase and direction entries in stim.setPhase
                self.frame_list[i][3](* self.frame_list[i][4])
                
                #calls build stim orientation entry in stim.setOrientation
                self.frame_list[i][5](self.frame_list[i][6])            
                
                #draws the stim
                self.frame_list[i][2]()
                self.window.flip()
                pin_a.write(self.frame_list[i][0])
    
    
            self.fixation.draw()
            self.window.flip()
            pin_a.write(0.0)
            pin_b.write(0.0)
            logging.flush()
            self.window.setRecordFrameIntervals(False)
            
            self.ABORT = False
            self.abort_warning_string.set("ready")
            self.update()
            
        return wrapper

    
    def abort_run(self):
        if self.window is not None:
            self.ABORT = True
            self.abort_warning_string.set("aborting")

    #Dummy event function
    def default_on_event(self):
        print "event detected"
        
    def on_focus_in(self, event):
        self.lift()
        for win in self.windows:
            self.windows[win].lift()
    
    def on_closing(self):
        if self.window is not None:
            #if messagebox.askokcancel("Quit", "Do you want to quit?"):

            self.window.close()
        board.exit()
        self.destroy()

    
    #Open a file dialog and record selected filenames to self.file_names
    def load(self):
        files = tkFileDialog.askopenfilenames()
        self.file_list = list(files)
    
    def file_to_array(self, fn):
        with open(fn, 'rb') as open_file:
            self.data.append(np.array(open_file))
    
    def csv_to_array(self, fn):
        with open(fn, 'rb') as csv_file:
            reader = csv.reader(csv_file, delimiter = ',')
            self.data.append(np.array(reader))

              
#-----Windows-----
#Left Window
class window_one(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #self.title("Window One")
        #Set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos = 0
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % ( self.hpos, self.vpos))

#Right Window
class window_two(Window):
    def __init__(self, parent, *args, **kwargs):
        Window.__init__(self, parent, *args, **kwargs)
        #set window position (needs to happen last to account for widget sizes)
        #self.geometry("+%d+%d" % (0, 0))
        self.update()
        self.hpos =  self.winfo_screenwidth() - self.winfo_width()
        self.vpos = self.winfo_screenheight()/2 - self.winfo_height()/2
        self.geometry("+%d+%d" % (self.hpos, self.vpos))

                
if __name__ == "__main__":
    MainApp()
