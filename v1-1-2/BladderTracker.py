##################################################
## BladderTracker Software
## 
## Used to track pressure and wall motions during bladder filling.
## Designed to work with Thorlabs DCC1545M
## For additional info see www.vasostracker.com and https://github.com/VasoTracker/BladderTracker
## 
##################################################
## 
## BSD 3-Clause License
## 
## Copyright (c) 2019, VasoTracker
## All rights reserved.
## 
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
## 
## ## * Redistributions of source code must retain the above copyright notice, this
##   list of conditions and the following disclaimer.
## 
## * Redistributions in binary form must reproduce the above copyright notice,
##   this list of conditions and the following disclaimer in the documentation
##   and/or other materials provided with the distribution.
## 
## * Neither the name of the copyright holder nor the names of its
##   contributors may be used to endorse or promote products derived from
##   this software without specific prior written permission.
## 
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
## DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
## FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
## SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
## CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
## OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
## 
##################################################
## 
## Author: Penelope F Lawton, Matthew D Lee, and Calum Wilson
## Additional programming: Nathan R. Tykocki
## Copyright: Copyright 2019, VasoTracker
## Credits: Penelope F Lawton, Matthew D Lee, and Calum Wilson (and maybe Nathan Tykocki)
## License: BSD 3-Clause License
## Version: 1.1.0
## Maintainer: Nathan Tykocki
## Email: vasotracker@gmail.com
## Status: Beta
## Last updated: 2019-11-05 (NRT)
## 
##################################################
## We found the following to be useful:
## https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch09s07.html
## http://code.activestate.com/recipes/82965-threads-tkinter-and-asynchronous-io/
## https://www.physics.utoronto.ca/~phy326/python/Live_Plot.py
## http://forum.arduino.cc/index.php?topic=225329.msg1810764#msg1810764
## https://stackoverflow.com/questions/9917280/using-draw-in-pil-tkinter
## https://stackoverflow.com/questions/37334106/opening-image-on-canvas-cropping-the-image-and-update-the-canvas
##################################################

from __future__ import division
import numpy as np
# Tkinter imports
import Tkinter as tk
from Tkinter import *
import tkSimpleDialog
import tkMessageBox as tmb
import tkFileDialog
import ttk
from PIL import Image, ImageTk #convert cv2 image to tkinter
E = tk.E
W = tk.W
N = tk.N
S = tk.S
ypadding = 1.5 #ypadding just to save time - used for both x and y

# Other imports
import os
import sys
import time
import datetime
import threading
import random
import Queue

import cv2
import csv
from skimage import io
import skimage
from skimage import measure
import serial
import win32com.client
import webbrowser
from skimage.transform import rescale, resize, downscale_local_mean
from scipy import misc
# Import Vasotracker functions
from VT_Arduino import Arduino
import snake

# Add MicroManager to path
import sys
MM_PATH = os.path.join('C:', os.path.sep, 'Program Files','Micro-Manager-1.4')
sys.path.append(MM_PATH)
os.environ['PATH'] = MM_PATH + ';' + os.environ['PATH']
import MMCorePy
'''
import sys
sys.path.append('C:\Program Files\Micro-Manager-1.4')
import MMCorePy
'''
#import PyQt5
# matplotlib imports
import matplotlib
#matplotlib.use('Qt5Agg') 
#matplotlib.use('Qt4Agg', warn=True)
import matplotlib.backends.tkagg as tkagg
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
from matplotlib.backends import backend_qt4agg
from matplotlib import pyplot


from collections import deque

