import pyodbc
import pandas as pd
from datetime import datetime
import data as dt

conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=DESKTOP-3C651IK\SQLEXPRESS;'
            r'DATABASE=Pravi_DB;'
            r'Trusted_Connection=yes;'
            r'Encrypt=no;'
            r'TrustServerCertificate=yes;'
            )


#DESKTOP-3C651IK\SQLEXPRESS




def insert_default_parameters(recipe_id, parameters):
    """
    Insert default parameters for a new recipe into Python_parameters table
    """
    try:
        # Create connection
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        # Prepare the bulk insert query
        insert_query = """
        INSERT INTO [Pravi_DB].[dbo].[Python_parameters] 
        (RecipeID, Station, Parameter, Value) 
        VALUES (?, ?, ?, ?)
        """
        
        # Prepare data for bulk insert
        insert_data = []
        for param in parameters:
            insert_data.append((
                recipe_id,
                param["Station"],
                param["Parameter"],
                param["Value"]
            ))
        
        # Execute bulk insert
        cursor.executemany(insert_query, insert_data)
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Successfully inserted {len(insert_data)} parameters for recipe {recipe_id}")
        return True
        
    except Exception as e:
        print(f"Error inserting default parameters: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False

def insert_default_station_parameters(recipe_id, parameters):
    """
    Insert default station parameters for a new recipe into StationParameterDetail table
    """
    try:
        # Create connection
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        # Prepare the bulk insert query for StationParameterDetail table
        insert_query = """
        INSERT INTO [Pravi_DB].[dbo].[StationParameterDetail] 
        (RecipeID, Place, Parameter, Value) 
        VALUES (?, ?, ?, ?)
        """
        
        # Prepare data for bulk insert
        insert_data = []
        for param in parameters:
            insert_data.append((
                recipe_id,
                param["Place"],
                param["Parameter"],
                param["Value"]
            ))
        
        # Execute bulk insert
        cursor.executemany(insert_query, insert_data)
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Successfully inserted {len(insert_data)} station parameters for recipe {recipe_id}")
        return True
        
    except Exception as e:
        print(f"Error inserting default station parameters: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False


def get_connection():
    return pyodbc.connect(conn_str)

def get_recipe_master_partsettings():
    conn = get_connection()
    query = "SELECT Recipe_id, Part_name, Subpart_name FROM Recipe_Master"
    df = pd.read_sql(query, conn)
    print("df: ", df)
    conn.close()
    return df


def generate_recipe_id(part_name, subpart_name):
    conn = get_connection()
    cursor = conn.cursor()

    # Find part number
    cursor.execute("SELECT DISTINCT Part_name FROM Recipe_Master ORDER BY Part_name")
    parts = [row[0] for row in cursor.fetchall()]

    if part_name not in parts:
        part_no = len(parts) + 1
    else:
        part_no = parts.index(part_name) + 1

    # Find subpart number for this part
    cursor.execute("SELECT COUNT(*) FROM Recipe_Master WHERE Part_name = ?", part_name)
    subpart_count = cursor.fetchone()[0]
    subpart_no = subpart_count + 1

    recipe_id = f"P{part_no}S{subpart_no}"
    conn.close()
    return recipe_id

def add_part(part_name, subpart_name):
    conn = get_connection()
    cursor = conn.cursor()

    recipe_id = generate_recipe_id(part_name, subpart_name)

    cursor.execute(
        "INSERT INTO Recipe_Master (Part_name, Subpart_name, Recipe_id) VALUES (?, ?, ?)",
        (part_name, subpart_name, recipe_id)
    )
    conn.commit()
    conn.close()
    return recipe_id





def update_part(recipe_id, new_part, new_subpart):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Recipe_Master SET Part_name = ?, Subpart_name = ? WHERE Recipe_id = ?",
        (new_part, new_subpart, recipe_id)
    )
    conn.commit()
    conn.close()

def delete_part(recipe_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Recipe_Master WHERE Recipe_id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def get_defects():
    conn = get_connection()
    query = "SELECT  Part, [View], DefectName FROM Defects_Details"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def add_defect(part, view, defect_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Defects_Details (Part, [View], DefectName) VALUES (?, ?, ?)",
        (part, view, defect_name)
    )
    conn.commit()
    conn.close()
    return True

def update_defect(defect_id, part, view, defect_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Defects_Details SET Part=?, [View]=?, DefectName=? WHERE Id=?",
        (part, view, defect_name, defect_id)
    )
    conn.commit()
    conn.close()
    return True

def delete_defect(defect_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Defects_Details WHERE Id=?", (defect_id,))
    conn.commit()
    conn.close()
    return True





def get_settings():
    """Fetch all settings from Setting_Reference table as a dict"""
    settings = {}
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Key1, Ref_val1 FROM Setting_Reference")
            for row in cursor.fetchall():
                settings[row.Key1] = row.Ref_val1
    except Exception as e:
        print("Error in get_settings:", e)
    return settings


def update_settings(new_values: dict):
    """Update multiple settings in Setting_Reference"""
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            for key, value in new_values.items():
                cursor.execute(
                    "UPDATE Setting_Reference SET Ref_val1 = ? WHERE Key1 = ?",
                    value, key
                )
            conn.commit()
        return True
    except Exception as e:
        print("Error in update_settings:", e)
        return False


def load_python_parameters(recipe_id):
    
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
            SELECT Station, Parameter, Value
            FROM Pravi_DB.dbo.Python_parameters
            WHERE RecipeID = ?
        """
        cursor.execute(query, recipe_id)

        for station, param, value in cursor.fetchall():
            if station in dt.python_parameters and param in dt.python_parameters[station]:
                dt.python_parameters[station][param] = value
                print(f"Loaded {station} - {param}: {value}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error loading parameters: {e}")


def get_python_parameters(recipe_id):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        SELECT RecipeID, Station, Parameter, Value
        FROM Python_parameters
        WHERE RecipeID = ?
        """

        cursor.execute(query, recipe_id)
        rows = cursor.fetchall()

        result = []

        for row in rows:
            station = row.Station.strip()
            parameter = row.Parameter.strip()
            value = str(row.Value).strip() if row.Value is not None else ""

            result.append({
                "Station": station,
                "Parameter": parameter,
                "Value": value
            })

        conn.close()
        return result

    except pyodbc.Error as e:
        print("Database error:", e)
        return []


def update_python_parameters(recipe_id, parameters):

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        for param in parameters:
            station = param.get('Station')
            parameter = param.get('Parameter')
            value = param.get('Value')

            if not (station and parameter):  
                continue

            cursor.execute("""
                UPDATE Python_parameters
                SET Value = ?
                WHERE RecipeID = ? AND Station = ? AND Parameter = ?
            """, (value, recipe_id, station, parameter))

            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO Python_parameters (RecipeID, Station, Parameter, Value)
                    VALUES (?, ?, ?, ?)
                """, (recipe_id, station, parameter, value))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in update_python_parameters: {e}")
        return False


def get_users_Detail():
    return 0


def get_recipe_master():

    try:

        conn = pyodbc.connect(conn_str)
        
        query = f"SELECT [Part_name], [Subpart_name], [Recipe_id] FROM [Recipe_Master]"
        
        selected_parts_data = pd.read_sql(query, conn)

        print(selected_parts_data)

        conn.close()

        return selected_parts_data

    except Exception as ex:
        print(f"Error while Getting Selected part's Data!: {ex}")
        return None


def get_setting_reference():

    try:

        conn = pyodbc.connect(conn_str)
        
        query = f"SELECT [Key1]  ,[Ref_val1] ,[Ref_val2] ,[Val] FROM [Setting_Reference]"
        
        setting_reference_data = pd.read_sql(query, conn)

        print(setting_reference_data)

        conn.close()

        return setting_reference_data

    except Exception as ex:
        print(f"Error while Getting Settings Reference Data!: {ex}")
        return None


def get_recipe_id_for_selection(part_name, subpart_name):
    try:
        conn = pyodbc.connect(conn_str)
        query = f"""
        SELECT [Recipe_id]
        FROM [Pravi_DB].[dbo].[Recipe_Master]
        WHERE Part_name = ? AND Subpart_name = ?
        """
        df = pd.read_sql(query, conn, params=(part_name, subpart_name))
        conn.close()

        if not df.empty:
            return df.iloc[0]["Recipe_id"]
        else:
            print("⚠️ No recipe found for selection.")
            return None

    except Exception as ex:
        print(f"Error while fetching Recipe_ID: {ex}")
        return None


def get_parameters_for_recipe(recipe_id):
    try:
        conn = pyodbc.connect(conn_str)
        query = """
        SELECT [Place], [Parameter], [Value]
        FROM [Pravi_DB].[dbo].[StationParameterDetail]
        WHERE RecipeID = ?
        """
        df = pd.read_sql(query, conn, params=(recipe_id,))
        conn.close()

        # Create a lookup like { "SP:Conveyor1Speed": 22 }
        param_dict = {
            f"{row['Place']}:{row['Parameter']}": row['Value']
            for _, row in df.iterrows()
        }

        return param_dict

    except Exception as ex:
        print(f"Error getting parameters: {ex}")
        return {}


def build_command_sequence(param_dict):
    command_sequence = []

    # Example: looking for value of Conveyor1Speed at SP
    key = "SP:Conveyor1Speed"
    conv1_speed = param_dict.get(key)

    if conv1_speed is not None:
        command = f"$CONV1_SPD={conv1_speed}#\r\n"
        expected_ack = "ACK_CONV1_SPD"
        command_sequence.append((command, expected_ack))
        print(f"🔧 Built command: {command.strip()}")
    else:
        print(f"⚠️ Missing parameter: {key}")

    return command_sequence


def get_stationparameter_detail():
    try:
        conn = pyodbc.connect(conn_str)  # Make sure conn_str is defined
        query = """
        SELECT TOP (1000) [RecipeID], [Place], [Parameter], [Value]
        FROM [Pravi_DB].[dbo].[StationParameterDetail]
        """
        
        df = pd.read_sql(query, conn)
        print(df)
        conn.close()

        # Convert DataFrame to list of dicts
        station_list = df.to_dict(orient='records')

     
        return station_list

    except Exception as ex:
        print(f"Error while fetching StationParameterDetail data: {ex}")
        return None    


def get_recipe_master_data():
    try:
        conn = pyodbc.connect(conn_str)  # Ensure your conn_str is defined
        query = """
        SELECT TOP (1000) [Part_name], [Subpart_name], [Recipe_id]
        FROM [Pravi_DB].[dbo].[Recipe_Master]
        """
        
        df = pd.read_sql(query, conn)
        print(df)
        conn.close()

        # Convert DataFrame to list of dictionaries
        recipe_list = df.to_dict(orient='records')

      
        return recipe_list

    except Exception as ex:
        print(f"Error while fetching Recipe_Master data: {ex}")
        return None
    
# def get_stationparameter_detail():
#     try:
#         conn = pyodbc.connect(conn_str)  # Make sure conn_str is defined correctly

#         query = """
#         SELECT TOP (1000) [RecipeID], [Place], [Parameter], [Value]
#         FROM [Pravi_DB].[dbo].[StationParameterDetail]
#         """
        
#         station_data = pd.read_sql(query, conn)
#         print(station_data)

#         conn.close()
#         return station_data

#     except Exception as ex:
#         print(f"Error while fetching StationParameterDetail data: {ex}")
#         return None    
 
def get_workpartdetail():
    
    try:

        conn = pyodbc.connect(conn_str)
        
        query = f"SELECT * FROM Work_Part_Detail"
        
        workpartdetail_data = pd.read_sql(query, conn)

        print(workpartdetail_data)

        conn.close()

        return workpartdetail_data

    except Exception as ex:
        print(f"Error while Getting Work part detail Data!: {ex}")
        return None


def insert_workpartdetail_1st_Station(date_time, part_name, subpart_name, part_id, current_station, ID, OD, orifice,
                          concentricity, dimension_cam_image, dimension_result, dimension_cam_error_description,
                          thickness_cam_image, thickness_result, thickness_cam_error_description, topburr_cam_image,
                          topburr_result, topburr_cam_error_description, bottom_cam_image, bottom_result,
                          bottom_cam_error_description, supplier_name, invoice_no):
                                  
                        #   datetime, partname, subpartname, p1s1, 1, 10, 20, 30, 40, dimensionImage.png, OK, ID_is_not_good, na, na, na, na, na, na, na, na, na, suppliername, invoice123 

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        query = """
        INSERT INTO Work_Part_Detail (Date_time, Part_Name, Subpart_Name, Part_ID, Current_Station,
        ID, OD, Orifice, Concentricity, Dimension_Cam_Image, Dimension_Result, Dimension_Cam_Error_Description,
        Thickness_Cam_Image, Thickness_Result, Thickness_Cam_Error_Description, 
        TopBurr_Cam_Image, TopBurr_Result, TopBurr_Cam_Error_Description, 
        Bottom_Cam_Image, Bottom_Result, Bottom_Cam_Error_Description, Supplier_Name, Invoice_No)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (date_time, part_name, subpart_name, part_id, current_station, ID, OD, orifice,
                               concentricity, dimension_cam_image, dimension_result, dimension_cam_error_description,
                               thickness_cam_image, thickness_result, thickness_cam_error_description, topburr_cam_image,
                               topburr_result, topburr_cam_error_description, bottom_cam_image, bottom_result,
                               bottom_cam_error_description, supplier_name, invoice_no))
        
        conn.commit()
        conn.close()
        print("Record inserted successfully.")
    except Exception as ex:
        print(f"Error while inserting data: {ex}")


def update_workpartdetail_2nd_Station(current_station, result, thickness_error):
    
    try:

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        query = """
        UPDATE Work_Part_Detail
        SET Current_Station = ?, Thickness_Result = ?, Thickness_Cam_Error_Description = ?
        WHERE S_No = ?
        """
        
        cursor.execute(query, ( current_station, result, thickness_error))
        
        conn.commit()
        conn.close()
        print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")


def update_workpartdetail_3rd_Station(result, Error, BurrStatus, BurrCount):
    try:
        # conn = pyodbc.connect(conn_str)
        # cursor = conn.cursor()
        
        # query = """
        # UPDATE Work_Part_Detail
        # SET Date_time = ?, Part_Name = ?, Subpart_Name = ?, Part_ID = ?, Current_Station = ?, ID = ?, OD = ?, Orifice = ?,
        #     Concentricity = ?, Dimension_Cam_Image = ?, Dimension_Result = ?, Dimension_Cam_Error_Description = ?,
        #     Thickness_Cam_Image = ?, Thickness_Result = ?, Thickness_Cam_Error_Description = ?, TopBurr_Cam_Image = ?,
        #     TopBurr_Result = ?, TopBurr_Cam_Error_Description = ?, Bottom_Cam_Image = ?, Bottom_Result = ?,
        #     Bottom_Cam_Error_Description = ?, Supplier_Name = ?, Invoice_No = ?
        # WHERE S_No = ?
        # """
        
        # cursor.execute(query, ())
        
        # conn.commit()
        # conn.close()
        print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")


def update_workpartdetail_4th_Station(result, Error, BurrStatus, BurrCount):
    try:
        # conn = pyodbc.connect(conn_str)
        # cursor = conn.cursor()
        
        # query = """
        # UPDATE Work_Part_Detail
        # SET Date_time = ?, Part_Name = ?, Subpart_Name = ?, Part_ID = ?, Current_Station = ?, ID = ?, OD = ?, Orifice = ?,
        #     Concentricity = ?, Dimension_Cam_Image = ?, Dimension_Result = ?, Dimension_Cam_Error_Description = ?,
        #     Thickness_Cam_Image = ?, Thickness_Result = ?, Thickness_Cam_Error_Description = ?, TopBurr_Cam_Image = ?,
        #     TopBurr_Result = ?, TopBurr_Cam_Error_Description = ?, Bottom_Cam_Image = ?, Bottom_Result = ?,
        #     Bottom_Cam_Error_Description = ?, Supplier_Name = ?, Invoice_No = ?
        # WHERE S_No = ?
        # """
        
        # cursor.execute(query, ())
        
        # conn.commit()
        # conn.close()
        print("Record updated successfully.")
    except Exception as ex:
        print(f"Error while updating data: {ex}")


def update_defect_count(parameter: str):
    """
    Increments the count for the given parameter ("OK" or "NOK") in Defect_Count.
    If the row doesn't exist, it inserts it with count = 1.
    """
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        # Try to update an existing row
        rows = cursor.execute(
            "UPDATE [Pravi_DB].[dbo].[Defect_Count] "
            "SET Counts = Counts + 1 "
            "WHERE [Parameter] = ?", (parameter,)
        ).rowcount

        if rows == 0:
            # No existing row, insert a new one
            cursor.execute(
                "INSERT INTO [Pravi_DB].[dbo].[Defect_Count] ([Parameter], [Counts]) "
                "VALUES (?, 1)",
                (parameter,)
            )

        conn.commit()
        conn.close()
    except Exception as ex:
        print(f"Error upserting Defect_Count for {parameter}: {ex}")


def insert_defect_count(parameter: str, counts: int):
    """
    Inserts a new row into the Defect_Count table.

    :param parameter: The name of the defect parameter.
    :param counts: The count associated with that defect.
    """
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        query = """
            INSERT INTO [Pravi_DB].[dbo].[Defect_Count]
                ([Parameter], [Counts])
            VALUES (?, ?)
        """
        cursor.execute(query, (parameter, counts))
        conn.commit()
        conn.close()
        print(f"Inserted Defect_Count: ({parameter}, {counts})")
    except Exception as ex:
        print(f"Error inserting into Defect_Count: {ex}")


def get_recipe_id(part, subpart):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT RecipeID FROM Recipe_Master 
        WHERE Part_name = ? AND Subpart_name = ?
    """, part, subpart)
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_station_parameters(recipe_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Place, Parameter, Value 
        FROM StationParameterDetail 
        WHERE RecipeID = ?
    """, recipe_id)
    rows = cursor.fetchall()
    conn.close()
    return [{'Place': r.Place, 'Parameter': r.Parameter, 'Value': r.Value} for r in rows]


def update_station_parameters(recipe_id, param_list):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    for param in param_list:
        cursor.execute("""
          UPDATE StationParameterDetail 
          SET Value = ? 
          WHERE RecipeID = ? AND Place = ? AND Parameter = ?
          """, param['Value'].strip(), recipe_id.strip(), param['Place'].strip(), param['Parameter'].strip())

    conn.commit()
    conn.close()


def get_work_part_details():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP (1000) * FROM Work_Part_Detail ORDER BY S_No DESC
    """)
    columns = [column[0] for column in cursor.description]
    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return result


def execute_query(query, params=None):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results


def get_recipe_id(part, subpart):
    query = """
    SELECT Recipe_id FROM Recipe_Master
    WHERE Part_name = ? AND Subpart_name = ?
    """
    result = execute_query(query, (part, subpart))
    return result[0]['Recipe_id'] if result else None


def get_station_parameters(recipe_id):
    query = """
    SELECT Place, Parameter, Value FROM StationParameterDetail
    WHERE RecipeID = ?
    """
    return execute_query(query, (recipe_id,))


def get_part_data():
   
    return {
        'Date_time': '2025-03-31 12:00:00',
        'Part_Name': 'PartB',
        'Subpart_Name': 'Sub2',
        'Part_ID': 'P002',
        'Current_Station': 'StationY',
        'ID': 102,
        'OD': 52.0,
        'Orifice': 1.5,
        'Concentricity': 0.02,
        'Dimension_Cam_Image': 'dim_image.jpg',
        'Dimension_Result': 'Pass',
        'Dimension_Cam_Error_Description': '',
        'Thickness_Cam_Image': 'thick_image.jpg',
        'Thickness_Result': 'Fail',
        'Thickness_Cam_Error_Description': 'Low thickness',
        'TopBurr_Cam_Image': 'top_image.jpg',
        'TopBurr_Result': 'Pass',
        'TopBurr_Cam_Error_Description': '',
        'Bottom_Cam_Image': 'bottom_image.jpg',
        'Bottom_Result': 'Pass',
        'Bottom_Cam_Error_Description': '',
        'Supplier_Name': 'XYZ Ltd',
        'Invoice_No': 'INV5678'
    }


def insert_dict_into_db(data_dict):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO Work_Part_Detail (
                Date_time, Part_Name, Subpart_Name, Part_ID, Current_Station,
                ID, OD, Orifice, Concentricity, Dimension_Cam_Image,
                Dimension_Result, Dimension_Cam_Error_Description, Thickness_Cam_Image,
                Thickness_Result, Thickness_Cam_Error_Description, TopBurr_Cam_Image,
                TopBurr_Result, TopBurr_Cam_Error_Description, Bottom_Cam_Image,
                Bottom_Result, Bottom_Cam_Error_Description, Supplier_Name, Invoice_No
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(insert_query, (
            data_dict['Date_time'], data_dict['Part_Name'], data_dict['Subpart_Name'], data_dict['Part_ID'],
            data_dict['Current_Station'], data_dict['ID'], data_dict['OD'], data_dict['Orifice'],
            data_dict['Concentricity'], data_dict['Dimension_Cam_Image'], data_dict['Dimension_Result'],
            data_dict['Dimension_Cam_Error_Description'], data_dict['Thickness_Cam_Image'],
            data_dict['Thickness_Result'], data_dict['Thickness_Cam_Error_Description'],
            data_dict['TopBurr_Cam_Image'], data_dict['TopBurr_Result'],
            data_dict['TopBurr_Cam_Error_Description'], data_dict['Bottom_Cam_Image'],
            data_dict['Bottom_Result'], data_dict['Bottom_Cam_Error_Description'],
            data_dict['Supplier_Name'], data_dict['Invoice_No']
        ))

        conn.commit()
        print("Data inserted successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        conn.close()


def PythonResultProcessing():
    
    # 1st Station  
    # OK 
    #insert into list

    # NOK
    #insert into db table


    # 2nd Station   
    # OK
    #update the list 

    # NOK
    #take the data frrom the list and insert into db table

    # 3rd Station
    # OK
    # update the list
    # NOK


    # 4th Station    
    
    # OK
    
    # NOK
    
    return None

#if __name__ == '__main__':
    #  get_recipe_master_data()
    #  get_stationparameter_detail()
    #  print("Done")
     #get_python_parameters('P1S1')

    



