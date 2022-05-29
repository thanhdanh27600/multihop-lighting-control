# %%
import math
import _thread
import serial
import serial.tools.list_ports
import time
from datetime import datetime

from IPython.core.inputsplitter import last_blank

import tkinter as tk
import tkinter.messagebox as msgbox
from PIL import Image, ImageTk

OPTIONS = [
    {
        "text": "Routing Frame",
        "value": 0
    },
    {
        "text": "Broadcast Frame",
        "value": 1
    },
    {
        "text": "Specific Destination Frame",
        "value": 2
    }
]
ROUTING_TABLE = []

next_node = 3
target_address = "\x00\x02\x17"
counter = 499
lastTime = 0
length_of_packet = 1
node_count = 0

# START TKINTER


class Frame(tk.Frame):

    def __init__(self, parent):

        super(Frame, self).__init__(parent)
        self.routingQueue_text = tk.StringVar()
        self.payload_text = tk.StringVar()
        self.dpo_text = tk.StringVar()
        self.next_node_text = tk.StringVar()
        self.overide_type = -1
        self.overide_payload = -1

        # control variable
        self.type = tk.IntVar(root, 0)

        parent.title("MULTIHOP PROTOCOL IN LIGHTING SYSTEM APPLICATION")

        LeftFrame = tk.Frame()
        # group of radiobuttons
        for i in range(len(OPTIONS)):
            print(OPTIONS[i])
            self.radio = tk.Radiobutton(LeftFrame, text=OPTIONS[i]['text'], value=OPTIONS[
                i]['value'], variable=self.type)
            self.radio.configure(background='white')
            self.radio.pack(expand=tk.YES)

        RightFrame = tk.Frame()
        tk.Label(RightFrame, text="Routing Table", bg='white').pack(
            fill=tk.BOTH, expand=1, padx=100, pady=5)
        self.routeEntry = tk.Text(
            RightFrame, width=38, height=4)
        self.routeEntry.configure(background='white')
        self.routeEntry.pack(padx=20)

        tk.Label(RightFrame, text="Payload", bg='white').pack(
            fill=tk.BOTH, expand=1, padx=100, pady=5)
        self.payloadEntry = tk.Entry(
            RightFrame, textvar=self.payload_text, width=50, name = 'payload_text')
        self.payloadEntry.configure(background='white')
        self.payloadEntry.pack(
            padx=20)

        tk.Label(RightFrame, text="DPO Field", bg='white').pack(
            fill=tk.BOTH, expand=1, padx=100, pady=5)
        self.dpoEntry = tk.Entry(RightFrame, textvar=self.dpo_text, width=50)
        self.dpoEntry.configure(background='white')
        self.dpoEntry.pack(
            padx=20)

        tk.Label(RightFrame, text="Which Cluster", bg='white').pack(
            fill=tk.BOTH, expand=1, padx=100, pady=5)
        self.clusterEntry = tk.Entry(
            RightFrame, textvar=self.next_node_text, width=50)
        self.clusterEntry.configure(background='white')
        self.clusterEntry.pack(padx=20)

        # BUTTON
        self.chooseBtn = tk.Button(RightFrame, text=' Send ',
                                   command=self.handleChooseType, relief=tk.GROOVE,  width=10)
        self.chooseBtn.configure(background='white')
        self.chooseBtn.pack(side="bottom", pady=(15, 20))

        # CONTROL BUTTON
        self.maxControlBtn = tk.Button(LeftFrame, text=' On (100%) ',
                                   command=self.handle100, relief=tk.GROOVE,  width=10)
        self.maxControlBtn.configure(background='white')
        self.maxControlBtn.pack( pady=(5, 20), expand=tk.FALSE)

        self.medControlBtn = tk.Button(LeftFrame, text=' Dim (50%) ',
                                   command=self.handle50, relief=tk.GROOVE,  width=10)
        self.medControlBtn.configure(background='white')
        self.medControlBtn.pack( pady=(5, 20))

        self.minControlBtn = tk.Button(LeftFrame, text=' Off (0%) ',
                                   command=self.handle0, relief=tk.GROOVE,  width=10)
        self.minControlBtn.configure(background='white')
        self.minControlBtn.pack(side="bottom", pady=(5, 10))


        LeftFrame.configure(background='white')
        LeftFrame.pack(side=tk.LEFT, expand=tk.TRUE, anchor=tk.N, ipady=30)
        RightFrame.configure(background='white')
        RightFrame.pack(side=tk.RIGHT)

    def handle100(self):
        self.overide_type = 1
        self.overide_payload = 255
        self.handleChooseType()

    def handle50(self):
        self.overide_type = 1
        self.overide_payload = 125
        self.handleChooseType()

    def handle0(self):
        self.overide_type = 1
        self.overide_payload = 0
        self.handleChooseType()

    def reset(self):
        self.overide_type = -1
        self.overide_payload = -1

    def handleChooseType(self):
        chooseValue = self.type.get() if self.overide_type == -1 else self.overide_type
        if chooseValue == OPTIONS[0]['value']:
            ROUTING_TABLE.clear()
            route = self.routeEntry.get("1.0", 'end-1c')
            # save to ROUTING TABLE
            for cluster in route.split('\n'):
                ROUTING_TABLE.append([int(i) for i in cluster.split(',')])

            # Iter to route all
            for eachQueue in ROUTING_TABLE:
                next_node = eachQueue[1]
                print("Next node: {}".format(next_node))
                send_msg_to_lora(encap(eachQueue[1], True, False, len(
                    eachQueue), bytearray(eachQueue), 0))
                ack_label.configure(foreground='blue')
                ack_label.setvar('ack_text', 'Status: Wait ACK')
                # try:
                #     _thread.start_new_thread(wait_ack, (ack_label,))
                #     self.reset()
                try:
                    wait_ack(ack_label)
                except:
                    print("Error: unable to start thread")

        if chooseValue == OPTIONS[1]['value']:
            print("TODO: BROADCAST FRAME")
            pl = int(self.payloadEntry.get()) if self.overide_payload == -1 else self.overide_payload

            cluster = 0 if len(ROUTING_TABLE) == 1 else int(
                self.clusterEntry.get())
            if cluster > len(ROUTING_TABLE):
                return
            next_node = ROUTING_TABLE[cluster][1]
            send_msg_to_lora(
                encap(next_node, False, True, 1, bytearray([pl]), 0))
            ack_label.configure(foreground='blue')
            ack_label.setvar('ack_text', 'Status: Wait ACK')
            try:
                _thread.start_new_thread(wait_ack, (ack_label,))
                self.reset()
            except:
                print("Error: unable to start thread")

        if chooseValue == OPTIONS[2]['value']:
            print("TODO: SPECIFIC FRAME")

            cluster = 0 if len(ROUTING_TABLE) == 1 else int(
                self.clusterEntry.get())
                
            if cluster > len(ROUTING_TABLE):
                return

            pl = int(self.payloadEntry.get())
            dpo = int(self.dpoEntry.get())
            next_node = ROUTING_TABLE[cluster][1]
            send_msg_to_lora(
                encap(next_node, False, False, 1, bytearray([pl]), dpo))
            ack_label.configure(foreground='blue')
            ack_label.setvar('ack_text', 'Status: Wait ACK')
            try:
                _thread.start_new_thread(wait_ack, (ack_label,))
                self.reset()
            except:
                print("Error: unable to start thread")


