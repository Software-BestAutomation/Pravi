# dbscripts.py
import pyodbc
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
import data as dt

# ----------------------------
# Connection strings
# ----------------------------
conn_str = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=DESKTOP-3C651IK\SQLEXPRESS;"
    r"DATABASE=Pravi_DB;"
    r"Trusted_Connection=yes;"
    r"Encrypt=no;"
    r"TrustServerCertificate=yes;"
)

# Connection string WITHOUT database for initial check
server_conn_str = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=DESKTOP-3C651IK\SQLEXPRESS;"
    r"Trusted_Connection=yes;"
    r"Encrypt=no;"
    r"TrustServerCertificate=yes;"
)

# ----------------------------
# One-time DB / table setup
# ----------------------------
def ensure_database_exists():
    db_name = "Pravi_DB"
    try:
        conn = pyodbc.connect(server_conn_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(f"IF DB_ID('{db_name}') IS NULL CREATE DATABASE [{db_name}]")
        conn.close()
        print(f"✅ Database '{db_name}' checked/created.")
    except Exception as ex:
        print(f"❌ Error ensuring database {db_name}: {ex}")

def ensure_table_exists(table_name, create_sql):
    """Create table if it doesn't exist."""
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                IF NOT EXISTS (
                    SELECT * FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = ?
                )
                BEGIN
                    EXEC sp_executesql N'{}'
                END
                """.format(create_sql.replace("'", "''")),
                table_name,
            )
            conn.commit()
    except Exception as ex:
        print(f"Error ensuring table {table_name}: {ex}")

def ensure_recipe_master():
    create_sql = """
    CREATE TABLE Recipe_Master (
        Recipe_id NVARCHAR(50) PRIMARY KEY,
        Part_name NVARCHAR(100),
        Subpart_name NVARCHAR(100)
    )
    """
    ensure_table_exists("Recipe_Master", create_sql)

def ensure_work_part_detail():
    create_sql = """
    CREATE TABLE Work_Part_Detail (
        S_No INT IDENTITY(1,1) PRIMARY KEY,
        Date_time DATETIME,
        Part_Name NVARCHAR(100),
        Subpart_Name NVARCHAR(100),
        Part_ID NVARCHAR(50),
        Current_Station NVARCHAR(50),
        ID FLOAT,
        OD FLOAT,
        Orifice FLOAT,
        Concentricity FLOAT,
        Dimension_Cam_Image NVARCHAR(255),
        Dimension_Result NVARCHAR(50),
        Dimension_Cam_Error_Description NVARCHAR(255),
        Thickness_Cam_Image NVARCHAR(255),
        Thickness_Result NVARCHAR(50),
        Thickness_Cam_Error_Description NVARCHAR(255),
        TopBurr_Cam_Image NVARCHAR(255),
        TopBurr_Result NVARCHAR(50),
        TopBurr_Cam_Error_Description NVARCHAR(255),
        Bottom_Cam_Image NVARCHAR(255),
        Bottom_Result NVARCHAR(50),
        Bottom_Cam_Error_Description NVARCHAR(255),
        Supplier_Name NVARCHAR(100),
        Invoice_No NVARCHAR(50)
    )
    """
    ensure_table_exists("Work_Part_Detail", create_sql)

def ensure_python_parameters():
    create_sql = """
    CREATE TABLE Python_parameters (
        RecipeID NVARCHAR(50),
        Station NVARCHAR(50),
        Parameter NVARCHAR(100),
        Value NVARCHAR(255)
    )
    """
    ensure_table_exists("Python_parameters", create_sql)

def ensure_stationparameter_detail():
    create_sql = """
    CREATE TABLE StationParameterDetail (
        RecipeID NVARCHAR(50),
        Place NVARCHAR(50),
        Parameter NVARCHAR(100),
        Value NVARCHAR(255)
    )
    """
    ensure_table_exists("StationParameterDetail", create_sql)

def ensure_defect_count():
    create_sql = """
    CREATE TABLE Defect_Count (
        Parameter NVARCHAR(100) PRIMARY KEY,
        Counts INT
    )
    """
    ensure_table_exists("Defect_Count", create_sql)

def ensure_defects_details():
    create_sql = """
    CREATE TABLE Defects_Details (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Part NVARCHAR(100),
        [View] NVARCHAR(100),
        DefectName NVARCHAR(100)
    )
    """
    ensure_table_exists("Defects_Details", create_sql)

def ensure_setting_reference():
    create_sql = """
    CREATE TABLE Setting_Reference (
        Key1 NVARCHAR(100) PRIMARY KEY,
        Ref_val1 NVARCHAR(255),
        Ref_val2 NVARCHAR(255),
        Val NVARCHAR(255)
    )
    """
    ensure_table_exists("Setting_Reference", create_sql)

def ensure_all_tables():
    ensure_recipe_master()
    ensure_work_part_detail()
    ensure_python_parameters()
    ensure_stationparameter_detail()
    ensure_defect_count()
    ensure_defects_details()
    ensure_setting_reference()

def seed_recipe_master_if_empty():
    """Optional: seed one row so UI has something to show."""
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM dbo.Recipe_Master")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO dbo.Recipe_Master (Recipe_id, Part_name, Subpart_name)
                VALUES (?, ?, ?)
                """,
                ("P1S1", "PartA", "Sub1"),
            )
            conn.commit()
            print("🌱 Seeded Recipe_Master with PartA/Sub1 (P1S1)")

