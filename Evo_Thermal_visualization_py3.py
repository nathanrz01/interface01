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
#from pylab import *
import matplotlib.pyplot as plt
#from collections import deque
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
#from matplotlib.animation import FuncAnimation
#from matplotlib import style
#from PyQt5.QtWidgets import QApplication, QMainWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar



class EvoThermal(FigureCanvas):

    def __init__(self):
        #super(self).__init__()
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

        ### Visualization window ###
        self.activate_visualization = True
        self.window = Tk.Tk()
        self.window.wm_geometry("1720x1720")
        # self.create_text(100,100,"Test")
        # self.canvas= Canvas(tk,width=100, height = 100, bd=0, highlightthickness=0)
        
        #canvas.pack()
        #tk.ate()upd
        self.canvas_width = 500
        self.canvas_height = 500
        self.canvas2 = Tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height)
        self.canvas2.pack(side=Tk.TOP)
        self.photo = ImageTk.PhotoImage("P")
        
        #print(self.photo)
        self.img = self.canvas2.create_image(300,200, image=self.photo)
        self.text2 = Tk.Label(self.window)
        self.text2.config(height=8, width=20, text='', font=("Helvetica", 22))
        self.text2.pack(side=Tk.BOTTOM)
        self.text2.config(text="Evo Thermal 33")
        
        self.text3 = Tk.Label(self.window)
        self.text3.config(height=8, width=20, text='', font=("Helvetica", 25))
        self.text3.pack(side=Tk.TOP)
        self.text3.config(text="  Fenêtre en temp réel")

        self.canvas3_width = 200
        self.canvas3_height = 300
        self.canvas3 = Tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height)
        self.canvas3.pack(side=Tk.TOP)
        self.photo = ImageTk.PhotoImage("P")
        self.img = self.canvas3.create_image(100,0, image=self.photo)
        
        self.canvas4_width = 200
        self.canvas4_height = 300
        self.canvas4 = Tk.Canvas(self.window, width=self.canvas_width, height=self.canvas_height)
        self.canvas4.pack(side=Tk.TOP)
        self.photo = ImageTk.PhotoImage("P")
        self.img = self.canvas4.create_image(100,200, image=self.photo)
        
        self.txt = self.canvas5.create_text(300,200, "test")
        #self.canvas.create_text(50,50,text='text')
        
        #G=graphe(g,-2,3,6)
        
        #for i in progressbar.progressbar(range(60)):
            #time.sleep(1)
        
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
        fig = Figure()
        self.axes = fig.subplots()
        FigureCanvas.__init__(self, fig)
        # self.setParent(parent)
        # self.toolbar = NavigationToolbar(self, self)
        # height = self.toolbar.height() + self.height()
        # fig.set_figheight(height)
        # self.plot()

    def plot(self):
        import sqlite3
        var_personnage = []
        var_temperature = []
        with sqlite3.connect("base.db") as con:
            cur = con.cursor()
            cur.execute("select personne, count(*) from matable group by(personne)")
            for personne, nb in cur.fetchall():
                var_personnage.append(personne)
                var_temperature.append(nb)

        people = var_personnage
        y = range(len(people))
        error=0
        self.axes.barh(y, var_temperature, xerr=error, align='center',color='red', edgecolor='green', height=0.5)
        self.axes.set_yticks(y)
        self.axes.set_yticklabels(people)
        self.axes.invert_yaxis()  # labels read top-to-bottom
        self.axes.set_xlabel('Pourcentage')
        self.axes.set_title('temperature personne')
        
        # def ADC(dt):
 
        #     #vals= adc.read_adc(1, gain=GAIN) #Lecture ADC, test sans nbr aléatoire
        #     #valeurs.appendleft(vals)
            
        #     valeurs.appendleft(randint(1, 100)) #Géneration nombres aléatoire, test sans ADC
 
 
        #     moyenne = sum(valeurs) / len(valeurs)
        #     listbox.delete(0, Tk.END)
        #     for val in valeurs:
        #         listbox.insert(Tk.END, val)
        #     moyenne_texte.set("Moyenne : {:.2f}".format(moyenne))
        #     line.set_data(range(SIZE), valeurs)
 
 
    # SIZE = 10
    # app = Tk.Tk()
    # app.wm_title("Lecture de valeurs en continu")
    # valeurs = deque([0] * SIZE, maxlen=SIZE)
     
    # moyenne_texte = Tk.StringVar()
    # moyenne_texte.set("Moyenne :")
    # moyenne_label = Tk.Label(app, textvariable=moyenne_texte, font=('', 16),
    #                      fg="sea green")
    # moyenne_label.grid(row=0, column=0, padx=5, pady=5)
 
    # listbox = Tk.Listbox(app)
    # listbox.grid(row=1, column=0, sticky=Tk.N+Tk.EW, padx=5, pady=5)
 
    # style.use("ggplot")
    # fig = Figure(figsize=(8, 5), dpi=96)
    # ax = fig.add_subplot(111)
    # ax.set_xlim(0, SIZE)
    # ax.set_ylim(0, 400)
    # ax.set_xlabel("Temps (s)")
    # ax.set_ylabel("Valeur (points)")
    # line, = ax.plot(range(len(valeurs)), valeurs, 'b-o')
    # fig.set_tight_layout(True)
 
    # canvas = FigureCanvasTkAgg(fig, master=app)
    # canvas.show()
    # canvas.get_Tk_widget().grid(row=0, column=1, rowspan=2, sticky=Tk.NSEW)
 
    # app.grid_columnconfigure(0, weight=1)
    # app.grid_columnconfigure(1, weight=1)
    # app.grid_rowconfigure(1, weight=1)
 
    # anim = FuncAnimation(fig, ADC, interval=500)
    # app.mainloop()
        
        

    def update_GUI(self):
        
        frame = self.rounded_array.astype(np.uint8)
        frame = cv2.applyColorMap(frame, self.colormap)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = cv2.resize(frame, (self.canvas_width, self.canvas_height), interpolation=cv2.INTER_NEAREST)

        self.photo = ImageTk.PhotoImage(Image.fromarray(frame))
        self.canvas2.itemconfig(self.img, image=self.photo)
        self.window.update()

    def array_2_image(self, frame):
        '''
        This function is creating an Image from numpy array
        '''
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
        ### Get frame and print it ###
        frame = self.get_thermals()
        #print(frame)
        self.rounded_array = np.round(frame, 0)
        self.update_GUI()

    def stop(self):
        ### Deactivate USB VCP output and close port ###
        self.send_command(self.deactivate_command)
        self.port.close()
        
    # def graphe():
    
    #     moy = (AvgMax + AvgMin)/2
    #     moy2 = dataglob/60
    #     ecart_type = pstdev([data1, data2, data3, data4, data5, data6])
    #     X = np.linspace(-np.pi, np.pi, 256,endpoint=True)
    #     C,S = moy, ecart_type

    #     plot(X,C)
    #     plot(X,S)

    def init_plot():
        plt.ion()
        plt.figure()
        plt.title("Test d\'acqusition", fontsize=20)
        plt.xlabel("Temps(s)", fontsize=20)
        plt.ylabel("Tension (V)", fontsize=20)
        plt.grid(True)

    def continuous_plot(moy, fx, moy2, fx2):
        plt.plot(moy, fx, 'bo', markersize=1)
        plt.plot(moy2, fx2, 'ro', markersize=1)
        plt.draw()
        


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
