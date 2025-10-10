import socket
import threading
import time
import CameraConnection as cs
import dbscript as DB
import requests
import cv2
import station1 as Station1_detection
import station2 as Station2_detection
import station_3 as Station3_detection
import station_4 as Station4_detection
from event_bus import push_result

import data as dt
from queue import Queue

import numpy as np
import os
from PIL import Image

Cam1frame = None
image2 = None
image3 = None
image4 = None

CONTROLLER_IP = "10.226.234.133"   #"192.168.0.100"  # controller IP
CONTROLLER_PORT = 8888
timeout = 5

# Global control flag
keep_running = True

# set when connected inside communicate_with_controller
sock = None

OutputFolder1 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam1output"
OutputFolder2 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam2output"
OutputFolder3 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam3output"
OutputFolder4 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam4output"

BackUpOutputFolder1 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam1output\cam1_output_backup"
BackUpOutputFolder2 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam2output\cam2_output_backup"
BackUpOutputFolder3 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam3output\cam3_output_backup"
BackUpOutputFolder4 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output\cam4_output_backup"

# --- Debounce for $C1# ---
# We’ll ignore repeated C1 triggers that arrive within this time window.
# Default: 0.20 s (200 ms). You can override via dt.python_parameters["S1"]["C1_DEBOUNCE_MS"] or ["C1_DEBOUNCE_SEC"].
last_c1_ts = 0.0  # last time we actually accepted (processed) a C1

def _get_c1_debounce_sec() -> float:
    s1 = dt.python_parameters.get("S1", {}) or {}
    # allow ms or sec in your config
    val_ms = s1.get("C1_DEBOUNCE_MS") or s1.get("C1_DEBOUNCEMS")
    if val_ms is not None:
        try:
            return float(val_ms) / 1000.0
        except Exception:
            pass
    val_sec = s1.get("C1_DEBOUNCE_SEC") or s1.get("C1_DEBOUNCE")
    if val_sec is not None:
        try:
            return float(val_sec)
        except Exception:
            pass
    return 0.20  # default 200 ms


# Socket send/recv lock
sock_lock = threading.Lock()

def send_until_ack(sock, cmd: str, ack_token: str, *,
                   timeout_per_try: float = 1.0,
                   resend_every: float = 0.25,
                   max_wait: float | None = None) -> bool:
    """
    Keep sending `cmd` until we see `ack_token` in the rx stream.
    Returns True when ACK is seen, False if `keep_running` goes False or max_wait exceeded.

    Notes:
    - Uses a lock so other threads don't interleave on the same socket.
    - Resends every `resend_every` seconds while waiting up to `timeout_per_try` for each try.
    - If `max_wait` is None, it will retry indefinitely (until keep_running turns False).
    """
    global keep_running
    end_time = time.time() + max_wait if max_wait else None

    with sock_lock:
        while keep_running and (end_time is None or time.time() < end_time):
            try:
                # Send once
                if not cmd.endswith("\r\n"):
                    wire = (cmd + "\r\n").encode()
                else:
                    wire = cmd.encode()
                print(f"📤 Sending {cmd.strip()} (expect {ack_token})")
                sock.sendall(wire)

                # Try to receive ack within timeout_per_try
                start_try = time.time()
                buffer = ""
                while keep_running and (time.time() - start_try) < timeout_per_try:
                    try:
                        data = sock.recv(1024).decode(errors="ignore")
                        if not data:
                            # peer closed
                            break
                        buffer += data
                        if ack_token in buffer:
                            print(f"✅ ACK matched: {ack_token}")
                            return True
                    except socket.timeout:
                        # keep looping this try
                        continue
                    except Exception as e:
                        print(f"❌ recv error while waiting for {ack_token}: {e}")
                        break  # exit inner; we will resend
            except Exception as e:
                print(f"❌ send error for {cmd.strip()}: {e}")

            # No ack this try: short delay before resending (retry back-off)
            time.sleep(resend_every)

    print(f"⚠️ send_until_ack aborted for {cmd.strip()} (stopped or timed out)")
    return False

# Stop coordination
stop_event = threading.Event()

def wait_until(deadline_monotonic: float):
    """Sleep in small chunks so we can exit early when STOP arrives."""
    while keep_running and not stop_event.is_set():
        remaining = deadline_monotonic - time.monotonic()
        if remaining <= 0:
            return
        # sleep in small slices so STOP can interrupt quickly
        time.sleep(min(remaining, 0.05))

def _get_delay_for_station(n: int) -> float:
    smap = dt.python_parameters.get(f"S{n}", {}) or {}
    raw = (
        smap.get(f"CAM{n}DELAY")
        or smap.get(f"Delay_Cam{n}")
        or 0
    )
    try:
        return float(raw)
    except Exception:
        return 0.0

