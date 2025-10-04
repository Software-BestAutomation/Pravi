import sys
import os
import neoapi
import time
import datetime

# Create camera objects
camera1 = neoapi.Cam()
camera2 = neoapi.Cam()
camera3 = neoapi.Cam()
camera4 = neoapi.Cam()


# Function to connect to cameras
def camera_connect1():
    try:
        camera1.Connect('700012114996')  #700009456892 fixed camera ID 700011425074 700011425074
        camera1.f.ExposureTime.Set(1200)        #2500
        print('Camera 1 Connected!')
        return True
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 1 error:', exc)
        return False
  
def camera_connect2():
    try:
        camera2.Connect('700009729305')  #700009729305 fixed camera ID
        camera2.f.ExposureTime.Set(1000)
        print('Camera 2 Connected!')
        return True
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 2 error:', exc)
        return False

def camera_connect3():
    try:
        camera3.Connect('700009600803')
        camera3.f.ExposureTime.Set(5000)
        print('Camera 3 Connected!')
        return True
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 3 error:', exc)
        return False

def camera_connect4():
    try:
        camera4.Connect('700009600797') #700009600797 fixed camera ID
        camera4.f.ExposureTime.Set(8000)
        print('Camera 4 Connected!')
        return True
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 4 error:', exc)
        return False


# Function to check if cameras are connected
def isConnectedCamera1():
    try:
        if camera1.IsConnected():
            print('Camera 1 Status: Connected!')
            return True
        else:
            print('Camera 1 Status: Not Connected!')
            return False
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 1 error:', exc)
        return False

def isConnectedCamera2():
    try:
        if camera2.IsConnected():
            print('Camera 2 Status: Connected!')
            return True
        else:
            print('Camera 2 Status: Not Connected!')
            return False
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 2 error:', exc)
        return False

def isConnectedCamera3():
    try:
        if camera3.IsConnected():
            print('Camera 3 Status: Connected!')
            return True
        else:
            print('Camera 3 Status: Not Connected!')
            return False
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 3 error:', exc)
        return False

def isConnectedCamera4():
    try:
        if camera4.IsConnected():
            print('Camera 4 Status: Connected!')
            return True
        else:
            print('Camera 4 Status: Not Connected!')
            return False
    except (neoapi.NeoException, Exception) as exc:
        print('Camera 4 error:', exc)
        return False


# Function to capture images from cameras

def capture_image_1():
    try:
        print("Capture is triggered for CAM_1")
        start_time = time.time()
        image = camera1.GetImage()
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam1.bmp"  
        input_backup_cam_1 = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam1"

        # ensure dated/hourly backup folder exists and save timestamped BMP
        date_folder = time.strftime("%Y-%m-%d")
        hour_folder = time.strftime("%H")
        backup_dir_1 = os.path.join(input_backup_cam_1, date_folder, hour_folder)
        os.makedirs(backup_dir_1, exist_ok=True)
        backup_path_1 = os.path.join(backup_dir_1, f"cam1_{timestamp}.png")
        image.Save(backup_path_1)

        # ensure base_path directory exists and save latest image
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        image.Save(base_path)

        img = image.GetNPArray()
        end_time = time.time()
        execution_time = "{:.3f}".format((end_time - start_time) * 1000)
        print(f'Time taken to capture Image for CAM_1: {execution_time} ms\nSaved: {base_path}')
        return img
    except (neoapi.NeoException, Exception) as exc:
        print('Error: ', exc)
        return 0



def capture_image_2():
    try:
        print("Capture is triggered for CAM_2")
        start_time = time.time()
        image = camera2.GetImage()
        img = image.GetNPArray()
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam2.bmp"  # 
        input_backup_cam_2 = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam2"

        # ensure dated/hourly backup folder exists and save timestamped BMP
        date_folder = time.strftime("%Y-%m-%d")
        hour_folder = time.strftime("%H")
        backup_dir_2 = os.path.join(input_backup_cam_2, date_folder, hour_folder)
        os.makedirs(backup_dir_2, exist_ok=True)
        backup_path_2 = os.path.join(backup_dir_2, f"cam2_{timestamp}.png")
        image.Save(backup_path_2)

        # ensure base_path directory exists and save latest image
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        image.Save(base_path)

        end_time = time.time()
        execution_time = "{:.3f}".format((end_time - start_time) * 1000)
        print(f'Time taken to capture Image for CAM_2: {execution_time} ms\nSaved: {base_path}')
        return img
    except (neoapi.NeoException, Exception) as exc:
        print('Error: ', exc)
        return 0