##################################################
## GUI main application 
##################################################
class GuiPart(tk.Frame):

    #Initialisation function
    def __init__(self, master, queue,queue2, endCommand, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.queue = queue
        self.queue2 = queue2
        self.endApplication = endCommand
        global root
        self.root = root
        self.VTD = os.getcwd()
        global VTD
        VTD = self.VTD

    #Set up the GUI
        self.grid(sticky=N+S+E+W)
        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.filename = self.get_file_name()
        print self.filename  

    # Arduino       
        #self.Arduino = Arduino(self)
        #self.ports = self.Arduino.getports()
    
    # Timing functions
        self.timeit = TimeIt()
        self.timeit2 = TimeIt2()
        #self.timeit3 = TimeIt3()

    # Initial Values

    # Scale setting
        self.multiplication_factor = 1 # Scale setting

    # Exposure setting
        global exposure
        exposure = 500
        self.exposure = exposure

    # npts setting
        global npts
        npts = 1200
        self.npts = npts


    # Acquisition rate setting
        global acq_rate
        acq_rate = 0
        self.acq_rate = acq_rate

    # Record interval setting
        global rec_interval
        rec_interval = 1
        self.rec_interval = rec_interval

        self.initUI(endCommand)

    # Open the csv file and then clear it
        f = open(self.filename.name, "w+")
        f.close()

    # Add the headers
        with open((self.filename.name), 'ab') as f:
            w=csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(("Time",'Temperature (oC)', 'Pressure (mmHg)', 'Length (um)'))

    # Add file for table
        self.txt_file = os.path.splitext(self.filename.name)[0]
        print "tail = ", self.txt_file
        self.txt_file = self.txt_file + ' - Table' + '.csv'
        g = open(self.txt_file, "w+")
        g.close()
        with open((self.txt_file), 'ab') as g:
                v=csv.writer(g, quoting=csv.QUOTE_ALL)
                column_headings = 'Time (s)', 'Note', 'Temp (oC)', 'P (mmHg)', 'Dist (um)'
                v.writerow(column_headings)

    # Function for getting the save file.
    def get_file_name(self):
        tmb.showinfo("", "Create a file to save output...")
        now = datetime.datetime.now()
        savename = now.strftime("%Y%m%d")
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".csv", initialdir= os.path.join(VTD, 'Results'), initialfile=savename)
        if f:
            print "f = ", f
            return(f)            
        else: # asksaveasfile return `None` if dialog closed with "cancel".
            if tmb.askquestion("No save file selected", "Do you want to quit VasoTracker?", icon='warning') == "yes":
                self.endApplication()
            else:
                f = self.get_file_name()
                return (f)

    # Function for writing to the save file
    def writeToFile(self,data):
        with open((self.filename.name), 'ab') as f:
            w=csv.writer(f, quoting=csv.QUOTE_ALL)
            w.writerow(data)

    # Function for closing down
    def close_app(self):
        if tmb.askokcancel("Close", "Are you sure...?"):
            self.endApplication()

    def gotouserguide(self):
        tmb.showinfo("Woops", "We've been too busy to write a user guide. Some details (like using certain cameras) are detailed in our VasoTracker software manual. Have a quick look at that...")
        webbrowser.open_new(r"http://www.vasotracker.com/wp-content/uploads/2019/04/VasoTracker-Acquistion-Software-Manual.pdf")


    def gotocontact(self):
        tmb.showinfo("We would hate to hear from you", "Because it probably means there is a problem. Despite our feelings, we will do our best to help. Our contact details should pop up in your web browser...")
        webbrowser.open_new(r"http://www.vasotracker.com/about/contact-us/")

    def launchabout(self):
        webbrowser.open_new(r"http://www.vasotracker.com/about/")

    def launchsnake(self):
        tmb.showinfo("We did warn you.", "Any hope of this being a productive day have just went out the window...")
        window = tk.Toplevel(root)
        window.iconbitmap('bladder_ICON.ICO')
        snake.Application(window)



    # Function for defining an average checkbox ## Shouldbe in toolbar!
    def average_checkbox(self, window, text):
        avg_checkbox = ttk.Checkbutton(window, text=text)
        avg_checkbox.grid(row=0, columnspan=4, padx=3, pady=3)

    # Second Function for initialising the GUI
    def initUI(self,endCommand):

    # make Esc exit the program
        root.bind('<Escape>', lambda e: endCommand)

    # make the top right close button minimize (iconify) the main window
        root.protocol("WM_DELETE_WINDOW", self.close_app)

    # create a menu bar with an Exit command
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=self.close_app)
        filemenu = tk.Menu(menubar, tearoff=0)
        
    # Create a help menu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='User Guide', command = self.gotouserguide)
        helpmenu.add_command(label='Contact', command = self.gotocontact)
        helpmenu.add_command(label='About', command = self.launchabout)

        helpmenu.add_separator()

        helpmenu.add_command(label='Do not click here...', command = self.launchsnake)
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Help", menu=helpmenu)
        root.config(menu=menubar)
        self.pack(fill=BOTH, expand=1)

    # Make the toolbar along the top
        self.toolbar = ToolBar(self)#ttk.Frame(root, height=150)
        self.toolbar.grid(row=0, column=0,rowspan=1,columnspan=4, padx=ypadding, pady=ypadding, sticky=E+S+W+N)
        self.toolbar.grid(sticky='nswe')
        self.toolbar.rowconfigure(0, weight=1)
        self.toolbar.columnconfigure(0, weight=1)
        self.toolbar.grid_propagate(0)

    # Make the status bar along the bottom
        def callback(event):
            webbrowser.open_new(r"https://doi.org/10.3389/fphys.2019.00099")
        self.status_bar = ttk.Label(text = 'BladderTracker is based on VasoTracker software. Clicking here will take you to our wonderful paper.', relief=SUNKEN, anchor='w')
        
        self.status_bar.pack(side=BOTTOM, fill=X)
        self.status_bar.bind("<Button-1>", callback)
        
    # Make the graph frame
        self.graphframe = GraphFrame(self)
        self.graphframe.grid(row=1, column=0, rowspan=2,columnspan=1, padx=ypadding, pady=ypadding, sticky=E+S+W+N)
        self.graphframe.grid(sticky='nswe')
        print "this is the height: ", self.graphframe.winfo_height()
        #self.graphframe.rowconfigure(0, weight=1)
        #self.graphframe.columnconfigure(0, weight=1)
        #self.graphframe.grid_propagate(0)
 
    # Make the table frame
        self.tableframe = TableFrame(self)
        self.tableframe.grid(row=1, column=1,rowspan=1,columnspan=1, padx=ypadding, pady=ypadding, sticky=E+S+W+N)
        self.tableframe.grid(sticky='nwe')
        #self.tableframe.rowconfigure(0, weight=1)
        #self.tableframe.columnconfigure(0, weight=1)
        #self.tableframe.grid_propagate(0)


    #Update everything so that the frames are all the correct size. We need to do this so we can size the graph/image before we place them.
        self.toolbar.update()
        self.status_bar.update()
        #self.graphframe.update()
        self.tableframe.update()
        self.toolbar.update()


    # Make the Camera Frame bottom right
        self.cameraframe = CameraFrame(self)
        self.cameraframe.grid(row=2, column=1,rowspan=1,columnspan=1, padx=ypadding, pady=ypadding, sticky=E+S+W+N)
        self.cameraframe.grid(sticky='nswe')
        #self.cameraframe.rowconfigure(0, weight=3)
        #self.cameraframe.columnconfigure(0, weight=2)
        #self.cameraframe.grid_propagate(0)

        print "this is the height: ", self.graphframe.winfo_height()
        print "this is the width: ", self.graphframe.winfo_width()
        self.graphframe.mainWidgets() # Now set up the graph

        #if self.toolbar.start_flag:
        #    mmc.startContinuousSequenceAcquisition(500)
        

    # Count function for reading in with FakeCamera
        self.count = 0   
    # Count function for resizing on first image acquisition
        self.count2 = 0      

    # Lists for storing the data
        self.timelist = []
        self.temp = []
        self.pressure = []
        self.distance = []
        self.pressure_avg = []

        self.timelist = [np.nan] * (self.npts-1)
        self.templist = [np.nan] * (self.npts-1)
        #self.pressure1 = []
        #self.pressure2 = []
        self.pressureavglist = [np.nan] * (self.npts-1)

        self.T = []
        self.PAVG = np.nan

    def sortdata(self,temppres):
        #print temppres
        #print "Length of the data = ", len(temppres)
        T = np.nan
        P = np.nan
        D1 = np.nan
        for i,data in enumerate(temppres):
            #print "length of data = ", len(data)#val = ser.readline().strip('\n\r').split(';')
            #print "this is what we are looking at",data
            if len(data) > 0:
                val = data[0].strip('\n\r').split(';')[:-1]
                val = [el.split(':') for el in val]
                if val[0][0] == "T":
                    temp = float(val[0][1])
                    #print "this is a temp = ", temp
                    T = temp
                elif val[0][0] == "P":
                    pres = float(val[0][1])
                    length = float(val[1][1])
                    #print "this is a pressure = ", pres1
                    P,D1 = pres,length

        return P,D1,T



    # This function will process all of the incoming images
    def processIncoming(self): 
        """Handle all messages currently in the queue, if any."""
        if self.toolbar.record_flag:
            if self.count == 0:
                global start_time
                global T, P, D1
                global acqrate
                start_time=time.time()
            # This is for loading in a video as an example!
            try:
                mmc.setProperty('Focus', "Position", self.count%500)
                #print "the count is this:", self.count
                #print "the image is this:", self.count%500
                #print mmc.getProperty('Camera', 'Resolved path')
            except:
                pass

        #Get the image
            if self.queue.qsize(  )>0:
                msg = self.queue.get(0)

                #msg = downscale_local_mean(msg, (2, 2),np.mean)
                #msg = np.array(msg, dtype=np.uint8)
                #print "binned shape: ", msg.shape
            #Get the time
                timenow = time.time() - start_time
                self.toolbar.update_time(timenow)
            # Get the arduino data
                

                
                # Need to set this to remember the previos contents.
                if self.queue2.qsize(  )>0:
                    (P,D1,self.T) = self.queue2.get(0)
                    #self.PAVG = (P1+P2)/2
                    
                else:
                    (P,D1,T) = (np.nan,np.nan, np.nan)



                
                #PAVG = 100.99
                '''
                #temppres = self.Arduino.getData()
                #P1,P2,T = self.sortdata(temppres)
                #print "Arduino data = ", P1,P2,T
                PAVG = (P1+P2)/2
                PAVG = 100.99
                

                
                if self.queue2.qsize(  )>0:
                    print "Queue2 size is this", self.queue2.qsize(  )
                    temppres = self.queue2.get(0)
                    P,D1,T = temppres
                    PAVG = (P1+P2)/2
                else:
                    P,D1,T = np.nan,np.nan, np.nan
                    PAVG = (P1+P2)/2
                '''
                

                #with self.timeit2("update data display"):
                #self.toolbar.update_temp(T) #### CHANGE to T
                #self.toolbar.update_pressure(P1,P2, self.PAVG)
                self.toolbar.update_temp(self.T) #### CHANGE to T
                self.toolbar.update_pressure(P, D1)

            # Get the acquisition rate
                
                self.toolbar.update_acq_rate(acqrate)

                self.cameraframe.process_queue(msg,self.count2)

                #with self.timeit2("some other stuff"):
                
                
                
                #if self.count%10 == 0:

                self.timelist.append(timenow)
                self.templist.append(self.T)
                #pressure1list.append(P1)
                #pressure2list.append(P1)
                self.pressureavglist.append(self.PAVG)
                if len(self.timelist)>self.npts:
                    print "we are in here"
                    # Should use deque to do this.
                    
                    d = deque(self.timelist)
                    d.popleft()
                    self.timelist = list(d)

                    d = deque(self.templist)
                    d.popleft()
                    self.templist = list(d)

                    d = deque(self.pressureavglist)
                    d.popleft()
                    self.pressureavglist = list(d)
                    
                    '''
                    self.timelist.pop(0)
                    self.templist.pop(0)
                    #pressure1list.pop(0)
                    #pressure2list.pop(0)
                    self.pressureavglist.pop(0)
                    '''

                print "Length of pressurelist = ", len(self.pressureavglist)






                # Save the required data
                savedata = timenow,self.T, self.PAVG
                self.writeToFile(savedata)

                #Get points within the axis limits
                xdata = filter(lambda x: x >= self.timelist[-1]-abs(self.toolbar.xlims[0]), self.timelist)
                    
                # Subtract off the latest time point, so that the current time is t = 0
                xdata = map(lambda x: x - xdata[-1], xdata)

                # Get the corresponding ydata points
                ydata1 = self.pressureavglist[len(self.pressureavglist)-len(xdata)::]#[0::10]

                
                #with self.timeit2("graph"):
                if self.count%1 == 0:
                    self.graphframe.plot(xdata,ydata1,self.toolbar.xlims, self.toolbar.ylims, self.toolbar.xlims2, self.toolbar.ylims2)    
                
            else:
                print "no image"    

        else:
            msg = self.queue.get(0)
            self.cameraframe.process_queue(msg,self.count2)  
            try:
                msg2 = self.queue2.get(0)
            except:
                pass
            
        self.count += 1
        self.count2 += 1
        #print self.count
        #return