# END TKINTER


def send_msg_to_lora(frame):
    print("send:")
    print(frame)
    serialPort.write(frame)


def encap(target, RT, BC, DL, payload, DPO):
    frame = bytearray([0, target, 23])
    header = 0
    if RT:
        header = header | (1 << 7)
    if BC:
        header = header | (1 << 6)
    header = header | DL
    frame = frame + bytearray([header])
    frame = frame + payload
    if not (RT | BC):
        frame = frame + bytearray([DPO])
    return frame


def decap(frame):
    print("receive: ")
    print(frame)
    print(len(frame))
    RT = bool(frame[0] & (1 << 7))
    BC = bool(frame[0] & (1 << 6))
    DL = frame[0] & 63
    payload = frame[1:(DL+1)]
    DPO = 0
    if not (RT | BC):
        DPO = frame[-1]
    return RT, BC, DL, payload, DPO


def receive_msg_from_lora():
    frame = serialPort.readall()
    RT, BC, DL, payload, DPO = decap(frame)
    print("RT bit: {}".format(RT))
    print("BC bit: {}".format(BC))
    print("Dl field: {}".format(DL))
    print("Payload: {}".format([int(i) for i in payload]))
    print("DPO field: {}".format(DPO))
    return RT, BC


def wait_ack(ack_label):
    time_out = 0
    while True:
        if serialPort.in_waiting > 0:
            b1, b2 = receive_msg_from_lora()
            if b1 & b2:
                ack_label.configure(foreground='green')
                ack_label.setvar('ack_text', 'Status: ACK Received')

                return True
        time.sleep(0.001)
        time_out += 1
        if time_out == 1500:
            print("Time out")
            ack_label.configure(foreground='red')
            ack_label.setvar('ack_text', 'Status: ACK Error')
            return False