def _delays():
    # seconds as floats; S1 is usually 0 (first station)
    return (
        _get_delay_for_station(1),
        _get_delay_for_station(2),
        _get_delay_for_station(3),
        _get_delay_for_station(4),
    )

def build_command_sequence(param_dict):
    # Normalize keys
    param_dict = {key.replace(" ", ""): value for key, value in param_dict.items()}

    command_list = []

    camera_enabled = {
        "S1": str(param_dict.get("S1:Camera1Enable", "1")) == "1",
        "S2": str(param_dict.get("S2:Camera2Enable", "1")) == "1",
        "S3": str(param_dict.get("S3:Camera3Enable", "1")) == "1",
        "S4": str(param_dict.get("S4:Camera4Enable", "1")) == "1",
    }

    # Define a fixed order for commands
    ordered_keys = [
        # Enable flags (always included; mapping may skip them if PLC doesn't expect)
        "S1:Camera1Enable",
        "S2:Camera2Enable",
        "S3:Camera3Enable",
        "S4:Camera4Enable",
        # Station 1
        "S1:CameraVerticalMoment",
        "S1:LightIntensity",
        "S1:CameraExposure",
        "S1:CameraGain",
        "S1:CapturingDelay",
        # Station 2
        "S2:CameraLateralMoment",
        "S2:LightIntensity",
        "S2:CameraExposure",
        "S2:CameraGain",
        "S2:CapturingDelay",
        # Station 3
        "S3:CameraVerticalMoment",
        "S3:LightIntensity",
        "S3:CameraExposure",
        "S3:CameraGain",
        "S3:CapturingDelay",
        # Station 4
        "S4:CameraVerticalMoment",
        "S4:LightIntensity",
        "S4:CameraExposure",
        "S4:CameraGain",
        "S4:CapturingDelay",
        # Speed parameters
        "SP:IndexingSpeed",
        "SP:VibratorSpeed",
        "SP:Conveyor1Speed",
        "SP:Conveyor2Speed",
        "SP:PartPushSpeed",
    ]

    mapping = {
        # "S1:Camera1Enable": "$CAM1_ENB={value}#",
        # "S2:Camera2Enable": "$CAM2_ENB={value}#",
        # "S3:Camera3Enable": "$CAM3_ENB={value}#",
        # "S4:Camera4Enable": "$CAM4_ENB={value}#",
        "S1:CameraVerticalMoment": "$CAM1_HT={value}#",
        "S1:LightIntensity": "$ST1_LIT_INT={value}#",
        # "S1:CameraExposure": "$CAM1_EXP={value}#",
        # "S1:CameraGain": "$CAM1_GAIN={value}#",
        # "S1:CapturingDelay": "$CAM1_CAP_DELAY={value}#",
        # "S2:CameraLateralMoment": "$CAM2_LAT_MT={value}#",
        "S2:LightIntensity": "$ST2_LIT_INT={value}#",
        # "S2:CameraExposure": "$CAM2_EXP={value}#",
        # "S2:CameraGain": "$CAM2_GAIN={value}#",
        # "S2:CapturingDelay": "$CAM2_CAP_DELAY={value}#",
        # "S3:CameraVerticalMoment": "$CAM3_VERT_MT={value}#",
        "S3:LightIntensity": "$ST3_LIT_INT={value}#",
        # "S3:CameraExposure": "$CAM3_EXP={value}#",
        # "S3:CameraGain": "$CAM3_GAIN={value}#",
        # "S3:CapturingDelay": "$CAM3_CAP_DELAY={value}#",
        # "S4:CameraVerticalMoment": "$CAM4_VERT_MT={value}#",
        "S4:LightIntensity": "$ST4_LIT_INT={value}#",
        # "S4:CameraExposure": "$CAM4_EXP={value}#",
        # "S4:CameraGain": "$CAM4_GAIN={value}#",
        # "S4:CapturingDelay": "$CAM4_CAP_DELAY={value}#",
        "SP:IndexingSpeed": "$INDX_SPD={value}#",
        # "SP:VibratorSpeed": "$VIBRTR_SPD={value}#",
        "SP:Conveyor1Speed": "$CONV1_SPD={value}#",
        "SP:Conveyor2Speed": "$CONV2_SPD={value}#",
        # "SP:PartPushSpeed": "$PRT_PUSH_MT_SPD={value}#",
    }

    for key in ordered_keys:
        if key not in param_dict:
            continue

        if key.startswith("S1:") and not camera_enabled["S1"]:
            continue
        if key.startswith("S2:") and not camera_enabled["S2"]:
            continue
        if key.startswith("S3:") and not camera_enabled["S3"]:
            continue
        if key.startswith("S4:") and not camera_enabled["S4"]:
            continue

        if key in mapping:
            value = param_dict[key]
            command = mapping[key].format(value=value)
            ack = "$ACK_" + command.strip("$#\r\n").split("=")[0]
            command_list.append((command, ack))

    print(f"✅ Command list built with {len(command_list)} commands")
    return command_list