# Class for the main toolbar
class ToolBar(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self, parent, height = 150)#,  width=250, highlightthickness=2, highlightbackground="#111")
        self.parent = parent
        self.mainWidgets()
        self.set_camera = setCamera(self)
        self.ref_OD = None




    #Functions that do things in the toolbar
    def update_temp(self, temp):
        # Updates the temperature widget
        '''
        self.temp_entry.config(state='normal')
        self.temp_entry.delete(0, 'end')
        self.temp_entry.insert(0, '%.2f' % temp)
        self.temp_entry.config(state='DISABLED')
        '''
        temp_string = str(round(temp,2))
        self.temp_contents.set(temp_string)

    def update_pressure(self, P,D1):
        # Update average pressure
        '''
        self.pressureavg_entry.config(state='normal')
        self.pressureavg_entry.delete(0, 'end')
        self.pressureavg_entry.insert(0, '%.2f' % PAvg)
        self.pressureavg_entry.config(state='DISABLED')
        '''
        pres_string = str(round(P,3))
        self.pressure_contents.set(pres_string)
        
    def update_distance(self, P,D1):
        # Update distance
        '''
        self.pressureavg_entry.config(state='normal')
        self.pressureavg_entry.delete(0, 'end')
        self.pressureavg_entry.insert(0, '%.2f' % PAvg)
        self.pressureavg_entry.config(state='DISABLED')
        '''
        pres_string = str(round(D1,3))
        self.distance_contents.set(pres_string)

    
    def update_time(self, time):
        #Update the temperature widget
        self.time_contents.set(str(datetime.timedelta(seconds=time))[:-4])
        print "the time is: ", str(datetime.timedelta(seconds=time))[:-4]
        '''
        self.time_entry.config(state='normal')
        self.time_entry.delete(0, END)
        timestring = str(datetime.timedelta(seconds=time))[:-4]
        self.time_entry.insert(0, timestring)
        self.time_entry.config(state='DISABLED')
        '''

    def update_acq_rate(self, acqrate):
        #Update the temperature widget
        self.acq_rate_contents.set(str(round(acqrate,2)))
        '''
        self.acq_rate__entry.config(state='normal')
        self.acq_rate__entry.delete(0, END)
        acqratestring = str(round(acqrate,2))
        self.acq_rate__entry.insert(0, acqratestring)
        self.acq_rate__entry.config(state='DISABLED')
        '''
        
    # Function that changes the exposure on enter key
    def update_exposure(self,event):
        global prevcontents,exposure        
        try:
        # Check if the exposure is within a suitable range
            exp = self.contents.get()
            if exp < 10:
                exp = 10
            elif exp > 500:
                exp = 500
            self.exposure_entry.delete(0, 'end')
            self.exposure_entry.insert('0', exp) 
            if exp < 10:
                tmb.showinfo("Warning", "Except for ThorCam, we recommend an exposure between 10 ms and 500ms")

            print "Setting exposure to:", exp
            self.parent.exposure = int(exp)
            print mmc.getExposure()
            prevcontents = exp
            exposure = exp
        except: 
            print "Exposure remaining at:", prevcontents
            self.exposure_entry.delete(0, 'end')
            self.exposure_entry.insert('0', prevcontents)
            exposure = prevcontents
        self.set_camera.set_exp(exposure)
        print mmc.getExposure()
        self.exposure_entry.delete(0, 'end')
        self.exposure_entry.insert('0', mmc.getExposure()) 

    # Function that changes the exposure on enter key
    def update_npts(self,event):
        global npts_prevcontents,npts        
        try:
        # Check if the exposure is within a suitable range
            npts = self.npts_contents.get()
            if npts < 10:
                npts = 10
            elif npts > 2400:
                npts = 2400
            self.npts_entry.delete(0, 'end')
            self.npts_entry.insert('0', npts) 

            print "Setting npts to:", npts
            self.parent.npts = int(npts)
            npts_prevcontents = npts
            npts = npts
        except: 
            print "Exposure remaining at:", npts_prevcontents
            self.npts_entry.delete(0, 'end')
            self.npts_entry.insert('0', npts_prevcontents)
            npts = npts_prevcontents


    def update_rec_interval(self,event):
        global rec_interval, rec_prevcontents
        try: # Should check contents for int rather than try and catch exception
            rec = self.rec_contents.get()
            self.rec_interval_entry.delete(0, 'end')
            self.rec_interval_entry.insert('0', rec) 
            self.parent.rec_interval = int(rec)
            rec_prevcontents = rec
            rec_interval = rec
        except: 
            print "Record interval remaining at:", rec_prevcontents
            self.rec_interval_entry.delete(0, 'end')
            self.rec_interval_entry.insert('0', rec_prevcontents)
            rec_interval = rec_prevcontents

        # TO DO MAKE SURE THIS WORKS
        # Function that changes the exposure on enter key
    def update_scale(self,event):
        print "updating the scale..."
        try:
        # Check if the exposure is within a suitable range
            scale = self.scale_contents.get()
            print "the scale is:", scale
            self.scale_entry.delete(0, 'end')
            self.scale_entry.insert('0', scale) 
            print "Setting scale to:", scale
            self.parent.multiplication_factor = scale
            self.scale_prevcontents = scale
            
        except:
            print "Scale remaining at:", self.scale_prevcontents
            self.scale_entry.delete(0, 'end')
            self.scale_entry.insert('0', self.scale_prevcontents)
            self.parent.multiplication_factor = self.scale_prevcontents


    def mainWidgets(self):
        self.toolbarview = ttk.Frame(root, relief=RIDGE)
        self.toolbarview.grid(row=2,column=3,rowspan=2,sticky=N+S+E+W, pady=0)

   # Tool bar groups
        source_group = ttk.LabelFrame(self, text='Source', height=150, width=150)
        source_group.pack(side=LEFT, anchor=N, padx=3, fill=Y)

        settings_group = ttk.LabelFrame(self, text='Acquisition Settings', height=150, width=150)
        settings_group.pack(side=LEFT, anchor=N, padx=3, fill=Y)

        outer_diameter_group = ttk.LabelFrame(self, text='Graph Settings', height=150, width=150)
        outer_diameter_group.pack(side=LEFT, anchor=N, padx=3, fill=Y)

        acquisition_group = ttk.LabelFrame(self, text='Data acquisition', height=150, width=150)
        acquisition_group.pack(side=LEFT, anchor=N, padx=3, fill=Y)

        start_group = ttk.LabelFrame(self, text='Start/Stop', height=150, width=150)
        start_group.pack(side=LEFT, anchor=N, padx=3, fill=Y)

    # Source group (e.g. camera and files)
        camera_label = ttk.Label(source_group, text = 'Camera:')
        camera_label.grid(row=0, column=0, sticky=E)

        path_label = ttk.Label(source_group, text = 'Path:')
        path_label.grid(row=1, column=0, sticky=E)

        save_label = ttk.Label(source_group, text = 'File:')
        save_label.grid(row=2, column=0, sticky=E)

        # Flag Start/stop group
        self.start_flag = False
        def set_cam(self):
            if self.start_flag == False:
                camera_label = self.variable.get()
                self.set_camera.set(camera_label)
                #self.BIN_entry.configure(state="enabled")
                #self.FOV_entry.configure(state="enabled")
                return
            else:
                print "You can't change the camera whilst acquiring images!"
                return

        self.camoptions = ["...","TIS_DCAM","Thorlabs","OpenCV", "FakeCamera", "uManagerCam"]

        self.variable = StringVar()
        self.variable.set(self.camoptions[0])
        self.camera_entry = ttk.OptionMenu(source_group, self.variable,self.camoptions[0], *self.camoptions, command= lambda _: set_cam(self))
        self.camera_entry.grid(row=0, column=1, pady=5)

        global head, tail
        head,tail = os.path.split(self.parent.filename.name)

        path_entry = ttk.Entry(source_group, width=20)
        path_entry.insert(0, head)
        path_entry.config(state=DISABLED)
        path_entry.grid(row=1, column=1, pady=5)

        save_entry = ttk.Entry(source_group, width=20)
        save_entry.insert(0, tail)
        save_entry.config(state=DISABLED)
        save_entry.grid(row=2, column=1, pady=5)

        # Create list buttons for the field of view


        self.test = 0
        def ShowChoice():
            if self.test == 0:
                self.cam_x_dim = mmc.getImageWidth()
                self.cam_y_dim = mmc.getImageHeight()
                print "Cam dimensions: ", self.cam_x_dim, self.cam_y_dim
                self.test = self.test + 1

            mmc.stopSequenceAcquisition()

            print(self.FOV_variable.get())
            # Need to get the dimensions of the image.
            if self.FOV_variable.get() == "w x h":
                try:
                    mmc.setROI(0, 0, self.cam_x_dim, self.cam_y_dim)
                    mmc.startContinuousSequenceAcquisition(0)
                except:
                    tmb.showinfo("Warning", "Not available for this camera")
                    self.FOV_variable.set(self.FOV_modes[0])
            elif self.FOV_variable.get() == "w/2 x h/2":
                try:
                    mmc.setROI(int(self.cam_x_dim/4), int(self.cam_y_dim/4), int(self.cam_x_dim/2), int(self.cam_y_dim/2))

                    mmc.startContinuousSequenceAcquisition(0)
                except:
                    tmb.showinfo("Warning", "Not available for this camera")
                    self.FOV_variable.set(self.FOV_modes[0])


        #self.FOV_selection = IntVar(value=1)  # initializing the choice, i.e. Python
        self.FOV_modes = [("w x h"), ("w/2 x h/2")]
        self.FOV_modes_label = ttk.Label(source_group, text = 'FOV:')
        self.FOV_modes_label.grid(row=3, column=0, sticky=E)

        self.FOV_variable = StringVar()
        self.FOV_variable.set(self.FOV_modes[0])
        self.FOV_entry = ttk.OptionMenu(source_group, self.FOV_variable,self.FOV_modes[0], *self.FOV_modes, command= lambda _: ShowChoice())
        self.FOV_entry.grid(row=3, column=1, pady=5)
        self.FOV_entry.configure(state="disabled")



        def SetBin():
            self.test = 0
            try:
                cameraName = mmc.getCameraDevice()
                print cameraName
                self.test = 1
            except:
                pass

            #mmc.stopSequenceAcquisition()
            '''
            print(self.BIN_variable.get())
            # Need to get the dimensions of the image.
            if self.BIN_variable.get() == "1x":
                try:
                    mmc.setProperty(cameraName, "Binning", "1")
                    print "Binning set to 1X"
                    self.BIN_prevcontents = self.BIN_variable.get()
                except:
                    self.BIN_variable.set(self.BIN_prevcontents)
                mmc.startContinuousSequenceAcquisition(0)
            elif self.BIN_variable.get() == "2x":
                try:
                    mmc.setProperty(cameraName, "Binning", "2")
                    print "Binning set to 2X"
                    self.BIN_prevcontents = self.BIN_variable.get()
                except:
                    self.BIN_variable.set(self.BIN_prevcontents)
            elif self.BIN_variable.get() == "4x":
                try:
                    mmc.setProperty(cameraName, "Binning", "4")
                    print "Binning set to 4X"
                    self.BIN_prevcontents = self.BIN_variable.get()
                except:
                    self.BIN_variable.set(self.BIN_prevcontents)

            '''

                

        self.BIN_modes = [("1x"), ("2x"), ("4x")]
        self.BIN_modes_label = ttk.Label(source_group, text = 'Binning:')
        self.BIN_modes_label.grid(row=4, column=0, sticky=E)

        self.BIN_variable = StringVar()
        self.BIN_variable.set(self.BIN_modes[0])
        self.BIN_prevcontents = self.BIN_variable.get()
        self.BIN_entry = ttk.OptionMenu(source_group, self.BIN_variable,self.BIN_modes[0], *self.BIN_modes, command= lambda _: SetBin())
        self.BIN_entry.grid(row=4, column=1, pady=5)        
        self.BIN_entry.configure(state="disabled")
        #cameraName = mmc.getCameraDevice()
        #mmc.setProperty(cameraName, "Binning", "1")       


    # Settings group (e.g. camera and files)
        scale_label = ttk.Label(settings_group, text = 'um/pixel:')
        scale_label.grid(row=0, column=0, sticky=E)

        exposure_label = ttk.Label(settings_group, text = 'Exp (msec):')
        exposure_label.grid(row=1, column=0, sticky=E)

        acqrate_label = ttk.Label(settings_group, text = 'Acq rate (Hz):')
        acqrate_label.grid(row=2, column=0, sticky=E)

        rec_interval_label = ttk.Label(settings_group, text = 'Rec intvl (frames):')
        rec_interval_label.grid(row=3, column=0, sticky=E)

        # Scale settings
        scale = self.parent.multiplication_factor
        scalefloat = "%3.0f" % scale
        self.scale_contents = DoubleVar()
        self.scale_contents.set(scalefloat)
        global scale_contents
        self.scale_prevcontents = self.scale_contents.get()
        self.scale_entry = ttk.Entry(settings_group, textvariable = self.scale_contents,width=20)
        self.scale_entry.grid(row=0, column=1, pady=5)
        self.scale_entry.bind('<Return>', self.update_scale)

        # Exposure settings
        exp = self.parent.exposure
        expfloat = "%3.0f" % exp
        self.contents = IntVar()
        self.contents.set(int(exp))
        global prevcontents
        prevcontents = self.contents.get()
        self.exposure_entry = ttk.Entry(settings_group, textvariable = self.contents,width=20)
        self.exposure_entry.grid(row=1, column=1, pady=5)
        self.exposure_entry.bind('<Return>', self.update_exposure)


               
        # Acquisition rate settings
        acq_rate = self.parent.acq_rate
        acq_rate = "%3.0f" % acq_rate
        self.acq_rate_contents = IntVar()
        self.acq_rate_contents.set(int(acq_rate))
        global acq_rate_prevcontents
        acq_rate_prevcontents = self.acq_rate_contents.get()
        self.acq_rate__entry = ttk.Entry(settings_group, textvariable = self.acq_rate_contents,width=20)
        self.acq_rate__entry.grid(row=2, column=1, pady=5)
        self.acq_rate__entry.configure(state="disabled")
        #self.acq_rate_entry.bind('<Return>', self.acq_rate_exposure)

        # Record interval settings
        rec_interval = self.parent.rec_interval
        self.rec_contents = IntVar()
        self.rec_contents.set(int(rec_interval))
        global rec_prevcontents
        rec_prevcontents = self.rec_contents.get()
        self.rec_interval_entry = ttk.Entry(settings_group, textvariable = self.rec_contents,width=20)
        self.rec_interval_entry.grid(row=3, column=1, pady=5)
        self.rec_interval_entry.bind('<Return>', self.update_rec_interval)

      

    # Outer diameter group
    # Function for the labels
        def coord_label(window, text, row, column):
            label=ttk.Label(window, text=text)
            label.grid(row=row, column=column, padx = 5, pady=5, sticky=E)
    # Function for the labels 2
        def coord_entry(window, row, column, coord_label):
            entry = ttk.Entry(window, width=8, textvariable=coord_label)
            entry.config(state=NORMAL)
            entry.grid(row=row, column=column, padx=5, pady=5, sticky=E)
            root.focus_set()
            entry.focus_set()
            root.focus_force()
            return entry
            
        def set_button(window):
            set_button = ttk.Button(window, text='Set', command= lambda: coord_limits(get_coords=True, default = False))
            set_button.grid(row=6, column=1,columnspan=2, pady=5)

        def coord_limits(get_coords, default):
            if get_coords == True:
                self.xlims = (self.x_min_label.get(),self.x_max_label.get())
                self.ylims = (self.y_min_label.get(),self.y_max_label.get())
                self.xlims2 = self.xlims
                self.ylims2 = (self.y_min_label2.get(),self.y_max_label2.get())
                self.parent.graphframe.update_scale()
                return self.xlims, self.ylims, self.xlims2, self.ylims2
                get_coords = False
            else:
                pass

    #Pressure Values
    # Set the initial xlimit values

        self.x_min_label, self.x_max_label = IntVar(value=-120), IntVar(value=0)
        self.x_min_default, self.x_max_default = self.x_min_label.get(),self.x_max_label.get()
    # Set the initial xlimit values
        self.y_min_label, self.y_max_label = IntVar(value=0), IntVar(value=200)
        self.y_min_default, self.y_max_default = self.y_min_label.get(),self.y_max_label.get()
    # Get the x and y limits
        self.xlims = (self.x_min_label.get(),self.x_max_label.get())
        self.ylims = (self.y_min_label.get(),self.y_max_label.get())
    #Temp Values
    # Set the initial xlimit values
        self.x_min_label2, self.x_max_label2 = IntVar(value=-120), IntVar(value=0)
        self.x_min_default2, self.x_max_default2 = self.x_min_label2.get(),self.x_max_label2.get()
    # Set the initial xlimit values
        self.y_min_label2, self.y_max_label2 = IntVar(value=0), IntVar(value=50)
        self.y_min_default2, self.y_max_default2 = self.y_min_label2.get(),self.y_max_label2.get()
    # Get the x and y limits
        self.xlims2 = self.xlims
        self.ylims2 = (self.y_min_label2.get(),self.y_max_label2.get())

        coord_label(outer_diameter_group, 'Min', 1, 1)
        coord_label(outer_diameter_group, 'Max', 1, 2)

        coord_label(outer_diameter_group, 'Time:', 2, 0)
        coord_label(outer_diameter_group, 'Pressure:', 3, 0)


        P_xmin_entry = coord_entry(outer_diameter_group, 2, 1, self.x_min_label)
        P_xmax_entry = coord_entry(outer_diameter_group, 2, 2, self.x_max_label)
        P_ymin_entry = coord_entry(outer_diameter_group, 3, 1, self.y_min_label)
        P_ymax_entry = coord_entry(outer_diameter_group, 3, 2, self.y_max_label)

        coord_label(outer_diameter_group, 'Temp:', 4, 0)

        T_ymin_entry = coord_entry(outer_diameter_group, 4, 1, self.y_min_label2)
        T_ymax_entry = coord_entry(outer_diameter_group, 4, 2, self.y_max_label2)


        npts_label = ttk.Label(outer_diameter_group, text = 'Graph pts:')
        npts_label.grid(row=5, column=1, sticky=E)

        # Exposure settings
        npts = self.parent.npts
        nptsfloat = "%3.0f" % exp
        self.npts_contents = IntVar()
        self.npts_contents.set(int(npts))
        global npts_prevcontents
        npts_prevcontents = self.npts_contents.get()
        self.npts_entry = ttk.Entry(outer_diameter_group, textvariable = self.npts_contents,width=8)
        self.npts_entry.grid(row=5, column=2, pady=5)
        self.npts_entry.bind('<Return>', self.update_npts)

        set_button(outer_diameter_group)     





    # acquisition_group
        temp_label = ttk.Label(acquisition_group, text = 'Temp (oC):')
        temp_label.grid(row=0, column=0, sticky=E)

        pressureavg_label = ttk.Label(acquisition_group, text = 'Avg Pressure (mmHg):')
        pressureavg_label.grid(row=1, column=0, sticky=E)

        time_label = ttk.Label(acquisition_group, text = 'Time (hr:min:sec:msec):')
        time_label.grid(row=4, column=0, sticky=E)

        self.temp_contents = IntVar()
        self.temp_contents.set("N/A")
        self.temp_entry = ttk.Entry(acquisition_group, textvariable = self.temp_contents, width=10)
        self.temp_entry.config(state=DISABLED)
        self.temp_entry.grid(row=0, column=1, pady=0)

        self.pressure_contents = IntVar()
        self.pressure_contents.set("N/A")
        self.pressureavg_entry = ttk.Entry(acquisition_group, textvariable = self.pressure_contents, width=10)
        self.pressureavg_entry.config(state=DISABLED)
        self.pressureavg_entry.grid(row=1, column=1, pady=0)

        self.time_contents = IntVar()
        self.time_contents.set(str(datetime.timedelta(seconds=time.time()-time.time()))[:-4])
        self.time_entry = ttk.Entry(acquisition_group,textvariable = self.time_contents, width=10)
        self.time_entry.config(state=DISABLED)
        self.time_entry.grid(row=4, column=1, pady=0)






    # Function that will start the image acquisition
        def start_acq():
            if self.variable.get() == "...":
                tmb.showwarning(title="Warning", message = "You need to select a camera source!")
                self.start_flag = False
            else:
                self.camera_entry.configure(state="disabled")
                self.exposure_entry.configure(state="disabled")
                self.scale_entry.configure(state="disabled")
                self.rec_interval_entry.configure(state="disabled")
                self.start_flag = True
                self.record_video_checkBox.configure(state="disabled")

                self.npts_entry.configure(state="disabled")
                mmc.startContinuousSequenceAcquisition(exposure) #50
                print "everything should be running"
            return self.start_flag
    # Function that will stop the image acquisition
        def stop_acq():
            self.camera_entry.configure(state="enabled")
            self.exposure_entry.configure(state="enabled")
            self.scale_entry.configure(state="enabled")
            self.rec_interval_entry.configure(state="enabled")
            self.start_flag = False
            self.record_video_checkBox.configure(state="enabled")
            mmc.stopSequenceAcquisition()
            self.record_flag = False
            #self.FOV_entry.configure(state="enabled")
            return self.start_flag,self.record_flag

    # Function that will start the data acquisition
        self.record_flag = False
        self.first_go = True
        def record_data():
            # On first press, set the global start time
            if self.first_go == True:
                    global start_time
                    start_time=time.time()
                    self.first_go = False

            if self.start_flag == True:
                self.record_flag = True
                mmc.clearCircularBuffer()
                self.FOV_entry.configure(state="disabled")
            print "Just set the record flag to: ", self.record_flag
            return self.record_flag
        '''
        def stop_record_data():
            self.record_flag = False
            print "Just set the record flag to: ", self.record_flag
            return self.record_flag
        '''
        def snapshot():
            self.snapshot_flag = True
            return self.snapshot_flag


        start_button = ttk.Button(start_group, text='Start', command= lambda: start_acq())
        start_button.grid(row=0, column=0, pady=0, sticky=N+S+E+W) 
        #console = tk.Button(master, text='Exit', command=self.close_app)
        #console.pack(  )
        live_button = ttk.Button(start_group, text='Stop', command= lambda: stop_acq())
        live_button.grid(row=1, column=0, pady=0, sticky=N+S+E+W) 

        record_button = ttk.Button(start_group, text='Track', command= lambda: record_data())
        record_button.grid(row=3, column=0, pady=0, sticky=N+S+E+W) 
        
        self.snapshot_flag = False
        snapshot_button = ttk.Button(start_group, text='Snapshot', command= lambda: snapshot())
        snapshot_button.grid(row=4, column=0, pady=0, sticky=N+S+E+W) 

        #stop_record_button = ttk.Button(start_group, text='Stop tracking', command= lambda: stop_record_data())
        #stop_record_button.grid(row=4, column=0, pady=5, sticky=N+S+E+W) 

        self.record_is_checked = IntVar()

        self.record_video_label = ttk.Label(settings_group, text = 'Record video?')
        self.record_video_label.grid(row=4, column=0, sticky=E)
        self.record_video_checkBox = ttk.Checkbutton(settings_group, onvalue=1, offvalue=0, variable=self.record_is_checked)
        self.record_video_checkBox.grid(row=4, column=1, columnspan=1, padx=5, pady=3, sticky=W)

