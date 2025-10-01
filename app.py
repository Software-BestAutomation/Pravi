from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_from_directory
import dbscript as dbscript
from tcp_client import communicate_with_controller,stop_process
import data as data
from threading import Thread, Event
import threading
import time
import CameraConnection as cs
import json
from event_bus import result_event_queue 
import os


app = Flask(__name__)
show_image_event = Event()


def uniq_parts(recipe_rows):
    return sorted({r['Part_name'] for r in (recipe_rows or [])})

def subparts_for(part, recipe_rows):
    return sorted({r['Subpart_name'] for r in (recipe_rows or []) if r['Part_name'] == part})

from flask import abort, send_from_directory
from werkzeug.utils import safe_join
import os

OUTPUT_ROOT = r"D:\PIM_25-09-25\Pravi_Flask\static\OutputImages"

@app.route('/images/<cam_id>/<path:filename>')
def images(cam_id, filename):
    allowed = {"cam1output", "cam2output", "cam3output", "cam4output"}
    if cam_id not in allowed:
        abort(404)

    directory = safe_join(OUTPUT_ROOT, cam_id)

    # Optional: guard for missing file (helps you see 404s instead of 500s)
    full_path = safe_join(directory, filename)
    if not os.path.isfile(full_path):
        abort(404)

    # Werkzeug ≥3: use max_age (cache_timeout removed)
    try:
        resp = send_from_directory(directory, filename, max_age=0)
    except TypeError:
        # Old Werkzeug fallback
        resp = send_from_directory(directory, filename)

    # Strong no-cache headers so your ?v=... works reliably
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp




@app.route("/", methods=["GET", "POST"])
def Home():
    recipe_data = dbscript.get_recipe_master()           # list[dict] or None
    work_data = dbscript.get_work_part_details()         # list[dict]

    part_list = uniq_parts(recipe_data)

    return render_template(
        "index.html",
        parts=part_list,
        work_part_details=work_data
    )


@app.route('/get_subparts_home', methods=['POST'])
def get_subparts_home():
    selected_part = request.json.get('part')
    recipe_data = dbscript.get_recipe_master()
    return jsonify({'subparts': subparts_for(selected_part, recipe_data)})


@app.route('/StationSettings', methods=["GET", "POST"])
def StationSettings():
    recipe_data = dbscript.get_recipe_master()
    part_list = uniq_parts(recipe_data)
    return render_template('StationSettings.html', parts=part_list)


@app.route('/get_subparts', methods=['POST'])
def get_subparts():
    selected_part = request.json.get('part')
    recipe_data = dbscript.get_recipe_master()
    return {'subparts': subparts_for(selected_part, recipe_data)}

@app.route('/get_station_parameters', methods=['POST'])
def get_station_parameters_route():
    data = request.get_json()
    part = data.get('part')
    subpart = data.get('subpart')

    recipe_id = dbscript.get_recipe_id(part, subpart)
    if recipe_id:
        parameters = dbscript.get_station_parameters(recipe_id)
        print(f"Part: {part}, Subpart: {subpart}, Recipe ID: {recipe_id}")
        print("Parameters:", parameters)

        return jsonify(parameters)
    else:
        return jsonify([])  # Or return error


@app.route('/update_station_parameters', methods=["POST"])
def update_station_parameters():
    data = request.get_json()
    part = data['part']
    subpart = data['subpart']
    parameters = data['parameters']

    recipe_id = dbscript.get_recipe_id(part, subpart)
    if not recipe_id:
        return jsonify({'message': 'Invalid Recipe ID'}), 400

    dbscript.update_station_parameters(recipe_id, parameters)
    return jsonify({'message': 'Parameters updated successfully'})





# @app.route('/PartsStationSettings', methods=["GET", "POST"])
# def PartsStationSettings():
#     recipe_data = dbscript.get_recipe_master()


#     if recipe_data is not None:
#         part_list = recipe_data['Part_name'].unique().tolist()
#         subpart_list = recipe_data['Subpart_name'].unique().tolist()
#     else:
#         part_list = []
#         subpart_list = []

#     return render_template('partsettings.html', parts=part_list, subparts=subpart_list)






@app.route('/PartsStationSettings', methods=["GET", "POST"])
def PartsStationSettings():
    recipe_data = dbscript.get_recipe_master() or []
    part_list = uniq_parts(recipe_data)
    rows = recipe_data  # already list[dict]
    return render_template('partsettings.html', parts=part_list, rows=rows)


