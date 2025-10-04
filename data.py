StaticData = {
    "PartID": "",
    "PartName": "",
    "SubPartName": "",
}

# data.py
 
python_parameters = {
    "S1": {
        "IDMIN": None,
        "IDMAX": None,
        "ODMIN": None,
        "ODMAX": None,
        "THRESHOLDID2": None,
        "THRESHOLDOD2": None,
        "THRESHOLDID3": None,
        "THRESHOLDOD3": None,
        "CONCENTRICITY": None,
        "ORIFICEMIN": None,
        "ORIFICEMAX": None,
        "PIXELTOMICRON": None,
        "PIXELTOMICRON_ID": None,
        "PIXELTOMICRON_OD": None,
        "Delay_Cam1": None,
        "CAM1DELAY": 0.0,  
    },
    "S2": {
        "THICKNESSMIN": None,
        "THICKNESSMAX": None,
        "PIXELTOMICRON": None,
        "MINTHRESH": None,
        "MAXTHRESH": None,
        "Delay_Cam2": None,
        "CAM2DELAY": 0.0, 
    },
    "S3": {
        #         id_BURR_MIN_AREA
        # id_BURR_MAX_AREA
        # id_BURR_MIN_PERIMETER
        # id_BURR_MAX_PERIMETER
        # HIGHLIGHT_SIZE ID2_OFFSET
        "ID2_OFFSET": None,
        "HIGHLIGHT_SIZE": None,
        "id_BURR_MIN_AREA": None,
        "id_BURR_MAX_AREA": None,
        "id_BURR_MIN_PERIMETER": None,
        "id_BURR_MAX_PERIMETER": None,
        "min_id_area3": None,
        "max_id_area3": None,
        "min_od_area3": None,
        "max_od_area3": None,
        "min_circularity3": None,
        "max_circularity3": None,
        "min_aspect_ratio3": None,
        "max_aspect_ratio3": None,
        "ID2_OFFSET_OD3": None,
        "HIGHLIGHT_SIZE_OD3": None,
        "OD_BURR_MIN_AREA3": None,
        "OD_BURR_MAX_AREA3": None,
        "OD_BURR_MIN_PERIMETER3": None,
        "OD_BURR_MAX_PERIMETER3": None,
        "Delay_Cam3": None,
        "CAM3DELAY": 0.0,
        # Station: "S3", Parameter: "min_id_area3", Value: document.getElementById("min_id_area3").value },
        # { Station: "S3", Parameter: "max_id_area3", Value: document.getElementById("max_id_area3").value },
        # { Station: "S3", Parameter: "min_od_area3", Value: document.getElementById("min_od_area3").value },
        # { Station: "S3", Parameter: "max_od_area3", Value: document.getElementById("max_od_area3").value },
    },
    "S4": {
        "ID4_OFFSET": None,
        "HIGHLIGHT_SIZE": None,
        "id_BURR_MIN_AREA": None,
        "id_BURR_MAX_AREA": None,
        "id_BURR_MIN_PERIMETER": None,
        "id_BURR_MAX_PERIMETER": None,
        "min_id_area4": None,
        "max_id_area4": None,
        "min_od_area4": None,
        "max_od_area4": None,
        "min_circularity4": None,
        "max_circularity4": None,
        "min_aspect_ratio4": None,
        "max_aspect_ratio4": None,
        "ID2_OFFSET_OD4": None,
        "HIGHLIGHT_SIZE_OD4": None,
        "OD_BURR_MIN_AREA4": None,
        "OD_BURR_MAX_AREA4": None,
        "OD_BURR_MIN_PERIMETER4": None,
        "OD_BURR_MAX_PERIMETER4": None,
        "Delay_Cam4": None,
        "CAM4DELAY": 0.0,  
    },
}


StaticData = {
    "PartID": "",
    "PartName": "",
    "SubPartName": "",
}


Frames = {"Cam1frame": "", "Cam2frame": "", "Cam3frame": "", "Cam4frame": ""}

# Initialize result dictionary
result = {
    "result_type": None,
    "result": None,
    "id": None,
    "id_status": None,
    "od": None,
    "od_status": None,
    "concentricity": None,
    "concentricity_status": None,
    "flash_defect": None,
    "defect_position": None,
    "orifice_diameter": None,
    "orifice_status": None,
    "error": None,
    "output_path": None,
}