class GraphFrame(tk.Frame):

    min_x = 0
    max_x = 10
    def __init__(self,parent):
        tk.Frame.__init__(self, parent)#, bg = "yellow")#, highlightthickness=2, highlightbackground="#111")
        self.parent = parent
        self.top = Frame()
        self.top.update_idletasks()
        self.n_points = 100
        self.xlim1 = self.parent.toolbar.x_min_default # Outer
        self.xlim2 = self.parent.toolbar.x_max_default # Outer
        self.ylim1 = self.parent.toolbar.y_min_default # Outer
        self.ylim2 = self.parent.toolbar.y_max_default # Outer


        self.xlim3 = self.parent.toolbar.x_min_default2 # Inner
        self.xlim4 = self.parent.toolbar.x_max_default2 # Inner
        self.ylim3 = self.parent.toolbar.y_min_default2 # Inner
        self.ylim4 = self.parent.toolbar.y_max_default2 # Inner

        self.delta_i = 1
        self.n_data = 100000000
        self.update = 1
        #self.mainWidgets()
        
    def update_scale(self, blit=True): #### NEE
        print "attempting to update a blitted axis"
        self.graphview.ax1.set_xlim(self.parent.toolbar.xlims[0],self.parent.toolbar.xlims[1]) # Outer diameter
        self.graphview.ax1.set_ylim(self.parent.toolbar.ylims[0],self.parent.toolbar.ylims[1]) # Outer diameter
        #self.graphview.ax2.set_xlim(self.parent.toolbar.xlims2[0],self.parent.toolbar.xlims2[1]) # Outer diameter
        #self.graphview.ax2.set_ylim(self.parent.toolbar.ylims2[0],self.parent.toolbar.ylims2[1])
        self.graphview.figure.canvas.draw()

    def mainWidgets(self,blit=True):  
        #
        # We want to explicitly set the size of the graph so that we can blit
        print "this is the height: ", self.parent.graphframe.winfo_height()
        print "this is the width: ", self.parent.graphframe.winfo_width()

        self.graphview = tk.Label(self)
        print "Graph width: ", self.graphview.winfo_width()
        print "Graph height: ", self.parent.graphframe.winfo_height()
        default_figsize = (plt.rcParams.get('figure.figsize'))
        print "default fig size = ", default_figsize
        other_figsize = [self.parent.graphframe.winfo_width()/100,self.parent.graphframe.winfo_height()/100]
        print other_figsize
        self.graphview.figure,self.graphview.ax1 = plt.subplots(1,1, figsize=other_figsize)
        self.graphview.figure = pyplot.figure()
        self.graphview.ax1 = self.graphview.figure.add_subplot(211)
        self.graphview.ax2 = self.graphview.figure.add_subplot(212)
        self.graphview.line, = self.graphview.ax1.plot([],[]) # initialize line to be drawn
        self.graphview.line2, = self.graphview.ax2.plot([],[])

        self.graphview.ax1.set_xlim(self.xlim1,self.xlim2) # Pressure
        self.graphview.ax2.set_xlim(self.xlim3,self.xlim4) # Distance
        self.graphview.ax1.set_ylim(self.ylim1,self.ylim2) # Pressure
        self.graphview.ax2.set_ylim(self.ylim3,self.ylim4) # Distance

        self.graphview.ax1.set_xlabel('Time (s)', fontsize=14) # Pressure labels
        self.graphview.ax1.set_ylabel('Pressure (mmHg)', fontsize=14) # Pressure labels

        self.graphview.ax2.set_xlabel('Time (s)', fontsize=14) # Distance labels
        self.graphview.ax2.set_ylabel('Distance (um)', fontsize=14) # Distance labels

        self.graphview.figure.canvas = FigureCanvasTkAgg(self.graphview.figure, self)
        self.graphview.figure.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=None, expand=False) ##### THIS IS THE PROBLEM WITH BLITTING HERE. WE NEED TO EXPLICITLY STATE THE FIGURE SIZE ABOVE!!
        print "Graph width: ", self.graphview.figure.canvas.get_tk_widget().winfo_width()
        self.graphview.figure.canvas.draw()
        print "Graph width: ", self.graphview.figure.canvas.get_tk_widget().winfo_width()

        if blit:
        # Get the background
            self.ax1background = self.graphview.figure.canvas.copy_from_bbox(self.graphview.ax1.bbox)
            self.ax2background = self.graphview.figure.canvas.copy_from_bbox(self.graphview.ax2.bbox)

            print "bounding box = ", self.graphview.ax1.bbox.get_points()
            bbarrray = self.graphview.ax1.bbox.get_points()
            from matplotlib.transforms import Bbox

            my_blit_box = Bbox(bbarrray)
            #my_blit_box = Bbox(np.array([[x0,y0],[x1,y1]]))
            my_blit_box = Bbox.from_bounds(bbarrray[0][0], bbarrray[0][1], (bbarrray[1][0]-bbarrray[0][0])*1.5, bbarrray[1][1]-bbarrray[0][1])
            print "bounding box = ", my_blit_box.get_points()
            self.ax1background = self.graphview.figure.canvas.copy_from_bbox(my_blit_box)
        
    

    def plot(self, timelist1, ydata1, xlims,ylims, xlims2, ylims2, blit=True):
        # Get the data
        if len(timelist1)>1:
            # Set the axis values
            self.graphview.ax1.set_xlim(xlims[0],xlims[1])  # Pressure
            self.graphview.ax1.set_ylim(ylims[0],ylims[1])  # Pressure

            self.graphview.ax2.set_xlim(xlims2[0],xlims2[1]) # Distance
            self.graphview.ax2.set_ylim(ylims2[0],ylims2[1]) # Distance

            # If there are many data points, it is a waste of time to plot all
            #   of them once the screen resolution is reached,
            #   so when the maximum number of points is reached,
            #   halve the number of points plotted. This is repeated
            #   every time the number of data points has doubled.
            '''
            self.i = int(len(timelist1))
            self.i2 = int(len(timelist2))
            print "length =", self.i
            if self.i > self.n_points :
                self.n_points *= 2
                # frequency of plotted points
                self.delta_i *= self.n_points/self.i
                self.update = max(self.delta_i, self.update)
                print("updating n_rescale = ",\
                    self.n_points, self.update, self.delta_i)
            '''
            
            # drawing the canvas takes most of the CPU time, so only update plot
            #   every so often
            if blit == False:

                try:
                    self.graphview.ax1.lines.remove(self.graphview.line)
                except:
                    pass

                self.graphview.line, = self.graphview.ax1.plot(
                                            timelist1,ydata1,
                                                color="blue", linewidth = 3)


                self.graphview.figure.canvas.draw()
                self.graphview.figure.canvas.get_tk_widget().update_idletasks()
                self.after(2,self.plotter)
                self.graphview.figure.canvas.flush_events()
            if blit == True:
                self.graphview.figure.canvas.restore_region(self.ax1background)
                self.graphview.figure.canvas.restore_region(self.ax2background)

                try:
                    self.graphview.ax1.lines.remove(self.graphview.line)
                    self.graphview.ax2.lines.remove(self.graphview.line2)
                except:
                    pass



                self.graphview.line.set_xdata(timelist1)#[::-1][0::int(self.delta_i)][::-1])
                self.graphview.line.set_ydata(ydata1)#[::-1][0::int(self.delta_i)][::-1])
                self.graphview.line.set_color('blue')


                self.graphview.line2.set_xdata(timelist2[::-1][0::int(self.delta_i)][::-1])
                self.graphview.line2.set_ydata(ydata2[::-1][0::int(self.delta_i)][::-1])
                self.graphview.line2.set_color('red')

                # redraw just the points
                self.graphview.ax1.draw_artist(self.graphview.line)
                self.graphview.ax2.draw_artist(self.graphview.line2)

                # fill in the axes rectangle
                self.graphview.figure.canvas.blit(self.graphview.ax1.bbox)
                self.graphview.figure.canvas.blit(self.graphview.ax2.bbox)

        #Example
        return