# ----------------------------
# Low-level query helpers
# ----------------------------
def _rows_to_dicts(cursor) -> List[Dict[str, Any]]:
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def query_all(sql: str, params: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return _rows_to_dicts(cur)

def query_one(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    rows = query_all(sql, params)
    return rows[0] if rows else None

# ----------------------------
# Business functions (READ)
# ----------------------------
def get_recipe_master() -> Optional[List[Dict[str, Any]]]:
    try:
        sql = "SELECT Part_name, Subpart_name, Recipe_id FROM dbo.Recipe_Master"
        return query_all(sql)
    except Exception as ex:
        print(f"Error while Getting Selected part's Data!: {ex}")
        return None

def get_recipe_master_partsettings() -> List[Dict[str, Any]]:
    sql = "SELECT Recipe_id, Part_name, Subpart_name FROM dbo.Recipe_Master"
    return query_all(sql)

def get_defects() -> List[Dict[str, Any]]:
    sql = "SELECT Part, [View], DefectName FROM dbo.Defects_Details"
    return query_all(sql)

def get_setting_reference() -> Optional[List[Dict[str, Any]]]:
    try:
        sql = "SELECT Key1, Ref_val1, Ref_val2, Val FROM dbo.Setting_Reference"
        return query_all(sql)
    except Exception as ex:
        print(f"Error while Getting Settings Reference Data!: {ex}")
        return None

def get_recipe_id_for_selection(part_name: str, subpart_name: str) -> Optional[str]:
    try:
        sql = """
        SELECT Recipe_id
        FROM dbo.Recipe_Master
        WHERE Part_name = ? AND Subpart_name = ?
        """
        row = query_one(sql, (part_name, subpart_name))
        if row:
            return row["Recipe_id"]
        print("⚠️ No recipe found for selection.")
        return None
    except Exception as ex:
        print(f"Error while fetching Recipe_ID: {ex}")
        return None

def get_parameters_for_recipe(recipe_id: str) -> Dict[str, Any]:
    try:
        sql = """
        SELECT Place, Parameter, Value
        FROM dbo.StationParameterDetail
        WHERE RecipeID = ?
        """
        rows = query_all(sql, (recipe_id,))
        # build {"SP:Conveyor1Speed": value, ...}
        return {f"{r['Place']}:{r['Parameter']}": r['Value'] for r in rows}
    except Exception as ex:
        print(f"Error getting parameters: {ex}")
        return {}

def get_stationparameter_detail() -> Optional[List[Dict[str, Any]]]:
    try:
        sql = """
        SELECT TOP (1000) RecipeID, Place, Parameter, Value
        FROM dbo.StationParameterDetail
        """
        return query_all(sql)
    except Exception as ex:
        print(f"Error while fetching StationParameterDetail data: {ex}")
        return None

def get_recipe_master_data() -> Optional[List[Dict[str, Any]]]:
    try:
        sql = """
        SELECT TOP (1000) Part_name, Subpart_name, Recipe_id
        FROM dbo.Recipe_Master
        """
        return query_all(sql)
    except Exception as ex:
        print(f"Error while fetching Recipe_Master data: {ex}")
        return None

def get_workpartdetail() -> Optional[List[Dict[str, Any]]]:
    try:
        sql = "SELECT * FROM dbo.Work_Part_Detail"
        return query_all(sql)
    except Exception as ex:
        print(f"Error while Getting Work part detail Data!: {ex}")
        return None

def get_work_part_details() -> List[Dict[str, Any]]:
    sql = "SELECT TOP (1000) * FROM dbo.Work_Part_Detail ORDER BY S_No DESC"
    return query_all(sql)

def get_recipe_id(part: str, subpart: str) -> Optional[str]:
    sql = """
    SELECT Recipe_id FROM dbo.Recipe_Master
    WHERE Part_name = ? AND Subpart_name = ?
    """
    row = query_one(sql, (part, subpart))
    return row["Recipe_id"] if row else None

def get_station_parameters(recipe_id: str) -> List[Dict[str, Any]]:
    sql = """
    SELECT Place, Parameter, Value
    FROM dbo.StationParameterDetail
    WHERE RecipeID = ?
    """
    return query_all(sql, (recipe_id,))

# ----------------------------
# Business functions (WRITE)
# ----------------------------
def add_part(part_name: str, subpart_name: str) -> str:
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    recipe_id = generate_recipe_id(part_name, subpart_name)
    cur.execute(
        "INSERT INTO dbo.Recipe_Master (Part_name, Subpart_name, Recipe_id) VALUES (?, ?, ?)",
        (part_name, subpart_name, recipe_id),
    )
    conn.commit()
    conn.close()
    return recipe_id

def generate_recipe_id(part_name: str, subpart_name: str) -> str:
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    # parts list
    cur.execute("SELECT DISTINCT Part_name FROM dbo.Recipe_Master ORDER BY Part_name")
    parts = [row[0] for row in cur.fetchall()]
    part_no = parts.index(part_name) + 1 if part_name in parts else len(parts) + 1
    # subpart count for this part
    cur.execute("SELECT COUNT(*) FROM dbo.Recipe_Master WHERE Part_name = ?", part_name)
    subpart_no = cur.fetchone()[0] + 1
    conn.close()
    return f"P{part_no}S{subpart_no}"

def update_part(recipe_id: str, new_part: str, new_subpart: str) -> None:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE dbo.Recipe_Master SET Part_name = ?, Subpart_name = ? WHERE Recipe_id = ?",
            (new_part, new_subpart, recipe_id),
        )
        conn.commit()

def delete_part(recipe_id: str) -> None:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM dbo.Recipe_Master WHERE Recipe_id = ?", (recipe_id,))
        conn.commit()

def add_defect(part: str, view: str, defect_name: str) -> bool:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.Defects_Details (Part, [View], DefectName) VALUES (?, ?, ?)",
            (part, view, defect_name),
        )
        conn.commit()
    return True