@app.route('/get_subparts_parts', methods=['POST'])
def get_subparts_parts():
    selected_part = request.json.get('part')
    recipe_data = dbscript.get_recipe_master()
    return jsonify({'subparts': subparts_for(selected_part, recipe_data)})


@app.route('/PartSettings', methods=["GET", "POST"])
def PartSettings():
    if request.method == "POST":
        # Save camera settings
        new_values = {
            "Camera1SerialNo": request.form.get("camera-1-serial-no"),
            "Camera2SerialNo": request.form.get("camera-2-serial-no"),
            "Camera3SerialNo": request.form.get("camera-3-serial-no"),
            "Camera4SerialNo": request.form.get("camera-4-serial-no"),
            "Port Name": request.form.get("port-name"),
            "Baud Rate": request.form.get("baud-rate"),
            "Master Local Path": request.form.get("master-local-path")
        }
        success = dbscript.update_settings(new_values)
        flash("Settings updated successfully" if success else "Error updating settings", "success" if success else "error")
        return redirect(url_for("PartSettings"))

    # GET → fetch settings, parts, defects
    settings = dbscript.get_settings()

    recipe_data = dbscript.get_recipe_master() or []
    rows = recipe_data
    parts = uniq_parts(recipe_data)

    defect_data = dbscript.get_defects() or []   # list[dict]
    defect_rows = defect_data

    return render_template(
        'Settings.html',
        Camera1SerialNo=settings.get("Camera1SerialNo", ""),
        Camera2SerialNo=settings.get("Camera2SerialNo", ""),
        Camera3SerialNo=settings.get("Camera3SerialNo", ""),
        Camera4SerialNo=settings.get("Camera4SerialNo", ""),
        port_name=settings.get("Port Name", ""),
        baud_rate=settings.get("Baud Rate", ""),
        master_local_path=settings.get("Master Local Path", ""),
        rows=rows,
        parts=parts,
        defect_rows=defect_rows
    )