class TableFrame(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self, parent)#,highlightthickness=2,highlightbackground="#111")#, width=250, height = 300)#, highlightthickness=2, highlightbackground="#111")
        self.parent = parent
        self.mainWidgets()
              
    def mainWidgets(self):
        self.tableview = ttk.Frame(self)
        self.tableview.grid(row=0, column=0, sticky=N+S+E+W)

      


        def add_row():
            Label = table_text_entry.get()
            Time = (time.time() - start_time)
            Time = float(Time)
            Time = round(Time, 1)
			

            table_1.insert('', 'end', values=(Time, Label, T, P1,P2, (P1+P2)/2)) #P1, P2
            hello = ((Time, Label, T, P1,P2, (P1+P2)/2))               
            
            table_1.yview_moveto(1)
            save_table(hello)

        table_text_entry = StringVar()
        max_diameter_text = StringVar()


        def save_table(hello):
            with open((self.parent.txt_file), 'ab') as g:
                w=csv.writer(g, quoting=csv.QUOTE_ALL)
                w.writerow(hello)


        table_text_entry = StringVar()
        max_diameter_text = StringVar()


        table_2 = tk.Frame(self.tableview)
        table_2.grid(row=0, column=0, columnspan=5, sticky=N+S+E+W)

        table_label = ttk.Label(table_2, text = 'Note:')
        table_label.grid(row=0, column=0)
        table_entry = ttk.Entry(table_2, width=60, textvariable=table_text_entry )
        table_entry.grid(row=0, column=1)        
        add_button = ttk.Button(table_2, text='Add', command=add_row)
        add_button.grid(row=0, column=2)

       
        
        table_1 = ttk.Treeview(self.tableview, show= 'headings')
        table_1["columns"] = ('Time', 'Note', 'Temp', 'P', 'D1')

        table_1.column('#0', width=50)
        table_1.column('Time', width=50, stretch=True)
        table_1.column('Note', width=300)
        table_1.column('Temp', width=50)
        table_1.column('P', width=50)
        table_1.column('D1', width=50)