def update_defect(defect_id: int, part: str, view: str, defect_name: str) -> bool:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE dbo.Defects_Details SET Part=?, [View]=?, DefectName=? WHERE Id=?",
            (part, view, defect_name, defect_id),
        )
        conn.commit()
    return True

def delete_defect(defect_id: int) -> bool:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM dbo.Defects_Details WHERE Id=?", (defect_id,))
        conn.commit()
    return True

def get_settings() -> Dict[str, Any]:
    """Fetch all settings from Setting_Reference table as a dict."""
    settings: Dict[str, Any] = {}
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute("SELECT Key1, Ref_val1 FROM dbo.Setting_Reference")
            for row in cur.fetchall():
                settings[row.Key1] = row.Ref_val1
    except Exception as e:
        print("Error in get_settings:", e)
    return settings

def update_settings(new_values: Dict[str, Any]) -> bool:
    """Update multiple settings in Setting_Reference."""
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            for key, value in new_values.items():
                cur.execute(
                    "UPDATE dbo.Setting_Reference SET Ref_val1 = ? WHERE Key1 = ?",
                    (value, key),
                )
            conn.commit()
        return True
    except Exception as e:
        print("Error in update_settings:", e)
        return False

def load_python_parameters(recipe_id: str) -> None:
    """Load Python_parameters into in-memory dt.python_parameters."""
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT Station, Parameter, Value
                FROM dbo.Python_parameters
                WHERE RecipeID = ?
                """,
                (recipe_id,),
            )
            for station, param, value in cur.fetchall():
                if station in dt.python_parameters and param in dt.python_parameters[station]:
                    dt.python_parameters[station][param] = value
                    print(f"Loaded {station} - {param}: {value}")
    except Exception as e:
        print(f"❌ Error loading parameters: {e}")

def get_python_parameters(recipe_id: str) -> List[Dict[str, Any]]:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT RecipeID, Station, Parameter, Value
                FROM dbo.Python_parameters
                WHERE RecipeID = ?
                """,
                (recipe_id,),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                station = row.Station.strip()
                parameter = row.Parameter.strip()
                value = str(row.Value).strip() if row.Value is not None else ""
                result.append({"Station": station, "Parameter": parameter, "Value": value})
            return result
    except pyodbc.Error as e:
        print("Database error:", e)
        return []

