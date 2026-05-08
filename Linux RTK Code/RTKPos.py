from serial import Serial
from threading import Thread, Lock, Event
from queue import Queue
from time import sleep
from pyubx2 import UBXReader
from pygnssutils import GNSSNTRIPClient
import time
from RTK import RTK
from dotenv import load_dotenv
import os
load_dotenv()


# --- Linux serial port (change to /dev/ttyACM0 if needed) ---
# Check with: ls /dev/ttyUSB* /dev/ttyACM*
# Permissions: sudo usermod -aG dialout $USER (then log out/in)
SERIAL_PORT   = "/dev/ttyUSB0"
BAUDRATE      = 115200
TIMEOUT       = 0.1


GGAMODE        = 0
GGAINT         = 10
TIMEOUT_SECS   = 60  # max seconds before giving up

lock  = Lock()
queue = Queue()
stop  = Event()


def read_gnss(ser: Serial) -> None:
    """Read and print GNSS/UBX messages from the receiver."""
    ubr = UBXReader(ser)
    while not stop.is_set():
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


def send_rtcm(ser: Serial) -> None:
    """Forward RTCM corrections from the NTRIP queue to the receiver."""
    while not stop.is_set():
        try:
            raw, _ = queue.get(timeout=1)
            with lock:
                ser.write(raw)
        except Exception:
            pass  # queue.get timeout is normal


def main() -> None:
    print(f"Opening serial port {SERIAL_PORT} @ {BAUDRATE} baud")
    with Serial(SERIAL_PORT, BAUDRATE, timeout=TIMEOUT) as ser:
        with GNSSNTRIPClient() as client:
            print("Connecting to NTRIP caster...")
            streaming = client.run(
                server=NTRIP_SERVER,
                port=NTRIP_PORT,
                mountpoint=MOUNTPOINT,
                user=NTRIP_USER,
                password=NTRIP_PASSWORD,
                ggamode=GGAMODE,
                ggainterval=GGAINT,
                output=queue,
                version="2.0",
                https=False,
            )

            if not streaming:
                print("ERROR: NTRIP connection failed — check server/credentials")
                return
            print("NTRIP connected. Waiting for RTK fix...")
            sleep(20)  # give it a moment to start streaming


            Thread(target=read_gnss, args=(ser,), daemon=True).start()
            Thread(target=send_rtcm, args=(ser,), daemon=True).start()

            deadline = time.time() + TIMEOUT_SECS
            try:
                while streaming and not stop.is_set():
                    sleep(1)
                    if time.time() > deadline:
                        print(f"Timeout after {TIMEOUT_SECS}s — stopping")
                        break
            except KeyboardInterrupt:
                print("\nInterrupted by user")
            finally:
                stop.set()
                print("Done.")


if __name__ == "__main__":
    RTKPos = RTK()
    RTKPos.run()

    #main()