#        table_1.column('PAVG', width=50)

        table_1.heading('#1', text = 'Time')
        table_1.heading('#2', text = 'Note')
        table_1.heading('#3', text = 'Temp')
        table_1.heading('#4', text = 'P')
        table_1.heading('#5', text = 'D1')
#        table_1.heading('#6', text = 'PAVG')


        scrollbar = Scrollbar(self.tableview)
        scrollbar.grid(row=1,column=2, sticky=NS)
        scrollbar.config( command = table_1.yview )
        table_1.grid(row=1, column=1, sticky=N+S+E+W)


class CameraFrame(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self, parent)#, width=1000, height = 600)#, highlightthickness=2, highlightbackground="#111")
        self.parent = parent
        self.mainWidgets()
              
    def mainWidgets(self):
        # Get the max dimensions that the Canvas can be
        self.maxheight = self.parent.graphframe.winfo_height() - self.parent.tableframe.winfo_height() - self.parent.status_bar.winfo_height()
        self.maxwidth = self.parent.status_bar.winfo_width() -  self.parent.graphframe.winfo_width()
        # Set up the Canvas that we will show the image on
        self.cameraview = tk.Canvas(self, width=self.maxwidth, height=self.maxheight, background='black')
        self.cameraview.grid(row=2,column=2,sticky=N+S+E+W, pady=ypadding)

        # ROI rectangle initialisation
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        # Factors for scaling ROI to original image (which is scaled to fit canvas)
        #self.delta_width = None
        #self.delta_height = None
        #self.scale_factor = None

        # Bind events to mouse
        #self.cameraview.bind("<ButtonPress-1>",self.on_button_press)
        #self.cameraview.bind("<B1-Motion>",self.on_move_press)
        #self.cameraview.bind("<ButtonRelease-1>",self.on_button_release)


    # Define functions for mouse actions
    def on_button_press(self, event):
        if self.parent.toolbar.set_roi == True: # Only enable if we have just pressed the button
            # Delete any old ROIs
            found = event.widget.find_all()
            for iid in found:
                if event.widget.type(iid) == 'rectangle':
                    event.widget.delete(iid)
            # Create the rectangle ROI
            self.start_x = event.x
            self.start_y = event.y
            self.rect = self.cameraview.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y)

    def on_move_press(self, event):
        #Update the ROI when the mouse is dragged
        if self.parent.toolbar.set_roi == True:
            curX, curY = (event.x, event.y)
            self.cameraview.coords(self.rect, self.start_x, self.start_y, curX, curY)


    def on_button_release(self, event):
        if self.parent.toolbar.set_roi == True: # Only enable if we have just pressed the button
            self.end_x =  event.x
            self.end_y =  event.y
            self.parent.toolbar.set_roi = False
            self.parent.toolbar.ROI_checkBox.state(['selected'])
            self.parent.toolbar.ROI_is_checked.set(1)
            pass  

    def rescale_frame(self,frame):
        # Scaling a rectangle to fit inside another rectangle.
        # works out destinationwidth/sourcewidth and destinationheight/sourceheight
        # and scaled by the smaller of the two ratios
        width = frame.shape[1]
        height = frame.shape[0]

        #print "INFO"
        #print width, height
        #print self.maxwidth, self.maxheight

        widthfactor = self.maxwidth / width
        heightfactor = self.maxheight / height

        if widthfactor < heightfactor:
            self.scale_factor = widthfactor
        else:
            self.scale_factor = heightfactor

        global scale_factor
        scale_factor = self.scale_factor

        #print scale_factor

        width = int(frame.shape[1] * self.scale_factor)
        height = int(frame.shape[0] * self.scale_factor)

        #print "NEWDIMS"
        #print  width, height

        self.delta_width = int((self.maxwidth - width)/2)
        self.delta_height = int((self.maxheight - height)/2)
        a = misc.imresize(frame.astype('uint8'), [height,width])

        return a#cv2.resize(frame, (width, height), interpolation = cv2.INTER_NEAREST)
     
    def process_queue(self,img,count):

        try:
            img = img
            imgc = img#cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
          

            if self.parent.toolbar.record_flag:

                if self.parent.toolbar.snapshot_flag == True:
                    print "Snapshot pressed"
                    timenow2 = int(timenow)

                    directory = os.path.join(head, 'Snaps\\')
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    gfxPath = os.path.join(directory, '%s_t=%ss_Result SNAPSHOT.tiff' % (os.path.splitext(tail)[0],timenow2)) 
                    cv2.imwrite(gfxPath,imgc)
                    self.parent.toolbar.snapshot_flag = False
                else:
                    pass


            #Rescale the image so it doesnt take over the screen
            imgc = self.rescale_frame(imgc)
            
            #imgc = cv2.cvtColor(imgc, cv2.COLOR_BGR2RGBA)
            prevImg = Image.fromarray(imgc)
            imgtk = ImageTk.PhotoImage(image=prevImg)
            #Show the image
            self.imgtk = imgtk
            self.image_on_canvas_ = self.cameraview.create_image(self.maxwidth/2, self.maxheight/2, anchor=CENTER,image=self.imgtk)


        except:
            pass