def communicate_with_controller(param_dict):
    global sock
    global keep_running
    keep_running = True

    enabled = {
        "C1": str(param_dict.get("S1:Camera1Enable", "1")) == "1",
        "C2": str(param_dict.get("S2:Camera2Enable", "1")) == "1",
        "C3": str(param_dict.get("S3:Camera3Enable", "1")) == "1",
        "C4": str(param_dict.get("S4:Camera4Enable", "1")) == "1",
    }
    active_stations = [c for c in ["C1", "C2", "C3", "C4"] if enabled[c]]
    print(f"🔧 Active stations: {active_stations}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((CONTROLLER_IP, CONTROLLER_PORT))
            print("✅ Connected to controller.")
            globals()['sock'] = sock  # expose connected socket to other functions/threads

            # === Step 1: Build & send init commands (retry until ACK) ===
            command_list = build_command_sequence(param_dict)
            for command, ack in command_list:
                ok = send_until_ack(
                    sock,
                    command,
                    ack_token=ack,
                    timeout_per_try=timeout,
                    resend_every=0.2
                )
                if not ok:
                    print(f"❌ Failed to get ACK for {command.strip()} — aborting start.")
                    return
            print("✅ All commands acknowledged.")

            # === Step 2: Start request ($STR#) with retry-until-ACK ===
            print("📤 Sending $STR# to start process")
            if not send_until_ack(
                sock,
                "$STR#",
                "$ACK_STR#",
                timeout_per_try=timeout,
                resend_every=0.2
            ):
                print("❌ Could not get $ACK_STR# — aborting.")
                return
            print("✅ Received $ACK_STR")

            # === Step 3: Connect Cameras ===
            print("🔗 Connecting cameras...")
            ConnectCam(param_dict)

            # === Step 4: Main receive loop ===
            while keep_running:
                try:
                    with sock_lock:
                        data = sock.recv(1024).decode(errors="ignore")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving data: {e}")
                    break

                if not data:
                    continue
                data = data.strip()
                if not data:
                    continue
                print(f"📥 Received: {data}")

                # Controller -> UI triggers and commands
                if "$C1#" in data:
                    # Always ACK quickly so PLC/controller doesn't keep resending
                    try:
                        sock.sendall("$ACK_C1#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_C1#: {e}")

                    # ---- Debounce logic ----
                    # If multiple $C1# arrive within a few milliseconds, accept only the first.
                    # Anything inside the debounce window is ignored (but still ACKed above).
                    now = time.monotonic()
                    debounce = _get_c1_debounce_sec()

                    # Read/update a global "last accepted" timestamp
                    global last_c1_ts
                    if (now - last_c1_ts) < debounce:
                        print(f"🛑 Ignored duplicate C1 (only {now - last_c1_ts:.3f}s since last). Debounce={debounce:.3f}s")
                        continue  # do NOT start a new part pipeline

                    # This C1 is accepted; remember its time
                    last_c1_ts = now

                    print("✅ C1 accepted — starting per-part pipeline")

                    # Optional small pre-delay if you want (kept from your code)
                    # delay_time = 0.8
                    # if delay_time > 0:
                    #     print(f"⏳ Waiting {delay_time} sec before triggering per-part pipeline...")
                    #     wait_until(time.monotonic() + delay_time)
                    #     if not keep_running or stop_event.is_set():
                    #         continue

                    stop_event.clear()
                    threading.Thread(
                        target=run_part_pipeline,
                        args=(active_stations, sock),
                        daemon=True
                    ).start()
                    continue

                if "$C2#" in data:
                    try:
                        sock.sendall("$ACK_C2#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_C2#: {e}")
                    # (If you ever decide to start cam2 directly, do it here)
                    continue

                if "$C3#" in data:
                    try:
                        sock.sendall("$ACK_C3#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_C3#: {e}")
                    continue

                if "$C4#" in data:
                    try:
                        sock.sendall("$ACK_C4#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_C4#: {e}")
                    continue

                if "$STR#" in data:
                    try:
                        sock.sendall("$ACK_STR#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_STR#: {e}")
                    continue

                if "$STP#" in data:
                    try:
                        sock.sendall("$ACK_STP#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_STP#: {e}")
                    stop_event.set()
                    keep_running = False
                    cs.camera_disconnect()
                    print("🛑 Stop received from controller.")
                    break

                if "$OK_BIN_FULL#" in data:
                    try:
                        sock.sendall("$ACK_OK_BIN_FULL#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_OK_BIN_FULL#: {e}")
                    continue

                if "$NOK_BIN_FULL#" in data:
                    try:
                        sock.sendall("$ACK_NOK_BIN_FULL#\r\n".encode())
                    except Exception as e:
                        print(f"❌ Failed to send $ACK_NOK_BIN_FULL#: {e}")
                    continue

    except Exception as e:
        print(f"❌ Error in communicate_with_controller: {e}")

def _send_raw_noack(s, msg: str):
    """Send one line without waiting for ACK. Safe even if peer is slow."""
    try:
        if not msg.endswith("\r\n"):
            msg = msg + "\r\n"
        s.sendall(msg.encode())
        print(f"📤 Sent (no-ACK): {msg.strip()}")
    except Exception as e:
        print(f"❌ send error (no-ACK) for {msg.strip()}: {e}")

def _force_close_socket():
    """Force-close the global socket safely."""
    global sock
    try:
        with sock_lock:
            if sock is not None:
                try:
                    # Try to shutdown nicely first
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass  # ignore if already closed / not connected
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None
                print("🔌 TCP socket forcibly closed.")
    except Exception as e:
        print(f"❌ Error while force-closing socket: {e}")


def stop_process():
    """
    HARD STOP:
    1) Flip local flags (STOP everything here).
    2) Best-effort: send 2–3 STP quickly on the current socket (no ACK wait).
    3) Regardless of ACK, FORCE-CLOSE the TCP connection.
    4) Optional: try a new short-lived connection to send 1 more STP, then close.
    """
    global sock, keep_running
    print("🛑 Stop requested")

    # 1) Flip local flags first so all loops exit quickly
    stop_event.set()
    keep_running = False
    cs.camera_disconnect()  # disconnect cameras immediately

    # 2) Best-effort STP spam on existing socket (no ACK wait)
    try:
        with sock_lock:
            if sock is not None:
                for i in range(3):           # send 3 times fast
                    _send_raw_noack(sock, "$STP#")
                    time.sleep(0.15)        # small gap between sends (150 ms)
    except Exception as e:
        print(f"❌ Error while blasting STP on existing socket: {e}")

    # 3) FORCE-CLOSE regardless of ACK
    _force_close_socket()

    # 4) Optional: one last STP via a fresh, short-lived connection (best-effort)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.settimeout(1.0)
            s2.connect((CONTROLLER_IP, CONTROLLER_PORT))
            print("🛑 Fallback connect just to send final STP")
            _send_raw_noack(s2, "$STP#")
            time.sleep(0.1)
            _send_raw_noack(s2, "$STP#")
            # not waiting for ACK; socket auto-closes by context manager
    except Exception as e:
        print(f"⚠️ Fallback STP attempt failed (safe to ignore): {e}")

    print("✅ Stop sequence completed (socket closed regardless of ACK).")

def C_TriggeredProcess(cam_id, station, active_stations, ctx, result_queues):
    # launch capture+process for this station in its own thread
    t = threading.Thread(
        target=Capture_Prosses_Triggerflask,
        args=(cam_id, station, active_stations, ctx, result_queues),
        daemon=True
    )
    t.start()

def Capture_Prosses_Triggerflask(cam_id, station, active_stations, ctx, result_queues):
    if cam_id == "cam1":
        dt.Frames["Cam1frame"] = cs.capture_image_1()
        ReadPythonResult(
            cam_id="cam1", station=station, active_stations=active_stations,
            ctx=ctx, result_queues=result_queues
        )
        trigger_flask_camera(cam_id)

    elif cam_id == "cam2":
        dt.Frames["Cam2frame"] = cs.capture_image_2()
        ReadPythonResult(
            cam_id="cam2", station=station, active_stations=active_stations,
            ctx=ctx, result_queues=result_queues
        )
        trigger_flask_camera(cam_id)

    elif cam_id == "cam3":
        dt.Frames["Cam3frame"] = cs.capture_image_3()
        ReadPythonResult(
            cam_id="cam3", station=station, active_stations=active_stations,
            ctx=ctx, result_queues=result_queues
        )
        trigger_flask_camera(cam_id)

    elif cam_id == "cam4":
        dt.Frames["Cam4frame"] = cs.capture_image_4()
        ReadPythonResult(
            cam_id="cam4", station=station, active_stations=active_stations,
            ctx=ctx, result_queues=result_queues
        )
        # trigger_flask_camera(cam_id)

def ReadPythonResult(cam_id, station, active_stations, ctx, result_queues):
    part_name = "PISTON"
    subpart_name = ""
    part_id = "P1S1"
    date_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    supplier_name = "S1"
    invoice_no = "I1"

    cam_num = int(cam_id[-1])

    # 1️⃣ If camera is disabled, skip it and pass an OK token
    if not getattr(cs, f"isConnectedCamera{cam_num}")():
        print(f"{cam_id.upper()} is disabled. Passing OK to next stage.")
        result_queues[station].put(True)
        return

    # Initialize result variables
    result_ok = False

    # 2️⃣ Run detection and gather results
    if cam_id == "cam1":

        DB.load_python_parameters(dt.StaticData["PartID"])
        params = dt.python_parameters["S1"]
        print(params)

        # Unpack from Station1
        (
            resultType,
            result,
            ID,
            IDstatus,
            OD,
            ODstatus,
            Concentricity,
            ConcentricityStatus,
            FlashDefect,
            DefectPosition,
            OrificeDiameter,
            OrificeStatus,
            dim_err,
        ) = Station1_detection.main(
            part=dt.StaticData["PartName"],
            subpart=dt.StaticData["SubPartName"],
            frame=dt.Frames["Cam1frame"],
            id_min=params["IDMIN"],
            id_max=params["IDMAX"],
            od_min=params["ODMIN"],
            od_max=params["ODMAX"],
            concentricity_max=params["CONCENTRICITY"],
            orifice_min=params["ORIFICEMIN"],
            orifice_max=params["ORIFICEMAX"],
            threshold_id2=params["THRESHOLDID2"],
            threshold_id3=params["THRESHOLDID3"],
            threshold_od2=params["THRESHOLDOD2"],
            threshold_od3=params["THRESHOLDOD3"],
            pixel_to_micron=params["PIXELTOMICRON"],
            pixel_to_micron_id=params["PIXELTOMICRON_ID"],
            pixel_to_micron_od=params["PIXELTOMICRON_OD"],
            output_folder=OutputFolder1,
            backup_output_folder=BackUpOutputFolder1
        )
        part = dt.StaticData["PartName"]
        subpart = dt.StaticData["SubPartName"]

        print(
            f"part={part}, subpart={subpart},  "
            f'id_min={params["IDMIN"]}, id_max={params["IDMAX"]}, '
            f'od_min={params["ODMIN"]}, od_max={params["ODMAX"]}, '
            f'concentricity_max={params["CONCENTRICITY"]}, '
            f'orifice_min={params["ORIFICEMIN"]}, orifice_max={params["ORIFICEMAX"]}, '
            f'threshold_id2={params["THRESHOLDID2"]}, threshold_id3={params["THRESHOLDID3"]}, '
            f'threshold_od2={params["THRESHOLDOD2"]}, threshold_od3={params["THRESHOLDOD3"]}, '
            f'pixel_to_micron={params["PIXELTOMICRON"]}, '
            f'pixel_to_micron_id={params["PIXELTOMICRON_ID"]}, '
            f'pixel_to_micron_od={params["PIXELTOMICRON_OD"]}, '
            f"output_folder={OutputFolder1}"
        )

        result_ok = (result == "OK")
        flash_id = "OK" if result_ok else "NOK"
        flash_od = "OK" if result_ok else "NOK"

        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {"flash_id": flash_id, "flash_od": flash_od},
            "dimensions": {
                "id": ID if "ID" in locals() else "NA",
                "od": OD if "OD" in locals() else "NA",
                "orifice": OrificeDiameter if "OrificeDiameter" in locals() else "NA",
                "Concentricity": Concentricity if "Concentricity" in locals() else "NA",
            },
        }
        push_result(cam_id, payload)

        if not ctx.get("current_part_inserted", False):
            ctx["inserted_s_no"] = DB.insert_workpartdetail_1st_Station(
                date_time,
                part_name,
                subpart_name,
                part_id,
                station,
                ID,
                OD,
                OrificeDiameter,
                Concentricity,
                ConcentricityStatus,
                IDstatus,
                ODstatus,
                "NA",
                "NA",
                "NA",  # thickness
                "NA",
                "NA",
                "NA",  # top burr
                "NA",
                "NA",
                "NA",  # bottom burr
                supplier_name,
                invoice_no,
            )
            ctx["current_part_inserted"] = True

    elif cam_id == "cam2":
        (
            resultType,
            result,            # "OK" / "NOK"
            error,             # general error string (if any)
            thickness,         # numeric or computed thickness value
            thickness_error,   # description for thickness failure
            FlashDefect,       # (keep if you use it elsewhere)
            outputPath,        # path to saved cam2 image
        ) = Station2_detection.main(
            part=dt.StaticData["PartName"],
            subpart=dt.StaticData["SubPartName"],
            frame=dt.Frames["Cam2frame"],
            thick_min=dt.python_parameters["S2"]["THICKNESSMIN"],
            thick_max=dt.python_parameters["S2"]["THICKNESSMAX"],
            pixel_to_micron=dt.python_parameters["S2"]["PIXELTOMICRON"],
            output_folder=OutputFolder2,
            min_thresh=dt.python_parameters["S2"]["MINTHRESH"],
            max_thresh=dt.python_parameters["S2"]["MAXTHRESH"],
            backup_output_folder=BackUpOutputFolder2
        )

        print(
            f"Station 2 ResultType: {resultType}, Result: {result}, "
            f"Thickness: {thickness}, Error: {thickness_error}, OutputPath: {outputPath}"
        )

        result_ok = (result == "OK")
        thickness_status = "OK" if result_ok else "NOK"

        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {"vertical_flash": thickness_status},
            "dimensions": {"thickness": thickness},
        }
        print("Sending payload:", payload)
        push_result(cam_id, payload)

        if not ctx.get("current_part_inserted", False):
            ctx["inserted_s_no"] = DB.insert_workpartdetail_1st_Station(
                date_time,
                part_name,
                subpart_name,
                part_id,
                station,
                # S1 placeholders
                "NA", "NA", "NA", "NA", "NA", "NA", "NA",
                # S2
                outputPath,          # Thickness_Cam_Image
                thickness_status,    # Thickness_Result (OK/NOK)
                thickness_error,     # Thickness_Cam_Error_Description
                # S3 placeholders
                "NA", "NA", "NA",
                # S4 placeholders
                "NA", "NA", "NA",
                supplier_name,
                invoice_no,
            )
            ctx["current_part_inserted"] = True
        else:
            DB.update_workpartdetail_2nd_Station(
                ctx["inserted_s_no"],
                station,
                thickness_status,
                thickness_error,
            )

    elif cam_id == "cam3":
        res = Station3_detection.main(
            part=dt.StaticData["PartName"],
            subpart=dt.StaticData["SubPartName"],
            frame=dt.Frames["Cam3frame"],

            # ---- ID (inner) params ----
            ID2_OFFSET_ID=dt.python_parameters["S3"]["ID2_OFFSET"],
            HIGHLIGHT_SIZE_ID=dt.python_parameters["S3"]["HIGHLIGHT_SIZE"],
            ID_BURR_MIN_AREA=dt.python_parameters["S3"]["id_BURR_MIN_AREA"],
            ID_BURR_MAX_AREA=dt.python_parameters["S3"]["id_BURR_MAX_AREA"],
            ID_BURR_MIN_PERIMETER=dt.python_parameters["S3"]["id_BURR_MIN_PERIMETER"],
            ID_BURR_MAX_PERIMETER=dt.python_parameters["S3"]["id_BURR_MAX_PERIMETER"],

            # ---- OD (outer) params ----
            ID2_OFFSET_OD=dt.python_parameters["S3"]["ID2_OFFSET_OD3"],
            HIGHLIGHT_SIZE_OD=dt.python_parameters["S3"]["HIGHLIGHT_SIZE_OD3"],
            OD_BURR_MIN_AREA=dt.python_parameters["S3"]["OD_BURR_MIN_AREA3"],
            OD_BURR_MAX_AREA=dt.python_parameters["S3"]["OD_BURR_MAX_AREA3"],
            OD_BURR_MIN_PERIMETER=dt.python_parameters["S3"]["OD_BURR_MIN_PERIMETER3"],
            OD_BURR_MAX_PERIMETER=dt.python_parameters["S3"]["OD_BURR_MAX_PERIMETER3"],

            # ---- contour selection ----
            min_id_area=dt.python_parameters["S3"]["min_id_area3"],
            max_id_area=dt.python_parameters["S3"]["max_id_area3"],
            min_od_area=dt.python_parameters["S3"]["min_od_area3"],
            max_od_area=dt.python_parameters["S3"]["max_od_area3"],
            min_circularity=dt.python_parameters["S3"]["min_circularity3"],
            max_circularity=dt.python_parameters["S3"]["max_circularity3"],
            min_aspect_ratio=dt.python_parameters["S3"]["min_aspect_ratio3"],
            max_aspect_ratio=dt.python_parameters["S3"]["max_aspect_ratio3"],

            output_folder=OutputFolder3,
            backup_output_folder=BackUpOutputFolder3
        )

        id_status = (res.get("id") or {}).get("status", "NOK")
        od_status = (res.get("od") or {}).get("status", "NOK")
        id_count = (res.get("id") or {}).get("count", 0)
        od_count = (res.get("od") or {}).get("count", 0)

        result_ok = (id_status == "OK" and od_status == "OK")
        top_burr_status = "OK" if result_ok else "NOK"

        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {"top_burr": top_burr_status},
            "dimensions": {
                "id_burr_count": id_count,
                "od_burr_count": od_count
            }
        }
        push_result(cam_id, payload)

        if not ctx.get("current_part_inserted", False):
            ctx["inserted_s_no"] = DB.insert_workpartdetail_1st_Station(
                date_time, part_name, subpart_name, part_id, station,
                # S1 placeholders
                "NA", "NA", "NA", "NA", "NA", "NA", "NA",
                # S2 placeholders
                "NA", "NA", "NA",
                # S3 placeholders (adjust to your schema once finalized)
                "NA", "NA", "NA",
                # S4 placeholders
                "NA", "NA", "NA",
                supplier_name, invoice_no
            )
            ctx["current_part_inserted"] = True
        else:
            DB.update_workpartdetail_3rd_Station(
                "OK" if result_ok else "NOK",
                None,                # Error (if you decide to surface one)
                top_burr_status,     # Burr status summary
                id_count + od_count  # Total burr count (example)
            )

    elif cam_id == "cam4":
        res = Station4_detection.main(
            part=dt.StaticData["PartName"],
            subpart=dt.StaticData["SubPartName"],
            frame=dt.Frames["Cam4frame"],

            # ---- ID (inner) params ----
            ID2_OFFSET_ID=dt.python_parameters["S4"]["ID4_OFFSET"],
            HIGHLIGHT_SIZE_ID=dt.python_parameters["S4"]["HIGHLIGHT_SIZE"],
            ID_BURR_MIN_AREA=dt.python_parameters["S4"]["id_BURR_MIN_AREA"],
            ID_BURR_MAX_AREA=dt.python_parameters["S4"]["id_BURR_MAX_AREA"],
            ID_BURR_MIN_PERIMETER=dt.python_parameters["S4"]["id_BURR_MIN_PERIMETER"],
            ID_BURR_MAX_PERIMETER=dt.python_parameters["S4"]["id_BURR_MAX_PERIMETER"],

            # ---- OD (outer) params ----
            ID2_OFFSET_OD=dt.python_parameters["S4"]["ID2_OFFSET_OD4"],
            HIGHLIGHT_SIZE_OD=dt.python_parameters["S4"]["HIGHLIGHT_SIZE_OD4"],
            OD_BURR_MIN_AREA=dt.python_parameters["S4"]["OD_BURR_MIN_AREA4"],
            OD_BURR_MAX_AREA=dt.python_parameters["S4"]["OD_BURR_MAX_AREA4"],
            OD_BURR_MIN_PERIMETER=dt.python_parameters["S4"]["OD_BURR_MIN_PERIMETER4"],
            OD_BURR_MAX_PERIMETER=dt.python_parameters["S4"]["OD_BURR_MAX_PERIMETER4"],

            # ---- contour selection ----
            min_id_area=dt.python_parameters["S4"]["min_id_area4"],
            max_id_area=dt.python_parameters["S4"]["max_id_area4"],
            min_od_area=dt.python_parameters["S4"]["min_od_area4"],
            max_od_area=dt.python_parameters["S4"]["max_od_area4"],
            min_circularity=dt.python_parameters["S4"]["min_circularity4"],
            max_circularity=dt.python_parameters["S4"]["max_circularity4"],
            min_aspect_ratio=dt.python_parameters["S4"]["min_aspect_ratio4"],
            max_aspect_ratio=dt.python_parameters["S4"]["max_aspect_ratio4"],

            output_folder=OutputFolder4,
            backup_output_folder=BackUpOutputFolder4
        )

        id_status = (res.get("id") or {}).get("status", "NOK")
        od_status = (res.get("od") or {}).get("status", "NOK")
        id_count  = (res.get("id") or {}).get("count", 0)
        od_count  = (res.get("od") or {}).get("count", 0)

        result_ok = (id_status == "OK" and od_status == "OK")
        bottom_burr = "OK" if result_ok else "NOK"

        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {"bottom_burr": bottom_burr},
            "dimensions": {
                "id_burr_count": id_count,
                "od_burr_count": od_count,
            },
        }
        push_result(cam_id, payload)

        if not ctx.get("current_part_inserted", False):
            ctx["inserted_s_no"] = DB.insert_workpartdetail_1st_Station(
                date_time, part_name, subpart_name, part_id, station,
                # S1
                "NA","NA","NA","NA","NA","NA","NA",
                # S2
                "NA","NA","NA",
                # S3
                "NA","NA","NA",
                # S4
                "NA","NA","NA",
                supplier_name, invoice_no
            )
            ctx["current_part_inserted"] = True
        else:
            DB.update_workpartdetail_4th_Station(
                "OK" if result_ok else "NOK",
                None,               # Error string if you expose one
                bottom_burr,        # Burr status summary
                id_count + od_count # Example count aggregation
            )
        # ✅ Show image in UI immediately (DO NOT wait for PLC ACK)
        trigger_flask_camera("cam4")

        # Final OK/NOK only if C4 is the last active station
        if station == active_stations[-1]:
            try:
                code = "$OK#" if result_ok else "$NOK#"
                DB.update_defect_count("OK" if result_ok else "NOK")
                ack_token = "$ACK_" + code.strip("$#") + "#"
                ok = send_until_ack(
                    sock,
                    code,
                    ack_token,
                    # timeout_per_try=timeout,
                    # resend_every=0.2,
                    # max_wait=5*timeout
                    timeout_per_try=1.0,
                    resend_every=0.1,
                    max_wait=10.0
                )
                if ok:
                    print(f"Sent: {code} (ACK received)")
                else:
                    print(f"⚠️ Sent: {code} (no ACK)")
            except Exception as e:
                print(f"❌ Error sending final result: {e}")

    # 3️⃣ Put result in THIS part's queue for THIS station
    result_queues[station].put(result_ok)
    print(f"📝 Station {station} result: {result_ok}")

