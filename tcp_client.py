import socket
import threading
import time
import CameraConnection as cs
import dbscript as DB
import requests
import queue
import cv2
import station1 as Station1_detection
import station2 as Station2_detection
import station_3 as Station3_detection
import station_4 as Station4_detection
from event_bus import push_result

import data as dt

from queue import Queue

import cv2
import numpy as np
import os
from PIL import Image

Cam1frame = None
image2 = None
image3 = None
image4 = None

# Define station queues globally - FIXED: Create individual queues for each station
St1 = Queue()
St2 = Queue()
St3 = Queue()
St4 = Queue()

# FIXED: Map stations to their result queues
station_result_queues = {
    "C1": St1,
    "C2": St2,
    "C3": St3,
    "C4": St4,
}

CONTROLLER_IP = "192.168.0.104"  # 192.168.31.36        controller IP 192.168.0.104
CONTROLLER_PORT = 8888
timeout = 5

# Global control flag
keep_running = True

global sock
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
OutputFolder1 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam1output"
OutputFolder2 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam2output"
OutputFolder3 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam3output"
OutputFolder4 = r"D:\\PIM_25-09-25\\Pravi_Flask\\static\\OutputImages\\cam4output"

BackUpOutputFolder1 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam1output\cam1_output_backup"
BackUpOutputFolder2 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam2output\cam2_output_backup"
BackUpOutputFolder3 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam3output\cam3_output_backup"
BackUpOutputFolder4 = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages\cam4output\cam4_output_backup"


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
        # Enable flags (always included)
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

    # Clear queues
    for queue_obj in station_result_queues.values():
        while not queue_obj.empty():
            try:
                queue_obj.get_nowait()
            except:
                break

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((CONTROLLER_IP, CONTROLLER_PORT))
            print("✅ Connected to controller.")

            command_list = build_command_sequence(param_dict)

            # === Step 1: Send commands and wait for ACK ===
            for command, ack in command_list:
                # print(f"📤 Sending command: {command.strip()}")
                ack_received = False
                while not ack_received:
                    sock.sendall((command + "\r\n").encode())
                    time.sleep(0.5)
                    print(f"Sending {command} to controller")
                    try:
                        start_time = time.time()
                        buffer = ""
                        while time.time() - start_time < timeout:
                            try:
                                data = sock.recv(1024).decode()
                                buffer += data
                                if ack in buffer:
                                    ack_received = True
                                    # print(
                                    #     f"✅ Received ACK for {command.strip()}: {data.strip()}"
                                    # )
                                    break
                            except socket.timeout:
                                continue
                    except Exception as e:
                        print(f"❌ Error sending {command}: {e}")
                        break
                time.sleep(0.005)  # Slight delay before next command

            print("✅ All commands acknowledged.")

            # === Step 2: Send $STR# until $ACK_STR is received ===
            ack_received = False
            print("📤 Sending $STR# to start process")
            while not ack_received:
                sock.sendall("$STR#\r\n".encode())
                try:
                    start_time = time.time()
                    buffer = ""
                    while time.time() - start_time < timeout:
                        try:
                            data = sock.recv(1024).decode()
                            buffer += data
                            if "ACK_STR" in buffer:
                                ack_received = True
                                print("✅ Received $ACK_STR")
                                break
                        except socket.timeout:
                            continue
                except Exception as e:
                    print(f"❌ Error sending $STR#: {e}")

                time.sleep(0.05)

            # === Step 3: Connect Cameras ===
            print("🔗 Connecting cameras...")
            ConnectCam(param_dict)

            # === Step 4: Wait for C1 trigger ===
            while keep_running:
                try:
                    data = sock.recv(1024).decode().strip()
                    print(f"📥 Received: {data}")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving data: {e}")
                    break

                if "C1" in data:
                    print("✅ C1 received — starting processing")
                    print("Debugging starts here")

                    # Use the same helper you already wrote to read delays (supports CAM1DELAY or Delay_Cam1)
                    delay_time = 0.8
                    if delay_time > 0:
                        print(f"⏳ Waiting {delay_time} sec before triggering sequential process...")
                        time.sleep(delay_time)

                    threading.Thread(
                        target=run_sequential_process, args=(active_stations, sock)
                    ).start()


    except Exception as e:
        print(f"❌ Error in communicate_with_controller: {e}")