# Class for timing processes

class TimeIt():
    from datetime import datetime
    def __init__(self):
        self.name = None
    def __call__(self, name):
        self.name = name
        return self
    def __enter__(self):
        self.tic = self.datetime.now()
        return self
    def __exit__(self,name, *args, **kwargs):
        print('process ' + self.name + ' runtime: {}'.format(self.datetime.now() - self.tic))##]]

class TimeIt2():
    from datetime import datetime
    def __init__(self):
        self.name = None
    def __call__(self, name):
        self.name = name
        return self
    def __enter__(self):
        self.tic = self.datetime.now()
        return self
    def __exit__(self,name, *args, **kwargs):
        print('process ' + self.name + ' runtime: {}'.format(self.datetime.now() - self.tic))##]]

class TimeIt3():
    from datetime import datetime
    
    def millis_interval(self,start, end):
        diff = end - start
        millis = diff.days * 24 * 60 * 60 * 1000
        millis += diff.seconds * 1000
        millis += diff.microseconds / 1000
        return millis
    def __init__(self):
        self.name = None
        self.delta_time = 0
    def __call__(self, name):
        self.name = name
        return self
    def __enter__(self):
        self.tic = self.datetime.now()
        return self
    def __exit__(self,name, *args, **kwargs):
        self.delta_time = self.millis_interval(self.tic,self.datetime.now())
        print('process ' + self.name + ' runtime: {}'.format(self.datetime.now() - self.tic))##]]
        return self

class setCamera(object):
    def __init__(self,camera_label):
        camera_label = camera_label
        self.DEVICE = None

        # Factors for scaling ROI to original image (which is scaled to fit canvas)
        self.delta_width = 0
        self.delta_height = 0
        self.scale_factor = 1
    
    def set_exp(self,exposure):
        mmc.setExposure(exposure)
        return


    def set(self, camera_label):
        # Set up the camera
        mmc.reset()
        mmc.enableStderrLog(False)
        mmc.enableDebugLog(False)
        mmc.setCircularBufferMemoryFootprint(10)# (in case of memory problems)

        if camera_label == "TIS_DCAM":  
            print "Camera Selected: ", camera_label
            try:
                DEVICE = ["TIS_DCAM","TIS_DCAM","TIS_DCAM"] #camera properties - micromanager creates these in a file
                mmc.loadDevice(*DEVICE)
                mmc.initializeDevice(DEVICE[0])
                mmc.setCameraDevice(DEVICE[0])
                mmc.setProperty(DEVICE[0], 'Binning', 1)
               # mmc.setProperty(DEVICE[0], 'DeNoise', 2)
                mmc.setExposure(exposure)
            except:
                tmb.showinfo("Warning", "Cannot connect to camera!")


        if camera_label == "Thorlabs":
            print "Camera Selected: ", camera_label
            try:
                DEVICE = ["ThorCam","ThorlabsUSBCamera","ThorCam"] #camera properties - micromanager creates these in a file
                mmc.loadDevice(*DEVICE)
                mmc.initializeDevice(DEVICE[0])
                mmc.setCameraDevice(DEVICE[0])
                try:
                    mmc.setProperty(DEVICE[0], 'Binning', "1")
                except:
                    tmb.showinfo("Warning", "Cannot set binning on camera!")
                try:
                    mmc.setProperty(DEVICE[0], 'HardwareGain', 1)
                    mmc.setProperty(DEVICE[0], 'PixelClockMHz', 25)
                    mmc.setProperty(DEVICE[0], 'PixelType', '8bit')
                except:
                    tmb.showinfo("Warning", "Cannot set something on camera!")
                
                mmc.setExposure(exposure)
            except:
                tmb.showinfo("Warning", "Cannot connect to camera!")

        if camera_label == "OpenCV":
            print "Camera Selected: ", camera_label
            print os.path.join(VTD, 'OpenCV.cfg')
            mmc.loadSystemConfiguration(os.path.join(VTD, 'OpenCV.cfg'))
            print "loaded the config file."
            print "exposure is: ", exposure
            mmc.setProperty('OpenCVgrabber', 'PixelType', '8bit')
            mmc.setExposure(exposure)
            #except:
            #    tmb.showinfo("Warning", "Cannot connect to camera!")

        if camera_label == "uManagerCam":
            print "Camera Selected: ", camera_label
            config_loaded = False
            try:
                mmc.loadSystemConfiguration('MMConfig.cfg')
                print "loaded the config file."
                config_loaded = True
            except:
                tmb.showinfo("Warning", "MMConfig.cfg not found in home directory!")

            if config_loaded:
                camera = mmc.getLoadedDevicesOfType(2)[0]
                camera_properties = mmc.getDevicePropertyNames(camera)
                print "exposure is: ", exposure
                try:
                    mmc.setProperty(mmc.getLoadedDevicesOfType(2)[0], 'PixelType', '8bit')
                except:
                    pass
                try:
                    mmc.setProperty(mmc.getLoadedDevicesOfType(2)[0], 'Binning', 1)
                    mmc.setProperty(mmc.getLoadedDevicesOfType(2)[0], 'DeNoise', 2)
                except:
                    pass
                mmc.setExposure(exposure)


        elif camera_label == "FakeCamera":
            print "Camera Selected: ", camera_label
            try:
                DEVICE = ['Camera', 'FakeCamera', 'FakeCamera'] #camera properties - micromanager creates these in a file
                mmc.loadDevice(*DEVICE)
                mmc.initializeDevice(DEVICE[0])
                mmc.setCameraDevice(DEVICE[0])
                print "exposure is: ", exposure
                mmc.setExposure(exposure)
                mmc.setProperty(DEVICE[0], 'PixelType', '8bit')
                mmc.setProperty(DEVICE[0], 'Path mask', 'SampleData\\TEST?{4.0}?.tif') #C:\\00-Code\\00 - VasoTracker\\
                # To load in a sequence 
                DEVICE2 = ['Focus', 'DemoCamera', 'DStage']
                mmc.loadDevice(*DEVICE2)
                mmc.initializeDevice(DEVICE2[0])
                mmc.setFocusDevice(DEVICE2[0])
                mmc.setProperty(DEVICE2[0], "Position", 0)
            except:
                tmb.showinfo("Warning", "Cannot connect to camera!")

        elif camera_label == "":
            tmb.showinfo("Warning", "You need to select a camera source!")
            return
        
        # TODO SET BINNING PARAMETER
        '''
        try:
            mmc.setProperty(DEVICE[0], "Binning", "2")
        except:
            pass
        '''

