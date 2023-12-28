from io import BytesIO
import tkinter as tk
from PIL import ImageTk, Image, ImageDraw
import requests
from PIL import Image
import mysql.connector

IMG_ADDRESS_ROOT = "http://ktamv.ignat.se/nozzle_pics/"
CIRCLE_RADIUS = 10

current_frame = 0
changed_frames = []
frames = []

def reset_frames():
    status_label.config(text="Resetting frames")
    global current_frame
    global changed_frames
    global frames
    
    current_frame = 0
    changed_frames = []
    frames = []
    
    nozle_img = ImageTk.PhotoImage(Image.new('RGB', (640, 480), color = 'gray'))
    nozzle_widget.config(image=nozle_img)
    nozzle_widget.image = nozle_img
    
def load_image(nr: int):
    url = IMG_ADDRESS_ROOT + str(frames[nr][0]) + ".jpg"
    # print(url)
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Image could not be loaded: " + str(response.status_code))
        img= Image.open(BytesIO(response.content),formats=['jpeg'])
        draw = ImageDraw.Draw(img)
        print(frames[nr][2])
        coords = frames[nr][2].strip("()").split(", ")
        coords = [int(i) for i in coords]

        draw.ellipse(( coords[0] - CIRCLE_RADIUS,
                    coords[1] - CIRCLE_RADIUS,
                    coords[0] + CIRCLE_RADIUS, 
                    coords[1] + CIRCLE_RADIUS),
                    fill=(255, 0, 0, 255))
        
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

def fetch_db(getall=False):
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

    if getall:
        cursor.execute("SELECT id, status, points FROM `Frames` LIMIT 10;")
    else:
        cursor.execute("SELECT id, status, points FROM `Frames` WHERE status = 0 LIMIT 100;")
    
    global frames
    
    
    frames = [list(i) for i in cursor.fetchall()]

    status_label.config(text="Frames fetched")
    
    global current_frame
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

            cursor.execute("UPDATE `Frames` SET status = %s WHERE id = %s;", (frames[i][1], frames[i][0]))
            
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

    if current_frame < len(frames) - 1:
        current_frame += 1
        print("Next nozzle: " + str(current_frame))
        load_image(current_frame)
        set_text_nozzle_nr(current_frame)
    else:
        print("No more nozzles")
        
def get_previous_nozzle():
    global current_frame

    if current_frame > 0:
        current_frame -= 1
        print("Previous nozzle: " + str(current_frame))
        load_image(current_frame)
        set_text_nozzle_nr(current_frame)
    else:
        print("No more nozzles")

def get_first_nozzle():
    global current_frame
    current_frame = 0
    print("First nozzle: " + str(current_frame))
    load_image(current_frame)
    set_text_nozzle_nr(current_frame)
    
def get_last_nozzle():
    global current_frame
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
    print("Frame status changed to: " + str(status))
    get_next_nozzle()
    
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

nozle_img = ImageTk.PhotoImage(Image.new('RGB', (640, 480), color = 'gray'))
nozzle_widget = tk.Label(frame3, image=nozle_img)
nozzle_widget.image = nozle_img
nozzle_widget.pack()

tk.Button(frame4, text="Reset and get unchecked from DB", cursor="hand2", 
          activebackground="green", command=lambda:fetch_db(getall=False)).pack(side="left")
tk.Button(frame4, text="Reset and get all from DB", cursor="hand2", 
          activebackground="green", command=lambda:fetch_db(getall=True)).pack(side="left")
tk.Button(frame4, text="Save to DB", cursor="hand2", activebackground="green",
          command=lambda:save_db()).pack(side="left")

tk.Label(frame5, text="Status: ").pack(side="left")
status_label = tk.Label(frame5, text="Waiting for DB")
status_label.pack(side="left")

password_db = load_password_from_file(".password.txt")

#run the main loop
root.mainloop()

