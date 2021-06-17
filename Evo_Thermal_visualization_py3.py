#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import matplotlib.pyplot as plt 
#import time
#import progressbar
import sys
from tkinter import *
import numpy as np
import crcmod.predefined
import serial
from struct import unpack
import serial.tools.list_ports
import threading
from PIL import Image, ImageTk
import tkinter as Tk
import cv2
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from time import time



class EvoThermal(FigureCanvas):

    def __init__(self):

        ### Search for Evo Thermal port and open it ###
        ports = list(serial.tools.list_ports.comports())
        portname = None
        for p in ports:
            if ":5740" in p[2]:
                print("EvoThermal found on port " + p[0])
                portname = p[0]
        if portname is None:
            print("Sensor not found. Please Check connections.")
            exit()
        self.port = serial.Serial(
                            port=portname,  # To be adapted if using UART backboard
                            baudrate=115200, # 460800 for UART backboard
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS
                            )
        self.port.isOpen()
        self.serial_lock = threading.Lock()
        ### CRC functions ###
        self.crc32 = crcmod.predefined.mkPredefinedCrcFun('crc-32-mpeg')
        self.crc8 = crcmod.predefined.mkPredefinedCrcFun('crc-8')
        ### Activate sensor USB output ###
        self.activate_command   = (0x00, 0x52, 0x02, 0x01, 0xDF)
        self.deactivate_command = (0x00, 0x52, 0x02, 0x00, 0xD8)
        self.send_command(self.activate_command)

        #Fenêtre de visualisation
        self.activate_visualization = True
        self.window = Tk.Tk()
        self.window.wm_geometry("1000x1000")

        self.canvas_width = 600
        self.canvas_height = 600
        self.canvas2 = Tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height, bg="black")
        self.canvas2.pack(side=Tk.TOP)
        self.photo = ImageTk.PhotoImage("P")
        
        self.frames=[]
        self.start = None
        
        #print(self.photo)
        self.img = self.canvas2.create_image(300,200, image=self.photo)
        self.text2 = Tk.Label(self.window)
        self.text2.config(height=8, width=20, text='', font=("Helvetica", 22))
        self.text2.pack(side=Tk.BOTTOM)
        self.text2.config(text="Evo Thermal 33")
     


        #for i in progressbar.progressbar(range(60)):
            #time.sleep(1)
        #progressbar.pack(side=Tk.BOTTOM)
        
        
        self.MinAvg = []
        self.MaxAvg = []

        r = []
        g = []
        b = []
        with open('colormap.txt', 'r') as f:
            for i in range(256):
                x,y,z = f.readline().split(',')
                r.append(x)
                g.append(y)
                b.append(z.replace(";\n", ""))
        self.colormap = np.zeros((256, 1, 3), dtype=np.uint8)
        self.colormap[:, 0, 0] = b
        self.colormap[:, 0, 1] = g
        self.colormap[:, 0, 2] = r
        
    def create_fig(self, parent):
        root = Tk.Tk()
        root.wm_title("Embedding in Tk")

        fig = Figure(figsize=(5, 4), dpi=100)
        t = np.arange(0, 10, .01)
        fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
        
        canvas2 = FigureCanvasTkAgg(fig, master=root)  # c'est ici que tk dessine
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
        canvas3 = FigureCanvasTkAgg(fig, master=root)  # c'est ici que tk dessine
        canvas3.draw()
        canvas3.get_tk_widget().pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=1)
 

    def update_GUI(self):
        
        frame = self.rounded_array.astype(np.uint8)
        frame = cv2.applyColorMap(frame, self.colormap)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = cv2.resize(frame, (int(self.canvas_width/2), int(self.canvas_height/2)), interpolation=cv2.INTER_NEAREST)

        if len(self.frames)== 0:
            self.frames.append(frame)
            self.start = time()
            
        if time()-self.start > 60 and len(self.frames)==1:
            self.frames.append(frame)
            
            
            
        self.photo = ImageTk.PhotoImage(Image.fromarray(frame))
        self.photo1 = ImageTk.PhotoImage(Image.fromarray(self.frames[0]))
        # image en bas à gauche
        self.canvas2.create_image(150,int((self.canvas_height)/2), image=self.photo, anchor=Tk.NW)
        # image en haut à gauche
        self.canvas2.create_image(0,0, image=self.photo1, anchor=Tk.NW)
        if len(self.frames)==2:
            self.photo2 = ImageTk.PhotoImage(Image.fromarray(self.frames[1]))
            # image en haut à droite
            self.canvas2.create_image(int((self.canvas_width)/2),0, image=self.photo2, anchor=Tk.NW)
        self.window.update()

    def array_2_image(self, frame):

        thermal_img = frame
        im = Image.fromarray(np.uint8(thermal_img), mode="P")
        im = im.resize(size=(self.canvas_width, self.canvas_height), resample=Image.NEAREST)
        return im

    def get_thermals(self):
        got_frame = False
        while not got_frame:
            with self.serial_lock:
                ### Polls for header ###
                header = self.port.read(2)
                # header = unpack('H', str(header))
                header = unpack('H', header)
                if header[0] == 13:
                    ### Header received, now read rest of frame ###
                    data = self.port.read(2068)
                    ### Calculate CRC for frame (except CRC value and header) ###
                    calculatedCRC = self.crc32(data[:2064])
                    data = unpack("H" * 1034, data)
                    receivedCRC = (data[1032] & 0xFFFF ) << 16
                    receivedCRC |= data[1033] & 0xFFFF
                    TA = data[1024],
                    data = data[:1024],
                    data = np.reshape(data, (32, 32))
                    ### Compare calculated CRC to received CRC ###
                    if calculatedCRC == receivedCRC:
                        got_frame = True
                    else:
                        print("Bad CRC. Dropping frame")
        self.port.flushInput()
        ### Data is sent in dK, this converts it to celsius ###
        data = (data/10.0) - 273.15

        ### Get min/max/TA for averaging ###
        frameMin, frameMax = data.min(), data.max()
        self.MinAvg.append(frameMin)
        self.MaxAvg.append(frameMax)

        ### Need at least 10 frames for better average ###
        if len(self.MaxAvg) >= 10:
            AvgMax = sum(self.MaxAvg)/len(self.MaxAvg)
            AvgMin = sum(self.MinAvg)/len(self.MinAvg)
            ### Delete oldest insertions ###
            self.MaxAvg.pop(0)
            self.MinAvg.pop(0)
        else:
            ### Until list fills, use current frame min/max/ptat ###
            AvgMax = frameMax
            AvgMin = frameMin

        # Scale data
        data[data<=AvgMin] = AvgMin
        data[data>=AvgMax] = AvgMax
        multiplier = 255/(AvgMax - AvgMin)
        data = data - AvgMin
        data = data * multiplier

        return data

    def send_command(self, command):
        ### This avoid concurrent writes/reads of serial ###
        with self.serial_lock:
            self.port.write(command)
            ack = self.port.read(1)
            ### This loop discards buffered frames until an ACK header is reached ###
            while ord(ack) != 20:
                ack = self.port.read(1)
            else:
                ack += self.port.read(3)
            ### Check ACK crc8 ###
            crc8 = self.crc8(ack[:3])
            if crc8 == ack[3]:
                ### Check if ACK or NACK ###
                if ack[2] == 0:
                    print("Command acknowledged")
                    return True
                else:
                    print("Command not acknowledged")
                    return False
            else:
                print("Error in ACK checksum")
                return False

    def run(self):
        #on récupère frame ici
        frame = self.get_thermals()
        #print(frame)
        self.rounded_array = np.round(frame, 0)
        self.update_GUI()

    def stop(self):

        self.send_command(self.deactivate_command)
        self.port.close()
        
        


if __name__ == "__main__":
    evo = EvoThermal()
    try:
        evo.create_fig(sys.argv)
        while True:
            evo.run()
    except KeyboardInterrupt:
        evo.stop()
    finally:
        
        print("test")
        evo.window.destroy()
        evo.stop()
        
            