def capture_image_3():
    try:
        print("Capture is triggered for CAM_3")
        start_time = time.time()
        image = camera3.GetImage()
        img = image.GetNPArray()
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam3.bmp"
        input_backup_cam_3 = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam3"

        # ensure dated/hourly backup folder exists and save timestamped BMP
        date_folder = time.strftime("%Y-%m-%d")
        hour_folder = time.strftime("%H")
        backup_dir_3 = os.path.join(input_backup_cam_3, date_folder, hour_folder)
        os.makedirs(backup_dir_3, exist_ok=True)
        backup_path_3 = os.path.join(backup_dir_3, f"cam3_{timestamp}.png")
        image.Save(backup_path_3)

        # ensure base_path directory exists and save latest image
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        image.Save(base_path)

        end_time = time.time()
        execution_time = "{:.3f}".format((end_time - start_time) * 1000)
        print(f'Time taken to capture Image for CAM_3: {execution_time} ms\nSaved: {base_path}')
        return img
    except (neoapi.NeoException, Exception) as exc:
        print('Error: ', exc)
        return 1

def capture_image_4():
    try:
        print("Capture is triggered for CAM_4")
        start_time = time.time()
        image = camera4.GetImage()
        img = image.GetNPArray()
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
        input_backup_cam_4 = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam4"

        # ensure dated/hourly backup folder exists and save timestamped BMP
        date_folder = time.strftime("%Y-%m-%d")
        hour_folder = time.strftime("%H")
        backup_dir_4 = os.path.join(input_backup_cam_4, date_folder, hour_folder)
        os.makedirs(backup_dir_4, exist_ok=True)
        backup_path_4 = os.path.join(backup_dir_4, f"cam4_{timestamp}.png")
        image.Save(backup_path_4)

        # ensure base_path directory exists and save latest image
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        image.Save(base_path)

        end_time = time.time()
        execution_time = "{:.3f}".format((end_time - start_time) * 1000)
        print(f'Time taken to capture Image for CAM_4: {execution_time} ms\nSaved: {base_path}')
        return img
    except (neoapi.NeoException, Exception) as exc:
        print('Error: ', exc)
        return 1

def camera_disconnect():
    try:
        camera1.Disconnect()
        camera2.Disconnect()
        camera3.Disconnect()
        camera4.Disconnect()
        print('All Cameras Disconnected Successfully!')
    except (neoapi.NeoException, Exception) as exc:
        print('error: ', exc)


#if __name__ == '__main__':
     #camera_connect1()
     #camera_connect2()
     #capture_image_1()
     #capture_image_2()
     #camera_disconnect()






















## working 3 oct 2025
# import sys
# import os
# import neoapi
# import time
# import datetime

# # Create camera objects
# camera1 = neoapi.Cam()
# camera2 = neoapi.Cam()
# camera3 = neoapi.Cam()
# camera4 = neoapi.Cam()


# # Function to connect to cameras
# def camera_connect1():
#     try:
#         camera1.Connect('700012114996')  #700009456892 fixed camera ID 700011425074 700011425074
#         camera1.f.ExposureTime.Set(1200)        #2500
#         print('Camera 1 Connected!')
#         return True
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 1 error:', exc)
#         return False
  
# def camera_connect2():
#     try:
#         camera2.Connect('700009729305')  #700009729305 fixed camera ID
#         camera2.f.ExposureTime.Set(1000)
#         print('Camera 2 Connected!')
#         return True
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 2 error:', exc)
#         return False

# def camera_connect3():
#     try:
#         camera3.Connect('700009600803')
#         camera3.f.ExposureTime.Set(5000)
#         print('Camera 3 Connected!')
#         return True
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 3 error:', exc)
#         return False

# def camera_connect4():
#     try:
#         camera4.Connect('700009600797') #700009600797 fixed camera ID
#         camera4.f.ExposureTime.Set(8000)
#         print('Camera 4 Connected!')
#         return True
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 4 error:', exc)
#         return False


# # Function to check if cameras are connected
# def isConnectedCamera1():
#     try:
#         if camera1.IsConnected():
#             print('Camera 1 Status: Connected!')
#             return True
#         else:
#             print('Camera 1 Status: Not Connected!')
#             return False
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 1 error:', exc)
#         return False