@app.route('/add_part', methods=["POST"])
def add_part():
    data = request.json
    part = data.get("part")
    subpart = data.get("subpart")
    
    # Create the recipe_id by calling your dbscript function
    recipe_id = dbscript.add_part(part, subpart)
    
    if recipe_id is None:
        return jsonify({"success": False, "error": "Failed to create part"}), 500
    
    # Define default parameters for Python_parameters table
    python_parameters = [
        # Station S1 parameters
        {"Station": "S1", "Parameter": "IDMIN", "Value": 0},
        {"Station": "S1", "Parameter": "IDMAX", "Value": 0},
        {"Station": "S1", "Parameter": "ODMIN", "Value": 0},
        {"Station": "S1", "Parameter": "ODMAX", "Value": 0},
        {"Station": "S1", "Parameter": "THRESHOLDID2", "Value": 0},
        {"Station": "S1", "Parameter": "THRESHOLDOD2", "Value": 0},
        {"Station": "S1", "Parameter": "CONCENTRICITY", "Value": 0},
        {"Station": "S1", "Parameter": "ORIFICEMIN", "Value": 0},
        {"Station": "S1", "Parameter": "ORIFICEMAX", "Value": 0},
        {"Station": "S1", "Parameter": "PIXELTOMICRON_ID", "Value": 0},
        {"Station": "S1", "Parameter": "PIXELTOMICRON_OD", "Value": 0},
        {"Station": "S1", "Parameter": "THRESHOLDID3", "Value": 0},
        {"Station": "S1", "Parameter": "THRESHOLDOD3", "Value": 0},
        {"Station": "S1", "Parameter": "PIXELTOMICRON", "Value": 0},
        {"Station": "S1", "Parameter": "CAM1DELAY", "Value": 0},
        
        # Station S2 parameters
        {"Station": "S2", "Parameter": "THICKNESSMIN", "Value": 0},
        {"Station": "S2", "Parameter": "THICKNESSMAX", "Value": 0},
        {"Station": "S2", "Parameter": "MINTHRESH", "Value": 0},
        {"Station": "S2", "Parameter": "MAXTHRESH", "Value": 0},
        {"Station": "S2", "Parameter": "PIXELTOMICRON", "Value": 0},
        {"Station": "S2", "Parameter": "CAM2DELAY", "Value": 0},
        
        # Station S3 parameters
        {"Station": "S3", "Parameter": "ID2_OFFSET", "Value": 0},
        {"Station": "S3", "Parameter": "HIGHLIGHT_SIZE", "Value": 0},
        {"Station": "S3", "Parameter": "id_BURR_MIN_AREA", "Value": 0},
        {"Station": "S3", "Parameter": "id_BURR_MAX_AREA", "Value": 0},
        {"Station": "S3", "Parameter": "id_BURR_MIN_PERIMETER", "Value": 0},
        {"Station": "S3", "Parameter": "id_BURR_MAX_PERIMETER", "Value": 0},
        {"Station": "S3", "Parameter": "min_id_area3", "Value": 0},
        {"Station": "S3", "Parameter": "max_id_area3", "Value": 0},
        {"Station": "S3", "Parameter": "min_od_area3", "Value": 0},
        {"Station": "S3", "Parameter": "max_od_area3", "Value": 0},
        {"Station": "S3", "Parameter": "min_circularity3", "Value": 0},
        {"Station": "S3", "Parameter": "max_circularity3", "Value": 0},
        {"Station": "S3", "Parameter": "min_aspect_ratio3", "Value": 0},
        {"Station": "S3", "Parameter": "max_aspect_ratio3", "Value": 0},
        {"Station": "S3", "Parameter": "CAM3DELAY", "Value": 0},
        {"Station": "S3", "Parameter": "ID2_OFFSET_OD3", "Value": 0},
        {"Station": "S3", "Parameter": "HIGHLIGHT_SIZE_OD3", "Value": 0},
        {"Station": "S3", "Parameter": "OD_BURR_MIN_AREA3", "Value": 0},
        {"Station": "S3", "Parameter": "OD_BURR_MAX_AREA3", "Value": 0},
        {"Station": "S3", "Parameter": "OD_BURR_MIN_PERIMETER3", "Value": 0},
        {"Station": "S3", "Parameter": "OD_BURR_MAX_PERIMETER3", "Value": 0},

        
        # Station S4 parameters
        {"Station": "S4", "Parameter": "HIGHLIGHT_SIZE", "Value": 0},
        {"Station": "S4", "Parameter": "id_BURR_MIN_AREA", "Value": 0},
        {"Station": "S4", "Parameter": "id_BURR_MAX_AREA", "Value": 0},
        {"Station": "S4", "Parameter": "id_BURR_MIN_PERIMETER", "Value": 0},
        {"Station": "S4", "Parameter": "id_BURR_MAX_PERIMETER", "Value": 0},
        {"Station": "S4", "Parameter": "ID4_OFFSET", "Value": 0},
        {"Station": "S4", "Parameter": "min_id_area4", "Value": 0},
        {"Station": "S4", "Parameter": "max_id_area4", "Value": 0},
        {"Station": "S4", "Parameter": "min_od_area4", "Value": 0},
        {"Station": "S4", "Parameter": "max_od_area4", "Value": 0},
        {"Station": "S4", "Parameter": "min_circularity4", "Value": 0},
        {"Station": "S4", "Parameter": "max_circularity4", "Value": 0},
        {"Station": "S4", "Parameter": "min_aspect_ratio4", "Value": 0},
        {"Station": "S4", "Parameter": "max_aspect_ratio4", "Value": 0},
        {"Station": "S4", "Parameter": "CAM4DELAY", "Value": 0},
        {"Station": "S4", "Parameter": "ID2_OFFSET_OD4", "Value": 0},
        {"Station": "S4", "Parameter": "HIGHLIGHT_SIZE_OD4", "Value": 0},
        {"Station": "S4", "Parameter": "OD_BURR_MIN_AREA4", "Value": 0},
        {"Station": "S4", "Parameter": "OD_BURR_MAX_AREA4", "Value": 0},
        {"Station": "S4", "Parameter": "OD_BURR_MIN_PERIMETER4", "Value": 0},
        {"Station": "S4", "Parameter": "OD_BURR_MAX_PERIMETER4", "Value": 0},

    ]
    
    # Define default parameters for StationParameterDetail table
    station_parameters = [
        # Station S1 camera parameters
        {"Place": "S1", "Parameter": "CameraVerticalMoment", "Value": 0},
        {"Place": "S1", "Parameter": "LightIntensity", "Value": 0},
        {"Place": "S1", "Parameter": "CameraExposure", "Value": 0},
        {"Place": "S1", "Parameter": "CameraGain", "Value": 0},
        {"Place": "S1", "Parameter": "CapturingDelay", "Value": 0},
        {"Place": "S1", "Parameter": "Camera1Enable", "Value": 0},
        
        # Station S2 camera parameters
        {"Place": "S2", "Parameter": "CameraLateralMoment", "Value": 0},
        {"Place": "S2", "Parameter": "LightIntensity", "Value": 0},
        {"Place": "S2", "Parameter": "CameraExposure", "Value": 0},
        {"Place": "S2", "Parameter": "CameraGain", "Value": 0},
        {"Place": "S2", "Parameter": "CapturingDelay", "Value": 0},
        {"Place": "S2", "Parameter": "Camera2Enable", "Value": 0},
        
        # Station S3 camera parameters
        {"Place": "S3", "Parameter": "CameraVerticalMoment", "Value": 0},
        {"Place": "S3", "Parameter": "LightIntensity", "Value": 0},
        {"Place": "S3", "Parameter": "CameraExposure", "Value": 0},
        {"Place": "S3", "Parameter": "CameraGain", "Value": 0},
        {"Place": "S3", "Parameter": "CapturingDelay", "Value": 0},
        {"Place": "S3", "Parameter": "Camera3Enable", "Value": 0},
        
        # Station S4 camera parameters
        {"Place": "S4", "Parameter": "CameraVerticalMoment", "Value": 0},
        {"Place": "S4", "Parameter": "LightIntensity", "Value": 0},
        {"Place": "S4", "Parameter": "CameraExposure", "Value": 0},
        {"Place": "S4", "Parameter": "CameraGain", "Value": 0},
        {"Place": "S4", "Parameter": "CapturingDelay", "Value": 0},
        {"Place": "S4", "Parameter": "Camera4Enable", "Value": 0},
        
        # Special Place (SP) parameters
        {"Place": "SP", "Parameter": "IndexingSpeed", "Value": 0},
        {"Place": "SP", "Parameter": "VibratorSpeed", "Value": 0},
        {"Place": "SP", "Parameter": "Conveyor1Speed", "Value": 0},
        {"Place": "SP", "Parameter": "Conveyor2Speed", "Value": 0},
        {"Place": "SP", "Parameter": "PartPushSpeed", "Value": 0}
    ]
    
    # Insert both sets of parameters
    python_success = dbscript.insert_default_parameters(recipe_id, python_parameters)
    station_success = dbscript.insert_default_station_parameters(recipe_id, station_parameters)
    
    if python_success and station_success:
        return jsonify({
            "success": True, 
            "part": part, 
            "subpart": subpart, 
            "recipe_id": recipe_id,
            "python_parameters_inserted": len(python_parameters),
            "station_parameters_inserted": len(station_parameters)
        })
    else:
        return jsonify({
            "success": False, 
            "error": "Failed to insert some default parameters"
        }), 500


