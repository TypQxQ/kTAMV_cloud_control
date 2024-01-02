from io import BytesIO
import tkinter as tk
from PIL import ImageTk, Image, ImageDraw
import requests
from PIL import Image
import mysql.connector
import OpenCVDetectionModule
import csv
import os

IMG_ADDRESS_ROOT = "http://ktamv.ignat.se/nozzle_pics/"
CIRCLE_RADIUS = 10

current_frame = 0
changed_frames = []
frames = []
new_coordinates = [0, 0, 0]

def reset_frames():
    status_label.config(text="Resetting frames")
    global current_frame
    global changed_frames
    global frames
    
    current_frame = 0
    changed_frames = []
    frames = []
    new_coordinates = [0, 0, 0]
    
    reset_image()
    
def reset_image():
    nozle_img = ImageTk.PhotoImage(Image.new('RGB', (640, 480), color = 'gray'))
    nozzle_widget.config(image=nozle_img)
    nozzle_widget.image = nozle_img
    nozzle_widget.update()
    
def load_image(nr: int):
    url = IMG_ADDRESS_ROOT + str(frames[nr][0]) + ".jpg"
    global new_coordinates
    new_coordinates = [0, 0, 0]
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Image could not be loaded: " + str(response.status_code))
        img= Image.open(BytesIO(response.content),formats=['jpeg'])
        new_coord, img, radius = ocv.nozzleDetection(img)
        print(radius)
        
        coords = frames[nr][2].strip("()").split(", ")
        coords = [int(i) for i in coords]
        if coords != new_coord:
            print("Coords changed")
            print("Old: " + str(coords))
            print("New: " + str(new_coord)) 

            draw = ImageDraw.Draw(img, 'RGBA')

            draw.ellipse(( coords[0] - CIRCLE_RADIUS,
                        coords[1] - CIRCLE_RADIUS,
                        coords[0] + CIRCLE_RADIUS, 
                        coords[1] + CIRCLE_RADIUS),
                        fill=(0, 0, 255, 170))
            new_coordinates = new_coord[0], new_coord[1]
        frames[nr][3] = int(radius)
            
        nozle_img = ImageTk.PhotoImage(img)
        nozzle_widget.config(image=nozle_img)
        nozzle_widget.image = nozle_img

    except Exception as e:
        print("Image could not be loaded: " + str(e))
        status_label.config(text="Image could not be loaded: " + str(e))
        frames[nr][1] = 3 # Set status to Not found
        changed_frames.append(nr)
        get_next_nozzle()
        return
    
def load_password_from_file(filepath):
    with open(filepath, 'r') as file:
        password = file.read().strip()
    status_label.config(text="Password loaded from file")
    return password



def get_previous_nozzle():
    status_label.config(text="Getting previous nozzle")

def fetch_db(get_all=False, get_done=False):
    # Reset all data
    reset_frames()
    
    status_label.config(text="Connecting to DB")
    # Create a connection object
    connection = mysql.connector.connect(
        host="mariadb105.r103.websupport.se",
        user="189138_di76479",
        password=password_db,
        database="189138-ktamv"
    )
    
    status_label.config(text="Executing SQL query")
    # Create a cursor object to execute SQL queries
    cursor = connection.cursor()

    if get_all:
        cursor.execute("SELECT id, status, points, radius FROM `Frames` WHERE id < 80;")
    elif get_done:
        cursor.execute("SELECT id, status, points, radius FROM `Frames` WHERE (status = 1 OR status = 4) AND radius is NOT NULL LIMIT 10;")
    else:
        cursor.execute("SELECT id, status, points, radius FROM `Frames` WHERE status = 0;")
    
    global frames
    
    
    frames = [list(i) for i in cursor.fetchall()]

    status_label.config(text="Frames fetched")
    
    if not get_done:
        load_image(0)
        set_text_nozzle_nr(current_frame)

    # Close the cursor and connection
    cursor.close()
    connection.close()

def save_db():
    status_label.config(text="Saving to DB")

    try:
        # Create a connection object
        connection = mysql.connector.connect(
            host="mariadb105.r103.websupport.se",
            user="189138_di76479",
            password=password_db,
            database="189138-ktamv"
        )
            
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        for i in changed_frames:
            print("Saving frame: " + str(i))
            print("Saving id: " + str(frames[i][0]))
            
            cursor.execute("UPDATE `Frames` SET status = %s, points=%s, radius = %s WHERE id = %s;", (frames[i][1], frames[i][2], frames[i][3], frames[i][0]))
            
                
        connection.commit()
    except Exception as e:
        print("Error saving to DB: " + str(e))
        status_label.config(text="Error saving to DB: " + str(e))
    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
        print("DB Connection closed")

def get_next_nozzle():
    global current_frame
    
    reset_image()

    if current_frame < len(frames) - 1:
        current_frame += 1
        print("Next nozzle: " + str(current_frame))
        load_image(current_frame)
        set_text_nozzle_nr(current_frame)
    else:
        print("No more nozzles")
        
def get_previous_nozzle():
    global current_frame
    
    reset_image()

    if current_frame > 0:
        current_frame -= 1
        print("Previous nozzle: " + str(current_frame))
        load_image(current_frame)
        set_text_nozzle_nr(current_frame)
    else:
        print("No more nozzles")

def get_first_nozzle():
    global current_frame
    
    reset_image()
    
    current_frame = 0
    print("First nozzle: " + str(current_frame))
    load_image(current_frame)
    set_text_nozzle_nr(current_frame)
    