# def isConnectedCamera2():
#     try:
#         if camera2.IsConnected():
#             print('Camera 2 Status: Connected!')
#             return True
#         else:
#             print('Camera 2 Status: Not Connected!')
#             return False
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 2 error:', exc)
#         return False

# def isConnectedCamera3():
#     try:
#         if camera3.IsConnected():
#             print('Camera 3 Status: Connected!')
#             return True
#         else:
#             print('Camera 3 Status: Not Connected!')
#             return False
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 3 error:', exc)
#         return False

# def isConnectedCamera4():
#     try:
#         if camera4.IsConnected():
#             print('Camera 4 Status: Connected!')
#             return True
#         else:
#             print('Camera 4 Status: Not Connected!')
#             return False
#     except (neoapi.NeoException, Exception) as exc:
#         print('Camera 4 error:', exc)
#         return False


# # Function to capture images from cameras

# def capture_image_1():
#     try:
#         print("Capture is triggered for CAM_1")
#         start_time = time.time()
#         image = camera1.GetImage()
        
#         timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
#         base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam1.bmp"  
#         input_backup_cam_1=r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam1"
#         image.Save(f"{input_backup_cam_1}_{timestamp}",)
#         # D:\PIM_15-09-25\Pravi_Flask\static\Cam1InputImages
#         image.Save(base_path)
#         img = image.GetNPArray()
#         # print(f"image: {image}")
#         # print(f"img: {img}")
#         end_time = time.time()
#         execution_time = "{:.3f}".format((end_time - start_time) * 1000)
#         print(f'Time taken to capture Image for CAM_1: {execution_time} ms\nSaved: {base_path}')
#         return img
#     except (neoapi.NeoException, Exception) as exc:
#         print('Error: ', exc)
#         return 0



# def capture_image_2():
#     try:
#         print("Capture is triggered for CAM_2")
#         start_time = time.time()
#         image = camera2.GetImage()
#         img = image.GetNPArray()
#         timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
#         base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam2.bmp"  # 
#         input_backup_cam_2=r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam2"
#         image.Save(f"{input_backup_cam_2}_{timestamp}",)
#         image.Save(base_path) 
#         end_time = time.time()
#         execution_time = "{:.3f}".format((end_time - start_time) * 1000)
#         print(f'Time taken to capture Image for CAM_2: {execution_time} ms\nSaved: {base_path}')
#         return img
#     except (neoapi.NeoException, Exception) as exc:
#         print('Error: ', exc)
#         return 0

# def capture_image_3():
#     try:
#         print("Capture is triggered for CAM_3")
#         start_time = time.time()
#         image = camera3.GetImage()
#         img = image.GetNPArray()
#         timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
#         base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam3.bmp"
#         input_backup_cam_3=r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam3"
#         image.Save(f"{input_backup_cam_3}_{timestamp}",)
#         image.Save(base_path)
#         end_time = time.time()
#         execution_time = "{:.3f}".format((end_time - start_time) * 1000)
#         print(f'Time taken to capture Image for CAM_3: {execution_time} ms\nSaved: {base_path}')
#         return img
#     except (neoapi.NeoException, Exception) as exc:
#         print('Error: ', exc)
#         return 1

# def capture_image_4():
#     try:
#         print("Capture is triggered for CAM_4")
#         start_time = time.time()
#         image = camera4.GetImage()
#         img = image.GetNPArray()
#         timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
#         base_path = r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\cam4.bmp"
#         input_backup_cam_4=r"D:\PIM_25-09-25\Pravi_Flask\static\Cam1InputImages\input_backup_cam4"
#         image.Save(f"{input_backup_cam_4}_{timestamp}",)
#         image.Save(base_path)
#         end_time = time.time()
#         execution_time = "{:.3f}".format((end_time - start_time) * 1000)
#         print(f'Time taken to capture Image for CAM_4: {execution_time} ms\nSaved: {base_path}')
#         return img
#     except (neoapi.NeoException, Exception) as exc:
#         print('Error: ', exc)
#         return 1

# def camera_disconnect():
#     try:
#         camera1.Disconnect()
#         camera2.Disconnect()
#         camera3.Disconnect()
#         camera4.Disconnect()
#         print('All Cameras Disconnected Successfully!')
#     except (neoapi.NeoException, Exception) as exc:
#         print('error: ', exc)


# #if __name__ == '__main__':
#      #camera_connect1()
#      #camera_connect2()
#      #capture_image_1()
#      #capture_image_2()
#      #camera_disconnect()
  