@app.route('/update_part', methods=["POST"])
def update_part():
    data = request.json
    recipe_id = data.get("recipe_id")
    new_part = data.get("part")
    new_subpart = data.get("subpart")
    dbscript.update_part(recipe_id, new_part, new_subpart)
    return jsonify({"success": True})

@app.route('/delete_part', methods=["POST"])
def delete_part():
    data = request.json
    recipe_id = data.get("recipe_id")
    dbscript.delete_part(recipe_id)
    return jsonify({"success": True})


@app.route('/get_python_parameters', methods=['POST'])
def get_python_parameters():
    data = request.get_json()
    part = data.get('part')
    subpart = data.get('subpart')

    recipe_id = dbscript.get_recipe_id(part, subpart)
    if recipe_id:
        parameters = dbscript.get_python_parameters(recipe_id)
        print(f"Fetched Python Parameters for Part: {part}, Subpart: {subpart}, RecipeID: {recipe_id}")
        print("Parameters:", parameters)
        return jsonify(parameters)
    else:
        return jsonify([]), 404


@app.route('/update_python_parameters', methods=['POST'])
def update_python_parameters():
    data = request.get_json()
    part = data.get('part')
    subpart = data.get('subpart')
    parameters = data.get('parameters')

    recipe_id = dbscript.get_recipe_id(part, subpart)
    if not recipe_id:
        return jsonify({'message': 'Invalid Recipe ID'}), 400

    success = dbscript.update_python_parameters(recipe_id, parameters)
    if success:
        return jsonify({'message': 'Python parameters updated successfully'})
    else:
        return jsonify({'message': 'Failed to update parameters'}), 500