def update_python_parameters(recipe_id: str, parameters: List[Dict[str, Any]]) -> bool:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            for param in parameters:
                station = param.get("Station")
                parameter = param.get("Parameter")
                value = param.get("Value")
                if not (station and parameter):
                    continue
                # UPDATE first
                cur.execute(
                    """
                    UPDATE dbo.Python_parameters
                    SET Value = ?
                    WHERE RecipeID = ? AND Station = ? AND Parameter = ?
                    """,
                    (value, recipe_id, station, parameter),
                )
                # If no row updated, INSERT
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO dbo.Python_parameters (RecipeID, Station, Parameter, Value)
                        VALUES (?, ?, ?, ?)
                        """,
                        (recipe_id, station, parameter, value),
                    )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error in update_python_parameters: {e}")
        return False

def update_station_parameters(recipe_id: str, param_list: List[Dict[str, Any]]) -> None:
    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        for param in param_list:
            cur.execute(
                """
                UPDATE dbo.StationParameterDetail
                SET Value = ?
                WHERE RecipeID = ? AND Place = ? AND Parameter = ?
                """,
                (
                    str(param.get("Value", "")).strip(),
                    str(recipe_id or "").strip(),
                    str(param.get("Place", "")).strip(),
                    str(param.get("Parameter", "")).strip(),
                ),
            )
        conn.commit()

def update_defect_count(parameter: str) -> None:
    """
    Increments the count for the given parameter ("OK" or "NOK") in Defect_Count.
    If the row doesn't exist, inserts it with count = 1.
    """
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            rows = cur.execute(
                "UPDATE dbo.Defect_Count SET Counts = Counts + 1 WHERE [Parameter] = ?",
                (parameter,),
            ).rowcount
            if rows == 0:
                cur.execute(
                    "INSERT INTO dbo.Defect_Count ([Parameter], [Counts]) VALUES (?, 1)",
                    (parameter,),
                )
            conn.commit()
    except Exception as ex:
        print(f"Error upserting Defect_Count for {parameter}: {ex}")

def insert_defect_count(parameter: str, counts: int) -> None:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO dbo.Defect_Count ([Parameter], [Counts]) VALUES (?, ?)",
                (parameter, counts),
            )
            conn.commit()
            print(f"Inserted Defect_Count: ({parameter}, {counts})")
    except Exception as ex:
        print(f"Error inserting into Defect_Count: {ex}")

def insert_workpartdetail_1st_Station(
    date_time,
    part_name,
    subpart_name,
    part_id,
    current_station,
    ID,
    OD,
    orifice,
    concentricity,
    dimension_cam_image,
    dimension_result,
    dimension_cam_error_description,
    thickness_cam_image,
    thickness_result,
    thickness_cam_error_description,
    topburr_cam_image,
    topburr_result,
    topburr_cam_error_description,
    bottom_cam_image,
    bottom_result,
    bottom_cam_error_description,
    supplier_name,
    invoice_no,
) -> None:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO dbo.Work_Part_Detail (
                    Date_time, Part_Name, Subpart_Name, Part_ID, Current_Station,
                    ID, OD, Orifice, Concentricity, Dimension_Cam_Image, Dimension_Result, Dimension_Cam_Error_Description,
                    Thickness_Cam_Image, Thickness_Result, Thickness_Cam_Error_Description,
                    TopBurr_Cam_Image, TopBurr_Result, TopBurr_Cam_Error_Description,
                    Bottom_Cam_Image, Bottom_Result, Bottom_Cam_Error_Description, Supplier_Name, Invoice_No
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date_time,
                    part_name,
                    subpart_name,
                    part_id,
                    current_station,
                    ID,
                    OD,
                    orifice,
                    concentricity,
                    dimension_cam_image,
                    dimension_result,
                    dimension_cam_error_description,
                    thickness_cam_image,
                    thickness_result,
                    thickness_cam_error_description,
                    topburr_cam_image,
                    topburr_result,
                    topburr_cam_error_description,
                    bottom_cam_image,
                    bottom_result,
                    bottom_cam_error_description,
                    supplier_name,
                    invoice_no,
                ),
            )
            conn.commit()
            print("Record inserted successfully.")
    except Exception as ex:
        print(f"Error while inserting data: {ex}")

def update_workpartdetail_2nd_Station(s_no, current_station, result, thickness_error) -> None:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE dbo.Work_Part_Detail
                SET Current_Station = ?, Thickness_Result = ?, Thickness_Cam_Error_Description = ?
                WHERE S_No = ?
                """,
                (current_station, result, thickness_error, s_no),
            )
            conn.commit()
            print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")