def read_array_from_input(n):
    result = []
    for i in range(n):
        print("Please input element {}: ".format(i))
        a = int(input())
        while a < 0:
            print("Please input element {}: ".format(i))
            a = int(input())
        result.append(a)
    return result


def read_input():
    global next_node
    while True:
        print("Please input type of frame that you want to create: (1, 2, 3)")
        print("\t 1. Routing frame")
        print("\t 2. Broadcast frame")
        print("\t 3. Specific destination frame")
        frame_type = int(input())
        checks = [1, 2, 3]
        while not (frame_type in checks):
            print("Please input type of frame that you want to create: (1, 2, 3)")
            print("\t 1. Routing frame")
            print("\t 2. Broadcast frame")
            print("\t 3. Specific destination frame")
            frame_type = int(input())

        if frame_type == 1:
            print("Please input length of routing queue: ")
            l = int(input())
            while l <= 0:
                print("Please input length of routing queue: ")
                l = int(input())
            rt_q = read_array_from_input(l)
            next_node = rt_q[1]
            print("Next node: {}".format(next_node))
            send_msg_to_lora(
                encap(rt_q[1], True, False, len(rt_q), bytearray(rt_q), 0))
            wait_ack()

        elif frame_type == 2:
            print("Please input length of payload: ")
            l = int(input())
            while l <= 0:
                print("Please input length of the payload: ")
                l = int(input())
                read_array_from_input(l)
            pl = read_array_from_input(l)  # 4
            send_msg_to_lora(
                encap(next_node, False, True, 1, bytearray([pl]), 0))
            wait_ack()

        elif frame_type == 3:
            print("Please input length of payload: ")
            l = int(input())
            while l <= 0:
                print("Please input length of payload: ")
                l = int(input())
            pl = read_array_from_input(l)
            print("Please input the DPO field ")
            d = int(input())
            while d < 1:
                print("Please input the DPO field ")
                d = int(input())
            send_msg_to_lora(encap(next_node, False, False,
                                   len(pl), bytearray(pl), d))
            wait_ack()


# while True:
#     send_msg_to_lora(encap(3, True, False, 2, bytearray([1, 3]), 0))
#     if wait_ack():
#         break
# while True:
#     send_msg_to_lora(encap(1, False, True, 1, bytearray([0]), 0))s
#     wait_ack()
#     time.sleep(10)
#     send_msg_to_lora(encap(1, False, True, 1, bytearray([100]), 0))
#     wait_ack()
#     time.sleep(10)
#     send_msg_to_lora(encap(1, False, True, 1, bytearray([255]), 0))
#     wait_ack()
#     time.sleep(10)
#     send_msg_to_lora(encap(1, False, True, 1, bytearray([0]), 0))
#     wait_ack()
#     break
# read_input()
if __name__ == "__main__":

    ports = [p.name for p in serial.tools.list_ports.comports()]
    print(ports)

    serialPort = serial.Serial(
        port=ports[0], baudrate=115200, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)

    for port in serialPort:
        print(port)

    root = tk.Tk()
    root.configure(background='white')
    root.iconphoto(False, tk.PhotoImage(file="hcmut.png"))

    # Create a photoimage object of the image in the path
    image = Image.open("hcmut.png").resize((50, 50))
    imageTk = ImageTk.PhotoImage(image)

    labelImg = tk.Label(image=imageTk, bg="white")
    labelImg.image = imageTk

    # Position image
    labelImg.pack()

    label = tk.Label(
        root, text="MULTIHOP PROTOCOL IN LIGHTING SYSTEM APPLICATION", font=("Arial", 18))
    label.configure(background='white')
    label.pack(padx=20, pady=(5, 30))

    ack_text = tk.StringVar(root, 'Status: IDLE', 'ack_text')
    ack_label = tk.Label(root, textvar=ack_text, font=("Arial", 9))
    ack_label.configure(background='white')

    ack_label.place(x=5, y=400)

    main = Frame(root)
    root.mainloop()