@app.route('/start', methods=['POST'])
def start_sequence():
    part = request.json.get('part')
    subpart = request.json.get('subpart')

    data.StaticData["PartName"] = part
    data.StaticData["SubPartName"] = subpart

    # print(f"🚀 Starting sequence for Part: {part}, Subpart: {subpart}")

    # Step 1: Get Recipe ID
    recipe_id = dbscript.get_recipe_id_for_selection(part, subpart)
    if not recipe_id:
        return jsonify({"status": "failure", "error": "Recipe ID not found"}), 400

    # Step 2: Get Parameters for that Recipe
    raw_param_dict = dbscript.get_parameters_for_recipe(recipe_id)
    data.StaticData["PartID"] = recipe_id
    # print(recipe_id)

    # ✅ Step 2.5: Clean up the keys (strip extra spaces)
    param_dict = {}
    for key, value in raw_param_dict.items():
        cleaned_key = key.replace(" ", "")  # Remove all spaces
        param_dict[cleaned_key] = value

    # print("✅ Cleaned Parameter Dictionary:", param_dict)

    # Step 3: Start communication with parameter-based commands
    threading.Thread(target=communicate_with_controller, args=(param_dict,)).start()

    return jsonify({"status": "success"})



@app.route('/stop', methods=['POST'])
def stop_sequence():
    try:
        
        threading.Thread(target=stop_process).start()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"❌ Stop process error: {e}")
        return jsonify({"status": "failure", "error": str(e)}), 500



@app.route('/camera-status')
def camera_status():
    status = {
        'cam1': cs.isConnectedCamera1(),
        'cam2': cs.isConnectedCamera2(),
        'cam3': cs.isConnectedCamera3(),
        'cam4': cs.isConnectedCamera4()
    }
    return jsonify(status)



cam_events = {
    "cam1": Event(),
    "cam2": Event(),
    "cam3": Event(),
    "cam4": Event(),
}

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            for cam_id, event in cam_events.items():
                if event.is_set():
                    yield f"data: {cam_id}\n\n"
                    print(f"📡 Sending '{cam_id}' event to frontend")
                    event.clear()
            time.sleep(0.1)
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/trigger/<cam_id>', methods=['POST'])
def trigger(cam_id):
    if cam_id in cam_events:
        cam_events[cam_id].clear()  # Clear first to ensure re-trigger works
        cam_events[cam_id].set()    # Then set it again
        print(f"✅ Triggered event for {cam_id}")
        return "Triggered"
    return "Invalid camera ID", 400


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)
 


@app.route("/Report", methods=["GET", "POST"])
def report():
    recipe_data = dbscript.get_recipe_master() or []
    part_list = uniq_parts(recipe_data)
    subpart_list = sorted({r['Subpart_name'] for r in recipe_data})
    return render_template('Report.html', parts=part_list, subparts=subpart_list)



@app.route('/add_defect', methods=["POST"])
def add_defect_route():
    part = request.form.get("part")
    station = request.form.get("station")
    defect = request.form.get("defect")
    dbscript.add_defect(part, station, defect)
    return redirect(url_for("DefectSettings"))

@app.route('/update_defect/<int:defect_id>', methods=["POST"])
def update_defect_route(defect_id):
    part = request.form.get("part")
    station = request.form.get("station")
    defect = request.form.get("defect")
    dbscript.update_defect(defect_id, part, station, defect)
    return redirect(url_for("DefectSettings"))

@app.route('/delete_defect/<int:defect_id>', methods=["POST"])
def delete_defect_route(defect_id):
    dbscript.delete_defect(defect_id)
    return redirect(url_for("DefectSettings"))




@app.route("/result_stream")
def result_stream():
    def event_stream():
        while True:
            data = result_event_queue.get()  # blocking until new result
            print("[SSE] streaming:", data)
            yield f"data: {json.dumps(data)}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        dbscript.ensure_database_exists()
        dbscript.ensure_all_tables()
    app.run(debug=True, port=9000, threaded=True)