def trigger_flask_camera(cam_id):
    try:
        print(f"🔔 Notifying Flask to show {cam_id} image")
        response = requests.post(f"http://127.0.0.1:9000/trigger/{cam_id}")
        print("Flask Response:", response.status_code)
    except Exception as e:
        print("Error triggering Flask:", e)

def ConnectCam(param_dict):
    # Normalize keys
    param_dict = {key.replace(" ", ""): value for key, value in param_dict.items()}

    camera_enabled = {
        "cam1": str(param_dict.get("S1:Camera1Enable", "1")) == "1",
        "cam2": str(param_dict.get("S2:Camera2Enable", "1")) == "1",
        "cam3": str(param_dict.get("S3:Camera3Enable", "1")) == "1",
        "cam4": str(param_dict.get("S4:Camera4Enable", "1")) == "1",
    }

    if camera_enabled["cam1"]:
        cs.camera_connect1()
    if camera_enabled["cam2"]:
        cs.camera_connect2()
    if camera_enabled["cam3"]:
        cs.camera_connect3()
    if camera_enabled["cam4"]:
        cs.camera_connect4()

def run_part_pipeline(active_stations, sock):
    """
    Run the pipeline for ONE part.

    IMPORTANT: S1 is the delay from SENSOR to CAMERA-1 capture time.
               So C1 should NOT start at 0.0 — it should start at +S1.
               After that, C2, C3, C4 start at cumulative times:
               C2: +S1+S2, C3: +S1+S2+S3, C4: +S1+S2+S3+S4.
    """

    # Per-part context (DB info, etc.)
    ctx = {"current_part_inserted": False, "inserted_s_no": None}

    # One result queue (OK/NOK) per active station — isolated to THIS part/thread
    from queue import Queue
    result_queues = {st: Queue() for st in active_stations}

    # ---- Build absolute OFFSETS in seconds from t0 ----
    # We now include S1 for C1 so that camera-1 fires AFTER the part reaches the FOV.
    absolute_offsets = {}
    acc = 0.0  # running sum of delays S1..S4

    for st in active_stations:
        # station name is like "C1","C2","C3","C4" → take the last char → 1..4
        n = int(st[-1])

        # Add THIS station's inter-stage delay (S1 for C1, S2 for C2, ...)
        # S1 specifically means "sensor to CAM1 shutter" (your new requirement).
        acc += _get_delay_for_station(n)

        # The absolute start time for this station is the total we've accumulated so far.
        absolute_offsets[st] = acc

    # Mark the start using a stable (monotonic) clock
    t0 = time.monotonic()

    # ---- Run stations in order ----
    for i, station in enumerate(active_stations):
        # Stop quickly if a global stop is requested
        if not keep_running:
            print("⛔️ Stopped by keep_running=False")
            return

        cam_id = f"cam{station[-1]}"  # "C3" → "cam3"

        # If camera is disabled/not connected, skip but pass OK so line keeps moving
        if not getattr(cs, f"isConnectedCamera{station[-1]}")():
            print(f"⚠️ {cam_id.upper()} disabled. Skipping and marking OK.")
            result_queues[station].put(True)
            continue

        # Wait until the absolute time for THIS station.
        # Example: C1 waits S1; C2 waits S1+S2; etc.
        offset = absolute_offsets[station]
        print(f"⏳ {station}: waiting until +{offset:.3f}s from start")
        wait_until(t0 + offset)

        # If a stop arrived during the wait, bail out
        if not keep_running or stop_event.is_set():
            print("⛔️ Stopped during wait")
            return

        # From C2 onward, only run if previous station was OK
        if i > 0:
            prev_station = active_stations[i - 1]
            try:
                ok_prev = result_queues[prev_station].get(timeout=0.1)  # quick check
                print(f"📝 {prev_station} → {station}: prev OK? {ok_prev}")
            except Exception as e:
                print(f"❌ No result from {prev_station} (treat NOK): {e}")
                ok_prev = False

            if not ok_prev:
                # Mark this station NOK and, if last, notify controller now
                print(f"❌ Skipping {station} because {prev_station} was NOK")
                result_queues[station].put(False)

                if station == active_stations[-1]:
                    try:
                        ok = send_until_ack(
                            sock, "$NOK#", "$ACK_NOK#",
                            timeout_per_try=timeout, resend_every=0.2, max_wait=5 * timeout
                        )
                        print("Sent $NOK# due to earlier NOK" + (" [ACK]" if ok else " [no ACK]"))
                    except Exception as ex:
                        print(f"❌ Error sending NOK: {ex}")
                continue

        # Start capture/processing for this station.
        # This function should push True/False into result_queues[station] when done.
        C_TriggeredProcess(cam_id, station, active_stations, ctx, result_queues)
        print(f"✅ {station} started.")