##################################################
## Threaded client, check if there are images and process the images in seperate threads
##################################################
class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well. We spawn a new thread for the worker (I/O).
        """
        self.timeit3 = TimeIt3()
        #threading.Thread.daemon = True # Make sure the thread terminates on exit
        self.master = master
        # Create the queue
        self.queue = Queue.Queue(  )
        self.queue2 = Queue.Queue(  )
        # Set up the GUI part
        self.gui = GuiPart(master, self.queue,self.queue2, self.endApplication)
        self.Arduino = Arduino(self)
        self.ports = self.Arduino.getports()

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        #self.thread1.deamon = True
        self.thread1.start(  )

        self.thread2 = threading.Thread(target=self.workerThread2)
        self.thread2.start(  )

        # Start the periodic call in the GUI to check if the queue contains
        # anything

        self.periodicCall(  )
        
        

        self.acqrate = None

    def sortdata(self,temppres):
        #print temppres
        #print "Length of the data = ", len(temppres)
        T = np.nan
        P = np.nan
        D1 = np.nan
        for i,data in enumerate(temppres):
            #print "length of data = ", len(data)#val = ser.readline().strip('\n\r').split(';')
            #print "this is what we are looking at",data
            if len(data) > 0:
                
                val = data[0].strip('\n\r').split(';')[:-1]
                val = [el.split(':') for el in val]

                if val[0][0] == "T1":
                    temp = float(val[0][1])
                    #print "this is a temp = ", temp
                    T = temp
                elif val[0][0] == "P":
                    pres = float(val[0][1])
                    length = float(val[1][1])
                    #print "this is a pressure = ", pres1
                    P,D1 = pres,length

        return P,D1,T

    def periodicCall(self):
        """
        Check every 10 ms if there is something new in the queue.
        """

        if self.running:
            if self.queue.qsize(  ) > 0:
                #print "Queue size = ", self.queue.qsize(  )    
                #print "Queue2 size = ", self.queue2.qsize(  )
                #with self.timeit3("Total"):  # time for optimisation
                self.gui.processIncoming()
                #print "delta = ", self.timeit3.delta_time
                #
            #else:
            #    print "nothing in the queue"
            #    self.gui.processIncoming( self.timelist, self.temp, self.pressure1, self.pressure2, self.pressure_avg )
            self.master.after(10, self.periodicCall)
        '''
        elif not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            print "brutal exit"
            sys.exit(1)
        #self.master.after(100-int(self.timeit3.delta_time)-1, self.periodicCall)
        '''


    def workerThread2(self):
        while self.running:

            temppres = self.Arduino.getData()
            P,D1,T = self.sortdata(temppres)

            try:
                binthis = self.queue2.get(0)
            except:
                pass
            self.queue2.put((P,D1,T))

            #print "Queue size = ", self.queue2.qsize(  )  
            time.sleep(0.5)


    def workerThread1(self):

    
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        '''
        self.timenow = 0
        global acqrate
        global timenow
        '''



        
        self.timenow = 0
        while self.running:
            #print "self.running = ",self.running
            if(self.queue.empty()):
                try: # Catch exception on closing the window!
                # Check if there is an image in the buffer, or an image acuisition in progress
                    #print "image remaining count = ", mmc.getRemainingImageCount()
                    if (mmc.getRemainingImageCount() > 0 or mmc.isSequenceRunning()):
                    #Check if there is an image in the buffer
                        #if mmc.getRemainingImageCount > 1:
                        #    mmc.clearCircularBuffer()
                        if mmc.getRemainingImageCount() > 0:
                            #print "remaining images: ",mmc.getRemainingImageCount()
                            global timenow
                            timenow = time.time() - start_time #Get the time
                            global acqrate
                            acqrate = 1/(timenow - self.timenow)
                            self.timenow = timenow
                            img = mmc.getLastImage()# mmc.popNextImage() #mmc.getLastImage()## Get the next image. mmc.popNextImage() #
                            #print "original shape: ", img.shape

                            self.queue.put(img) # Put the image in the queue

                            # Save raw image:
                            if self.gui.toolbar.record_is_checked.get() == 1 and self.gui.count%self.gui.rec_interval == 0:
                                timenow2 = int(timenow)
                                directory = os.path.join(head, 'RawTiff\\')
                                if not os.path.exists(directory):
                                    os.makedirs(directory)
                                gfxPath = os.path.join(directory, '%s_f=%s.tiff' % (os.path.splitext(tail)[0],str(self.gui.count).zfill(6))) 
                                skimage.io.imsave(gfxPath, img)
                            else:
                                pass
                            #time.sleep(0.090)
                        else:
                            pass
                    else:
                        pass

                except:
                    pass




















    """
     This is a function that cleans up on
    exit. It should kill all processes properly.
    """
    def endApplication(self):
        print "we are exiting"
        try:
            mmc.stopSequenceAcquisition() # stop uManager acquisition
            mmc.reset() # reset uManager
        except:
            pass
        self.running = 0
        #sys.exit()
        root.quit()
        root.destroy()


##################################################
## Splash screen
##################################################
rootsplash = tk.Tk()
rootsplash.overrideredirect(True)
width, height = rootsplash.winfo_screenwidth(), rootsplash.winfo_screenheight()

#print "Screen height is = ", height
#print "Screen width is = ", width

#Load in the splash screen image
image_file = "Bladder_SPLASH.gif" 
image = Image.open(image_file)
image2 = PhotoImage(file=image_file)

# Scale to half screen, centered
imagewidth, imageheight = image2.width(), image2.height()
newimagewidth, newimageheight = int(np.floor(width*0.5)),  int(np.floor(height*0.5))
image = image.resize((newimagewidth,newimageheight), Image.ANTIALIAS)
image = ImageTk.PhotoImage(image)

# Create and show for 3 seconds
rootsplash.geometry('%dx%d+%d+%d' % (newimagewidth, newimageheight, width/2 - newimagewidth/2, height/2 - newimageheight/2))
canvas = tk.Canvas(rootsplash, height=height, width=width, bg="darkgrey")
canvas.create_image(width/2 - newimagewidth/2, height/2 - newimageheight/2, image=image)
canvas.pack()
rootsplash.after(3000, rootsplash.destroy)
rootsplash.mainloop()


##################################################
## Main application loop
##################################################

if __name__ == "__main__":

    
# Initiate uManager
    mmc = MMCorePy.CMMCore()

    '''
# Trying to populate list of possible cameras
# Creates a weird error when failing to load a library.
# Loading in mmConfig.cfg file instead....

# Get list of available libraries:
    for libname in mmc.getDeviceAdapterNames():
        print libname

    
# Get list of available cameras:
    available_cams = []
    for lib in mmc.getDeviceAdapterNames():
        try:
            if mmc.getAvailableDeviceTypes(lib)[0] == 2:
                available_cams.append(lib)
        except:
            pass
            #print("'%s':\tThis library Won't work") % libname

    print available_cams
    '''



# Create the main window
    rand = random.Random(  )
    root = tk.Tk(  )
    root.iconbitmap('bladder_ICON.ICO')
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.wm_title("BladderTracker") #Makes the title that will appear in the top left
    root.state("zoomed")
    root.resizable(0,0) # Remove ability to resize
    #w, h = root.winfo_screenwidth(), root.winfo_screenheight() # Can set the window size using the screenwidth if we wish
    #root.geometry("%dx%d+0+0" % (w, h))
    #root.overrideredirect(1) #hides max min buttons and the big x
    #root.wm_attributes('-fullscreen', 1)
# Go go go!
    client = ThreadedClient(root)
    root.mainloop(  )