def stop_process():
    global sock
    global keep_running

    keep_running = False  # Stop ongoing processes

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((CONTROLLER_IP, CONTROLLER_PORT))
            print("🛑 Connected to controller for STOP command.")

            ack_received = False
            print("📤 Sending STP to controller")
            while not ack_received:
                sock.sendall("$STP#\r\n".encode())
                try:
                    start_time = time.time()
                    buffer = ""
                    while time.time() - start_time < timeout:
                        try:
                            data = sock.recv(1024).decode()
                            buffer += data
                            if "$ACK_STP#" in buffer:
                                ack_received = True
                                print("✅ Received ACK_STP")
                                cs.camera_disconnect()
                                break
                        except socket.timeout:
                            continue
                except Exception as e:
                    print(f"❌ Error sending STP: {e}")

                time.sleep(0.05)

    except Exception as e:
        print(f"❌ Error in stop_process: {e}")


def C_TriggeredProcess(cam_id, station, active_stations):
    if cam_id == "cam1":
        thread = threading.Thread(
            target=Capture_Prosses_Triggerflask, args=("cam1", station, active_stations)
        )
        thread.start()

    elif cam_id == "cam2":
        print("C_TriggeredProcess Started for cam2")
        thread = threading.Thread(
            target=Capture_Prosses_Triggerflask, args=("cam2", station, active_stations)
        )
        thread.start()

    elif cam_id == "cam3":
        thread = threading.Thread(
            target=Capture_Prosses_Triggerflask, args=("cam3", station, active_stations)
        )
        thread.start()

    elif cam_id == "cam4":
        thread = threading.Thread(
            target=Capture_Prosses_Triggerflask, args=("cam4", station, active_stations)
        )
        thread.start()


def Capture_Prosses_Triggerflask(cam_id, station, active_stations):
    if cam_id == "cam1":
        dt.Frames["Cam1frame"] = cs.capture_image_1()
        ReadPythonResult(
            cam_id="cam1", station=station, active_stations=active_stations
        )
        trigger_flask_camera(cam_id)

    if cam_id == "cam2":
        print("Capture_Prosses_Triggerflask Started for cam2")
        dt.Frames["Cam2frame"] = cs.capture_image_2()
        ReadPythonResult(
            cam_id="cam2", station=station, active_stations=active_stations
        )
        trigger_flask_camera(cam_id)

    if cam_id == "cam3":
        dt.Frames["Cam3frame"] = cs.capture_image_3()
        ReadPythonResult(
            cam_id="cam3", station=station, active_stations=active_stations
        )
        trigger_flask_camera(cam_id)

    if cam_id == "cam4":
        dt.Frames["Cam4frame"] = cs.capture_image_4()
        ReadPythonResult(
            cam_id="cam4", station=station, active_stations=active_stations
        )
        trigger_flask_camera(cam_id)


# Globals for per-part DB state (reset at start of each new part)
current_part_inserted = False
inserted_s_no = None