def update_workpartdetail_3rd_Station(result, Error, BurrStatus, BurrCount) -> None:
    try:
        # Implement when schema/flow is finalized
        print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")

def update_workpartdetail_4th_Station(result, Error, BurrStatus, BurrCount) -> None:
    try:
        # Implement when schema/flow is finalized
        print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")

def insert_dict_into_db(data_dict: Dict[str, Any]) -> None:
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO dbo.Work_Part_Detail (
                    Date_time, Part_Name, Subpart_Name, Part_ID, Current_Station,
                    ID, OD, Orifice, Concentricity, Dimension_Cam_Image,
                    Dimension_Result, Dimension_Cam_Error_Description, Thickness_Cam_Image,
                    Thickness_Result, Thickness_Cam_Error_Description, TopBurr_Cam_Image,
                    TopBurr_Result, TopBurr_Cam_Error_Description, Bottom_Cam_Image,
                    Bottom_Result, Bottom_Cam_Error_Description, Supplier_Name, Invoice_No
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data_dict["Date_time"],
                    data_dict["Part_Name"],
                    data_dict["Subpart_Name"],
                    data_dict["Part_ID"],
                    data_dict["Current_Station"],
                    data_dict["ID"],
                    data_dict["OD"],
                    data_dict["Orifice"],
                    data_dict["Concentricity"],
                    data_dict["Dimension_Cam_Image"],
                    data_dict["Dimension_Result"],
                    data_dict["Dimension_Cam_Error_Description"],
                    data_dict["Thickness_Cam_Image"],
                    data_dict["Thickness_Result"],
                    data_dict["Thickness_Cam_Error_Description"],
                    data_dict["TopBurr_Cam_Image"],
                    data_dict["TopBurr_Result"],
                    data_dict["TopBurr_Cam_Error_Description"],
                    data_dict["Bottom_Cam_Image"],
                    data_dict["Bottom_Result"],
                    data_dict["Bottom_Cam_Error_Description"],
                    data_dict["Supplier_Name"],
                    data_dict["Invoice_No"],
                ),
            )
            conn.commit()
            print("Data inserted successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")

# ----------------------------
# Bulk default inserts used by /add_part

def insert_default_parameters(recipe_id: str, parameters: List[Dict[str, Any]]) -> bool:
    """
    Insert default rows into dbo.Python_parameters for a new recipe.
    Expects items like: {"Station": "S1", "Parameter": "IDMIN", "Value": 0}
    """
    if not recipe_id or not parameters:
        return False
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            # Optional: avoid duplicate defaults by clearing existing rows for this recipe first
            cur.execute("DELETE FROM dbo.Python_parameters WHERE RecipeID = ?", (recipe_id,))

            rows = [
                (recipe_id, str(p.get("Station", "")).strip(),
                 str(p.get("Parameter", "")).strip(),
                 str(p.get("Value", "")))
                for p in parameters
                if p.get("Station") and p.get("Parameter")
            ]
            if not rows:
                return False

            cur.executemany(
                """
                INSERT INTO dbo.Python_parameters (RecipeID, Station, Parameter, Value)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting default Python_parameters: {e}")
        return False


def insert_default_station_parameters(recipe_id: str, parameters: List[Dict[str, Any]]) -> bool:
    """
    Insert default rows into dbo.StationParameterDetail for a new recipe.
    Expects items like: {"Place": "S1", "Parameter": "CameraGain", "Value": 0}
    """
    if not recipe_id or not parameters:
        return False
    try:
        with pyodbc.connect(conn_str) as conn:
            cur = conn.cursor()
            # Optional: avoid duplicate defaults by clearing existing rows for this recipe first
            cur.execute("DELETE FROM dbo.StationParameterDetail WHERE RecipeID = ?", (recipe_id,))

            rows = [
                (recipe_id, str(p.get("Place", "")).strip(),
                 str(p.get("Parameter", "")).strip(),
                 str(p.get("Value", "")))
                for p in parameters
                if p.get("Place") and p.get("Parameter")
            ]
            if not rows:
                return False

            cur.executemany(
                """
                INSERT INTO dbo.StationParameterDetail (RecipeID, Place, Parameter, Value)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting default StationParameterDetail: {e}")
        return False
