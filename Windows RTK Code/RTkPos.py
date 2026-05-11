from asyncio import SelectorEventLoop
from ctypes import addressof
from serial import Serial
from threading import Thread, Lock, Event
from queue import Queue
from time import sleep
from pyubx2 import UBXReader
from pygnssutils import GNSSNTRIPClient
import math
import requests
import json
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
TIMEOUT = 0.1


GGAMODE = 0
GGAINT = 10

timeoutTimer = 60 ##timeout max seconds to determine position
    

lock = Lock()
queue = Queue()
stop = Event()




def read_gnss(ser):
    ubr = UBXReader(ser)
    while not stop.is_set():
        if ser.in_waiting:
            raw, parsed = ubr.read()
            try:
                if parsed and hasattr(parsed, "lat"):
                    print(f"LAT: {parsed.lat}, LON: {parsed.lon}, {parsed.lat}, {parsed.lon}")
                if parsed.identity == "RXM-RTCM":
                    print(f"RTCM {parsed.msgType} used: {parsed.msgUsed}")
                if hasattr(parsed, "fixType"):
                    print(f"FixType: {parsed.fixType}")
            except:
                pass


def send_rtcm(ser):
    while not stop.is_set():
        raw, _ = queue.get()
        with lock:
            ser.write(raw)



with Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT) as ser:

    with GNSSNTRIPClient() as client:
        print("Connecting to NTRIP")

        streaming = client.run(
                server=NTRIP_SERVER,
                port=NTRIP_PORT,
                mountpoint=MOUNTPOINT,
                user=NTRIP_USER,
                password=NTRIP_PASSWORD,
                ggamode=GGAMODE,
                ggainterval=GGAINT,
                output=queue,
                version="2.0",              # belangrijk voor GEODNET
                https=False,                # expliciet
        )

        if not streaming:
            print(" NTRIP connection failed stopping program")
            exit()

        print("NTRIP connected")

        Thread(target=read_gnss, args=(ser,), daemon=True).start()
        Thread(target=send_rtcm, args=(ser,), daemon=True).start()
        
        timerStart = time.time()

        while streaming and not stop.is_set():
            sleep(1)
            if (time.time() > timerStart + timeoutTimer):
                break

        stop.set()
