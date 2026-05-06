from serial import Serial
from threading import Thread, Lock, Event
from queue import Queue
from pyubx2 import UBXReader
from pygnssutils import GNSSNTRIPClient
import time
from dotenv import load_dotenv
import os

load_dotenv()

class RTK:
    def __init__(self, serial_port=os.getenv("SERIAL_PORT"), baudrate=115200, timeout=0.1,
                 ntrip_server=os.getenv("NTRIP_SERVER"), ntrip_port=int(os.getenv("NTRIP_PORT")), mountpoint=os.getenv("MOUNTPOINT"),
                 ntrip_user=os.getenv("NTRIP_USER"), ntrip_password=os.getenv("NTRIP_PASSWORD"), timout_secs=60,
                 ggamode=0, ggainterval=10):
        self.lock = Lock()
        self.queue = Queue()
        self.stop = Event()
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ntrip_server = ntrip_server
        self.ntrip_port = ntrip_port
        self.mountpoint = mountpoint
        self.ntrip_user = ntrip_user
        self.ntrip_password = ntrip_password
        self.timeout_secs = timout_secs
        self.ggamode = ggamode
        self.ggainterval = ggainterval
        print(f"RTK initialized with serial_port={serial_port}, ntrip_server={ntrip_server}:{ntrip_port}, mountpoint={mountpoint}", "user=" + ntrip_user, "ggamode=" + str(ggamode), "ggainterval=" + str(ggainterval), 
              "timeout_secs=" + str(timout_secs))


    def read_gnss(self, ser: Serial) -> None:
        """Read and print GNSS/UBX messages from the receiver."""
        ubr = UBXReader(ser)
        while not self.stop.is_set():
            try:
                if ser.in_waiting:
                    raw, parsed = ubr.read()
                    if parsed is None:
                        continue
                    if hasattr(parsed, "lat") and parsed.lat != 0:
                        #print("parsed is: ", parsed)
                        lat = float(parsed.lat)
                        lon = float(parsed.lon)
                        print(f"LAT: {lat:.8f}  LON: {lon:.8f}")
                    if parsed.identity == "RXM-RTCM":
                        print(f"  RTCM msg {parsed.msgType} used={parsed.msgUsed}")
                    if hasattr(parsed, "fixType"):
                        fix_names = {0:"No fix", 1:"Dead reckoning", 2:"2D", 3:"3D", 4:"GNSS+DR", 5:"Time only"}
                        print(f"  Fix: {fix_names.get(parsed.fixType, parsed.fixType)}")
            except Exception as exc:
                print(f"[read_gnss] {exc}")
    
    def send_rtcm(self, ser: Serial) -> None:
        """Forward RTCM corrections from the NTRIP queue to the receiver."""
        while not self.stop.is_set():
            try:
                raw, _ = self.queue.get(timeout=1)
                with self.lock:
                    ser.write(raw)
            except Exception:
                pass  # queue.get timeout is normal

    def run(self) -> None:
        """ Connect to the ntrip caster and start reading/writing to the serial port to determine position with RTK corrections.""" 
        print(f"Opening serial port {self.serial_port} @ {self.baudrate} baud")
        with Serial(self.serial_port, self.baudrate, timeout=self.timeout) as ser:
            with GNSSNTRIPClient() as client:
                print("Connecting to NTRIP caster...")
                streaming = client.run(
                    server=self.ntrip_server,
                    port=self.ntrip_port,
                    mountpoint=self.mountpoint,
                    user=self.ntrip_user,
                    password=self.ntrip_password,
                    output=self.queue,
                    ggamode=self.ggamode,
                    ggainterval=self.ggainterval,
                    version="2.0",
                    https=False,
                )

                if not streaming:
                    print("Failed to connect to NTRIP caster")
                    return
                print("NTRIP connected. Waiting for RTK fix...")
                read_thread = Thread(target=self.read_gnss, args=(ser,))
                send_thread = Thread(target=self.send_rtcm, args=(ser,))
                read_thread.start()
                send_thread.start()

                start_time = time.time()
                while time.time() - start_time < self.timeout_secs:
                    time.sleep(1)

                self.stop.set()
                read_thread.join()
                send_thread.join()