def ReadPythonResult(cam_id, station, active_stations):
    part_name = "PISTON"
    subpart_name = ""
    part_id = "P1S1"
    date_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    supplier_name = "S1"
    invoice_no = "I1"

    global current_part_inserted, inserted_s_no

    cam_num = int(cam_id[-1])

    # 1️⃣ If camera is disabled, skip it and pass an OK token
    if not getattr(cs, f"isConnectedCamera{cam_num}")():
        print(f"{cam_id.upper()} is disabled. Passing OK to next stage.")
        station_result_queues[station].put(True)
        return

    # Initialize result variables
    result_ok = False

    # 2️⃣ Run detection and gather results
    if cam_id == "cam1":

        DB.load_python_parameters(dt.StaticData["PartID"])
        params = dt.python_parameters["S1"]
        print(params)

        # Now call the function with unpacked values
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

        result_ok = result == "OK"

        if result == "OK":
            flash_id = "OK"
            flash_od = "OK"

        else:
            flash_id = "NOK"
            flash_od = "NOK"

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

        if not current_part_inserted:
            inserted_s_no = DB.insert_workpartdetail_1st_Station(
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
            current_part_inserted = True

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
            min_thresh = dt.python_parameters["S2"]["MINTHRESH"],
            max_thresh = dt.python_parameters["S2"]["MAXTHRESH"],
            backup_output_folder=BackUpOutputFolder2
        )
        

        print(
            f"Station 2 ResultType: {resultType}, Result: {result}, "
            f"Thickness: {thickness}, Error: {thickness_error}, OutputPath: {outputPath}"
        )

        result_ok = (result == "OK")
        thickness_status = "OK" if result_ok else "NOK"

        # ---- SSE payload: status in defects, numeric value in dimensions ----
        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {
                "vertical_flash": thickness_status
            },
            "dimensions": {
                "thickness": thickness
            },
        }
        print("Sending payload:", payload)
        push_result(cam_id, payload)

        # ---- DB insert/update ----
        if not current_part_inserted:
            inserted_s_no = DB.insert_workpartdetail_1st_Station(
                date_time,
                part_name,
                subpart_name,
                part_id,
                station,
                # S1 (not run here) -> "NA"
                "NA", "NA", "NA", "NA",
                "NA", "NA", "NA",
                # S2 (correct mapping)
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
            current_part_inserted = True
        else:
            DB.update_workpartdetail_2nd_Station(
                inserted_s_no,       # S_No to update
                station,             # Current_Station
                thickness_status,    # Thickness_Result (OK/NOK)
                thickness_error,     # Thickness_Cam_Error_Description
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
            backup_output_folder = BackUpOutputFolder3
        )

        # res is a dict per your new station3.py
        # Example keys: res["id"]["status"], res["id"]["count"], res["od"]["status"], res["od"]["count"], ...
        id_status = (res.get("id") or {}).get("status", "NOK")
        od_status = (res.get("od") or {}).get("status", "NOK")
        id_count = (res.get("id") or {}).get("count", 0)
        od_count = (res.get("od") or {}).get("count", 0)

        # Decide overall station result: OK only if both ID & OD are OK
        result_ok = (id_status == "OK" and od_status == "OK")
        top_burr_status = "OK" if result_ok else "NOK"   # keep your existing front-end contract

        payload = {
            "result": "OK" if result_ok else "NOK",
            "defects": {
                "top_burr": top_burr_status
            },
            "dimensions": {
                # if you want to expose counts/timings to UI, put them here (optional):
                "id_burr_count": id_count,
                "od_burr_count": od_count
            }
        }
        push_result(cam_id, payload)

        if not current_part_inserted:
            inserted_s_no = DB.insert_workpartdetail_1st_Station(
                date_time, part_name, subpart_name, part_id, station,
                # S1 placeholders
                "NA", "NA", "NA", "NA", "NA", "NA", "NA",
                # S2 placeholders (already handled earlier if cam2 ran first)
                "NA", "NA", "NA",
                # S3 placeholders or summaries — adjust once you wire columns
                "NA", "NA", "NA",
                # S4 placeholders
                "NA", "NA", "NA",
                supplier_name, invoice_no
            )
            current_part_inserted = True
        else:
            # Your DB.update_workpartdetail_3rd_Station is a stub; call once you define columns
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

            # ---- ID (inner) params (your S4 table names) ----
            ID2_OFFSET_ID=dt.python_parameters["S4"]["ID4_OFFSET"],          # note: using ID4_OFFSET for ID side
            HIGHLIGHT_SIZE_ID=dt.python_parameters["S4"]["HIGHLIGHT_SIZE"],
            ID_BURR_MIN_AREA=dt.python_parameters["S4"]["id_BURR_MIN_AREA"],
            ID_BURR_MAX_AREA=dt.python_parameters["S4"]["id_BURR_MAX_AREA"],
            ID_BURR_MIN_PERIMETER=dt.python_parameters["S4"]["id_BURR_MIN_PERIMETER"],
            ID_BURR_MAX_PERIMETER=dt.python_parameters["S4"]["id_BURR_MAX_PERIMETER"],

            # ---- OD (outer) params (OD-suffixed names you already store) ----
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
            backup_output_folder = BackUpOutputFolder4
        )

        # Expect the same dict shape as station3.py
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

        if not current_part_inserted:
            inserted_s_no = DB.insert_workpartdetail_1st_Station(
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
            current_part_inserted = True
        else:
            DB.update_workpartdetail_4th_Station(
                "OK" if result_ok else "NOK",
                None,               # Error string if you expose one
                bottom_burr,        # Burr status summary
                id_count + od_count # Example count aggregation
            )

        # Final OK/NOK only if C4 is the last active station
        if station == active_stations[-1]:
            try:
                total_delay = (
                    dt.python_parameters.get("Delay_Cam1", 0)
                    + dt.python_parameters.get("Delay_Cam2", 0)
                    + dt.python_parameters.get("Delay_Cam3", 0)
                    + dt.python_parameters.get("Delay_Cam4", 0)
                )
                print(f"⏳ Waiting {total_delay} sec before sending final result")
                time.sleep(total_delay)

                code = "$OK#\r\n" if result_ok else "$NOK#\r\n"
                DB.update_defect_count("OK" if result_ok else "NOK")
                sock.sendall(code.encode())
                print(f"Sent: {code.strip()}")
            except Exception as e:
                print(f"❌ Error sending final result: {e}")
    # 3️⃣ FIXED: Put result in current station's queue
    station_result_queues[station].put(result_ok)
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


def safe_get(obj, key, default=0):
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
    except Exception:
        pass
    return default


def run_sequential_process(active_stations, sock):
    """
    Runs C1–C4 sequentially:
    - C1 trigger comes from controller
    - C2–C4 follow with delays from data.py
    """

    for i, station in enumerate(active_stations):
        cam_id = f"cam{station[-1]}"

        # ⛳️ DEBUG: show raw delay values (from per-station dicts) and computed floats
        print("DEBUG raw delay keys:",
              "S1", dt.python_parameters.get("S1", {}).get("CAM1DELAY") or dt.python_parameters.get("S1", {}).get("Delay_Cam1"),
              "S2", dt.python_parameters.get("S2", {}).get("CAM2DELAY") or dt.python_parameters.get("S2", {}).get("Delay_Cam2"),
              "S3", dt.python_parameters.get("S3", {}).get("CAM3DELAY") or dt.python_parameters.get("S3", {}).get("Delay_Cam3"),
              "S4", dt.python_parameters.get("S4", {}).get("CAM4DELAY") or dt.python_parameters.get("S4", {}).get("Delay_Cam4"))
        print("DEBUG computed delays:",
              "S1", _get_delay_for_station(1),
              "S2", _get_delay_for_station(2),
              "S3", _get_delay_for_station(3),
              "S4", _get_delay_for_station(4))


        # Skip disabled cameras
        if not getattr(cs, f"isConnectedCamera{station[-1]}")():
            print(f"⚠️ {cam_id.upper()} is disabled. Passing OK to next stage.")
            station_result_queues[station].put(True)
            continue

        # If not first camera, wait for delay
        if station != "C1":
            delay_time = _get_delay_for_station(int(station[-1]))
            print(f"⏳ Waiting {delay_time} sec before {station}")
            if delay_time > 0:
                time.sleep(delay_time)


            # Check previous station result
            prev_station = active_stations[i - 1]
            try:
                ok = station_result_queues[prev_station].get(timeout=1)
                print(f"📝 Got result from {prev_station}: {ok}")
            except Exception as e:
                print(f"❌ Error getting token from {prev_station}: {e}")
                ok = False

            if not ok:
                # Still respect this station's configured delay before skipping
                delay_time = _get_delay_for_station(int(station[-1]))
                if delay_time > 0:
                    print(
                        f"⏳ Waiting {delay_time} sec before skipping {station} due to earlier NOK"
                    )
                    time.sleep(delay_time)

                print(f"❌ Skipping {station} because previous stage was NOK")
                station_result_queues[station].put(False)

                # If this was the last station, immediately notify controller
                if station == active_stations[-1]:
                    try:
                        print(dt.python_parameters.get("Delay_Cam1"))
                        print(dt.python_parameters.get("Delay_Cam2"))
                        print(dt.python_parameters.get("Delay_Cam3"))
                        print(dt.python_parameters.get("Delay_Cam4"))
                        

                        total_delay = sum(_get_delay_for_station(i) for i in (1,2,3,4))
                        print(
                            f"⏳ Waiting {total_delay} sec before sending final NOK (due to earlier NOK)"
                        )
                        time.sleep(total_delay)

                        sock.sendall("$NOK#\r\n".encode())
                        print("Sent: $NOK# (due to earlier NOK)")
                    except Exception as e:
                        print(f"❌ Error sending NOK: {e}")
                continue

        # Run detection for this station
        C_TriggeredProcess(cam_id, station, active_stations)
        print(f"✅ {station} processing started.")