def get_last_nozzle():
    global current_frame
    reset_image()
    current_frame = len(frames) - 1
    print("Last nozzle: " + str(current_frame))
    load_image(current_frame)
    set_text_nozzle_nr(current_frame)

def set_text_nozzle_nr(nr : int):
    if frames[nr][1] == 0:
        color = "yellow"
    elif frames[nr][1] == 1:
        color = "green"
    else:
        color = "red"
        
    nozzlenr_label.config(text="Nozzle Nr. "+ str(nr+1) + "/" + str(len(frames)), bg=color)
    
def set_frame_status(status : int):
    global current_frame
    global changed_frames
    
    frames[current_frame][1] = status
    changed_frames.append(current_frame)
    if (status == 1 or status == 4) and new_coordinates != [0, 0, 0]:
        frames[current_frame][2] = str(new_coordinates)
        print("Saved new coordinates for ID: " + str(frames[current_frame][0]))
        
    print("Frame status changed to: " + str(status))
    get_next_nozzle()
    
# Save all labels for YOLOv5
def save_all_labels_yolo5():
    global current_frame
    
    fetch_db(get_done=True)
    
    reset_image()

    for i in range(len(frames)):
        current_frame = i
        print("Next nozzle: " + str(current_frame))
        set_text_nozzle_nr(current_frame)
        if frames[current_frame][1] == 1:
            save_label_yolo5(type=0, frame=current_frame)
        elif frames[current_frame][1] == 4:
            save_label_yolo5(type=1, frame=current_frame)

    print("No more nozzles")
        
def save_label_yolo5(frame : int, type=0):
    folder_path = "annotations"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    print("Saving label for frame: " + str(frame) + " of " + str(len(frames)) + " id: " + str(frames[frame][0])) 
    
    file_path = os.path.join(folder_path, str(frames[frame][0]) + ".txt")
    
    x, y = frames[frame][2].strip("()").split(", ")    
    x = str(int(x)/640)
    y= str(int(y)/480)
    radius_x = str(int(frames[frame][3])/640)
    radius_y = str(int(frames[frame][3])/480)
    # radius = frames[frame][3]
    
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=' ')
        writer.writerow([type, x, y, radius_x, radius_y ])

    
# initialize tkinter
root = tk.Tk()
root.title("Ktamv Validator")
root.geometry("640x580")
# root.eval('tk::PlaceWindow . center')

# Create a frame widget
frame1 = tk.Frame(root)
frame1.grid(row=0, column=0)
frame2 = tk.Frame(root)
frame2.grid(row=1, column=0)
frame3 = tk.Frame(root)
frame3.grid(row=2, column=0)
frame4 = tk.Frame(root)
frame4.grid(row=3, column=0)
frame5 = tk.Frame(root)
frame5.grid(row=4, column=0)

tk.Button(frame1, text="<<", cursor="hand2", activebackground="green", 
          command=lambda:get_first_nozzle()).pack(side="left")
tk.Button(frame1, text="<", cursor="hand2", activebackground="green", 
          command=lambda:get_previous_nozzle()).pack(side="left")

nozzlenr_label = tk.Label(frame1, text="Nozzle Nr.")
nozzlenr_label.pack(side="left")

tk.Button(frame1, text=">", cursor="hand2", activebackground="green", 
          command=lambda:get_next_nozzle()).pack(side="left")
tk.Button(frame1, text=">>", cursor="hand2", activebackground="green", 
          command=lambda:get_last_nozzle()).pack(side="left")

tk.Button(frame2, text="Not good", cursor="hand2", 
          activebackground="orange", bg="red", 
          command=lambda:set_frame_status(2)).pack(side="left")
tk.Button(frame2, text="Good", cursor="hand2", 
          activebackground="green", bg="green", 
          command=lambda:set_frame_status(1)).pack(side="left")

tk.Label(frame2, text="     ").pack(side="left")

tk.Button(frame2, text="Endstop: Not good", cursor="hand2", 
          activebackground="orange", bg="red", 
          command=lambda:set_frame_status(5)).pack(side="left")
tk.Button(frame2, text="Endstop: Good", cursor="hand2", 
          activebackground="green", bg="green", 
          command=lambda:set_frame_status(4)).pack(side="left")


nozzle_widget = tk.Label(frame3)
reset_image()
nozzle_widget.pack()

tk.Button(frame4, text="Reset and get unchecked from DB", cursor="hand2", 
          activebackground="green", command=lambda:fetch_db(get_all=False)).pack(side="left")
tk.Button(frame4, text="Reset and get all from DB", cursor="hand2", 
          activebackground="green", command=lambda:fetch_db(get_all=True)).pack(side="left")
tk.Button(frame4, text="Save to DB", cursor="hand2", activebackground="green",
          command=lambda:save_db()).pack(side="left")
tk.Button(frame4, text="Save all Anotations", cursor="hand2", activebackground="green",
          command=lambda:save_all_labels_yolo5()).pack(side="left")
tk.Button(frame4, text="Reload image", cursor="hand2", activebackground="green",
          command=lambda:load_image(current_frame)).pack(side="left")

tk.Label(frame5, text="Status: ").pack(side="left")
status_label = tk.Label(frame5, text="Waiting for DB")
status_label.pack(side="left")

password_db = load_password_from_file(".password.txt")

ocv = OpenCVDetectionModule.OpenCVDetectionModule()

#run the main loop
root.mainloop()

