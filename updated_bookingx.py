
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import sqlite3
from twilio.rest import Client

account_sid = 'AC45c0811b26294556eacb598e800c5036'#Replace with your Twilio Account SID
auth_token = '1dc76b5f11cbd29671757dfe02e5b734'# Replace with your Twilio Auth Token
twilio_number = '+17202550212'  # Replace with your Twilio phone number

# Function to connect to the database
def connect_db():
    conn = sqlite3.connect('flight_book4.db')
    conn.execute("PRAGMA foreign_keys = 1")  # Enable foreign key constraints
    return conn

# Function to create the database tables if they do not exist
def setup_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        dob TEXT,
        gender TEXT,
        phone TEXT,
        email TEXT,
        nationality TEXT)''')

    # Create flights table
    cursor.execute('''CREATE TABLE IF NOT EXISTS flights (
        flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_name TEXT,
        departure TEXT,
        destination TEXT,
        flight_date TEXT,
        starting_time TEXT,
        arrival_time TEXT,
        seats_available INTEGER,
        price REAL)''')

    # Create bookings table
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER,
        user_name TEXT,
        seat_number TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        booking_date TEXT,
        payment_status TEXT,
        FOREIGN KEY(flight_id) REFERENCES flights(flight_id))''')

    # Insert dummy flight data (ignore if exists)
    cursor.execute('''INSERT OR IGNORE INTO flights 
                      (flight_name, departure, destination, flight_date, starting_time, arrival_time, seats_available, price)
                      VALUES 
                      ('Indigo', 'chennai', 'newdelhi', '2024-10-20', '08:00', '12:00', 10, 20000.00),
                      ('AirIndia', 'chennai', 'tuticorin', '2024-10-21', '10:00', '12:30', 5, 5000.00),
                      ('Vistara', 'chennai', 'mumbai', '2024-10-22', '14:00', '16:45', 8, 6300.00)''')

    conn.commit()

    conn.commit()
    conn.close()
# Function for user sign up with error handling
def signup(username, password, dob, gender, phone, email, nationality):
    if not all([username, password, dob, gender, phone, email, nationality]):
        messagebox.showerror("Error", "All fields are required!")
        return

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO users (username, password, dob, gender, phone, email, nationality)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, dob, gender, phone, email, nationality))
        
        conn.commit()
        messagebox.showinfo("Success", "Sign up successful!")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
    finally:
        conn.close()

# Function for user sign in
def signin(username, password):
    if not username or not password:
        messagebox.showerror("Error", "Both username and password are required!")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        messagebox.showinfo("Success", "Sign in successful!")
        open_flight_search_page()
    else:
        messagebox.showerror("Error", "Invalid username or password.")

# Sign up page function
def open_signup_page():
    signup_window = tk.Toplevel(root)
    signup_window.title("Sign Up")
    signup_window.geometry("700x600")
    signup_window.configure(bg='#F0F8FF')  # Light blue background
    
    # Add Entry Fields and Labels
    fields = [("Username",), ("Password",), ("Date of Birth",), ("Gender",), 
              ("Phone",), ("Email",), ("Nationality",)]
    entries = []

    for field in fields:
        tk.Label(signup_window, text=field, bg='#F0F8FF', fg='#000080', font=('Arial', 12)).pack(pady=5)
        entry = tk.Entry(signup_window)
        entry.pack(pady=5)
        entries.append(entry)
    
    tk.Button(signup_window, text="Complete Sign Up", command=lambda: signup(
        entries[0].get(), entries[1].get(), entries[2].get(), "Male",
        entries[4].get(), entries[5].get(), entries[6].get()), bg='#ADD8E6', fg='black').pack(pady=10)

# Sign in page function
def open_signin_page():
    signin_window = tk.Toplevel(root)
    signin_window.title("Sign In")
    signin_window.geometry("700x500")
    signin_window.configure(bg='#E6E6FA')  # Lavender background
    
    tk.Label(signin_window, text="WELCOME BACK", bg='#E6E6FA', fg='#4B0082', font=('Arial', 18, 'bold')).pack(pady=20)
    
    # Load image using Pillow (ensure the image file is in the same directory or provide the full path)
    img = Image.open("signin_image.png")  # Open the image with PIL
    img = img.resize((100, 100), Image.Resampling.LANCZOS)  # Resize with LANCZOS (formerly ANTIALIAS)
    img = ImageTk.PhotoImage(img)  # Convert to Tkinter-compatible image

    img_label = tk.Label(signin_window, image=img, bg='#E6E6FA')  # Add the image to a label
    img_label.image = img  # Keep a reference to the image
    img_label.pack(pady=10)

    tk.Label(signin_window, text="Username", bg='#E6E6FA', fg='#4B0082', font=('Arial', 12)).pack(pady=5)
    username_entry = tk.Entry(signin_window)
    username_entry.pack(pady=5)
    
    tk.Label(signin_window, text="Password", bg='#E6E6FA', fg='#4B0082', font=('Arial', 12)).pack(pady=5)
    password_entry = tk.Entry(signin_window, show='*')
    password_entry.pack(pady=5)

    tk.Button(signin_window, text="Sign In", command=lambda: signin(username_entry.get(), password_entry.get()), bg='#9370DB', fg='white').pack(pady=10)
    tk.Button(signin_window, text="Sign Up", command=open_signup_page, bg='#9370DB', fg='white').pack(pady=10)
    
    signin_window.mainloop()   # Ensures the image doesn't get garbage collected    
tree=None
# Flight search page function
# Flight search page function with filtering and sorting
def open_flight_search_page():
    global tree  # Make tree global to access it in search_flights
    flight_search_window = tk.Toplevel(root)
    flight_search_window.title("Search Flights")
    flight_search_window.geometry("700x450")
    flight_search_window.configure(bg='#FFFACD')

    tk.Label(flight_search_window, text="Enter Flight Details", bg='#FFFACD', font=('Arial', 14)).pack(pady=10)

    tk.Label(flight_search_window, text="Departure").pack()
    departure_entry = tk.Entry(flight_search_window)
    departure_entry.pack(pady=10)

    tk.Label(flight_search_window, text="Destination").pack()
    destination_entry = tk.Entry(flight_search_window)
    destination_entry.pack(pady=10)

    tk.Label(flight_search_window, text="Date(YYYY-MM-DD)").pack()
    date_entry = tk.Entry(flight_search_window)
    date_entry.pack(pady=10)

    tk.Label(flight_search_window, text="Sort by Price", bg='#FFFACD', fg='#8B4513').pack(pady=5)
    sort_var = tk.StringVar(value="ASC")  # Default sorting order
    tk.Radiobutton(flight_search_window, text="Low to High", variable=sort_var, value="ASC", bg='#FFFACD').pack(pady=2)
    tk.Radiobutton(flight_search_window, text="High to Low", variable=sort_var, value="DESC", bg='#FFFACD').pack(pady=2)

    tk.Button(flight_search_window, text="Search", 
              command=lambda: search_flights(departure_entry.get(), destination_entry.get(), date_entry.get(), sort_var.get()), 
              bg='#DEB887').pack(pady=15)
"""
    # Initialize the Treeview in the flight search window
    global tree  # Make sure the tree variable is accessible
    #tree = ttk.Treeview(flight_search_window, columns=('Flight ID', 'Flight Name', 'Departure', 'Destination', 'Date', 'Start Time', 'Arrival Time', 'Seats Available', 'Price'), show='headings')
    
    # Define the headings and columns
    for col in tree['columns']:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')

    tree.pack(pady=20)  # Pack the Treeview in the window"""

# Function to search flights with filtering and sorting
def search_flights(departure, destination, flight_date, sort_order):
    conn = connect_db()
    cursor = conn.cursor()

    # Clear previous search results if they exist
    if tree is not None:  # Check if tree is initialized
        for item in tree.get_children():
            tree.delete(item)

    # Execute query to retrieve flight details from the database
    query = '''
    SELECT * FROM flights 
    WHERE departure = ? AND destination = ? AND flight_date = ? 
    ORDER BY price {}
    '''.format(sort_order)

    cursor.execute(query, (departure, destination, flight_date))
    flights = cursor.fetchall()
    conn.close()

    # Check if flights exist, and display results if found
    if flights:
        display_flight_results(flights)
    else:
        messagebox.showinfo("No Flights", "No flights found for the given criteria.")
    
# Display flight results
def display_flight_results(flights):
    results_window = tk.Toplevel(root)
    results_window.title("Flight Results")
    results_window.geometry("900x500")
    results_window.configure(bg='#FFFACD')

    # Treeview with added starting_time and arrival_time columns
    tree = ttk.Treeview(results_window, columns=('Flight ID', 'Flight Name', 'Departure', 'Destination', 'Date', 'Start Time', 'Arrival Time', 'Seats Available', 'Price'), show='headings')
    tree.heading('Flight ID', text='Flight ID')
    tree.heading('Flight Name', text='Flight Name')
    tree.heading('Departure', text='Departure')
    tree.heading('Destination', text='Destination')
    tree.heading('Date', text='Date')
    tree.heading('Start Time', text='Start Time')
    tree.heading('Arrival Time', text='Arrival Time')
    tree.heading('Seats Available', text='Seats Available')
    tree.heading('Price', text='Price')

    # Adjust the columns to fit properly within the window
    tree.column('Flight ID', width=80)
    tree.column('Flight Name', width=120)
    tree.column('Departure', width=100)
    tree.column('Destination', width=100)
    tree.column('Date', width=90)
    tree.column('Start Time', width=90)
    tree.column('Arrival Time', width=90)
    tree.column('Seats Available', width=100)
    tree.column('Price', width=80)

    # Insert flights into the Treeview without adding to the database
    if tree is not None:  # Make sure tree is defined before inserting values
        for flight in flights:
            tree.insert('', tk.END, values=(flight[0], flight[1], flight[2], flight[3], flight[4], flight[5], flight[6], flight[7], flight[8]))

    tree.pack()
    tk.Button(results_window, text="Select Flight", command=lambda: select_flight(tree), bg='#DEB887').pack(pady=15)

# Select flight for booking
def select_flight(tree):
    selected_flight = tree.focus()
    flight_values = tree.item(selected_flight, 'values')

    if flight_values:
        open_seat_selection_page(flight_values)

def open_seat_selection_page(flight_values):
    seat_window = tk.Toplevel(root)
    seat_window.title("Seat Selection")
    seat_window.geometry("800x600")
    seat_window.configure(bg='#FAFAD2')

    tk.Label(seat_window, text="Select Your Seat", bg='#FAFAD2', font=('Arial', 14)).pack(pady=10)

    rows, cols = 10, 5
    seat_buttons = {}
    booked_seats = ['1A', '2B']

    def toggle_seat(seat):
        if seat_buttons[seat]['bg'] == 'green':
            seat_buttons[seat].config(bg='blue')
        elif seat_buttons[seat]['bg'] == 'blue':
            seat_buttons[seat].config(bg='green')

    for row in range(rows):
        seat_row_frame = tk.Frame(seat_window)
        seat_row_frame.pack(pady=5)

        for col in range(cols):
            seat = f"{row + 1}{chr(65 + col)}"
            color = 'red' if seat in booked_seats else 'green'
            btn = tk.Button(seat_row_frame, text=seat, width=4, bg=color, command=lambda seat=seat: toggle_seat(seat))
            btn.pack(side=tk.LEFT, padx=5)
            seat_buttons[seat] = btn

    tk.Button(seat_window, text="Confirm Seats", command=lambda: open_passenger_details_page(flight_values, seat_buttons), bg='#FFA07A').pack(pady=15)

def open_passenger_details_page(flight_values, seat_buttons):
    selected_seats = [seat for seat, btn in seat_buttons.items() if btn['bg'] == 'blue']
    if not selected_seats:
        messagebox.showerror("Error", "No seats selected!")
        return

    details_window = tk.Toplevel(root)
    details_window.title("Passenger Details")
    details_window.geometry("700x500")
    details_window.configure(bg='#FAFAD2')

    tk.Label(details_window, text="Enter Passenger Details", bg='#FAFAD2', font=('Arial', 14)).pack(pady=10)

    tk.Label(details_window, text="Full Name").pack()
    name_entry = tk.Entry(details_window)
    name_entry.pack(pady=5)
    
    tk.Label(details_window, text="Age").pack()
    age_entry = tk.Entry(details_window)
    age_entry.pack(pady=5)
    
    tk.Label(details_window, text="Gender").pack(pady=5)
    gender_var = tk.StringVar()
    tk.Radiobutton(details_window, text="Male", variable=gender_var, value='Male').pack(pady=2)
    tk.Radiobutton(details_window, text="Female", variable=gender_var, value='Female').pack(pady=2)
    tk.Radiobutton(details_window, text="Others", variable=gender_var, value='Others').pack(pady=2)

    tk.Label(details_window, text="Email").pack(pady=5)
    email_entry = tk.Entry(details_window)
    email_entry.pack(pady=5)

    tk.Label(details_window, text="Phone").pack()
    phone_entry = tk.Entry(details_window)
    phone_entry.pack(pady=5)

    tk.Button(details_window, text="Proceed to Payment", command=lambda: open_payment_page(flight_values, name_entry.get(), email_entry.get(), phone_entry.get(), selected_seats), bg='#FFA07A').pack(pady=15)

def open_payment_page(flight_values, name, email, phone, selected_seats):
    if not name or not email or not phone:
        messagebox.showerror("Error", "All fields are required!")
        return

    payment_window = tk.Toplevel(root)
    payment_window.title("Payment")
    payment_window.geometry("700x400")
    payment_window.configure(bg='#FFE4B5')

    tk.Label(payment_window, text="Make Payment", bg='#FFE4B5', font=('Arial', 14)).pack(pady=10)
    
    flight_name = flight_values[1]
    total_price = flight_values[8] * len(selected_seats)

    tk.Label(payment_window, text=f"Passenger Name: {name}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)
    tk.Label(payment_window, text=f"Flight Name: {flight_name}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)
    tk.Label(payment_window, text=f"Email: {email}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)
    tk.Label(payment_window, text=f"Phone: {phone}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)
    tk.Label(payment_window, text=f"Selected Seats: {', '.join(selected_seats)}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)
    tk.Label(payment_window, text=f"Total Price: ${total_price}", bg='#FFE4B5', font=('Arial', 12)).pack(pady=5)

    tk.Button(payment_window, text="Confirm Payment", command=lambda: confirm_booking(flight_values, name, email, phone, selected_seats), bg='#FFA500').pack(pady=20)


def confirm_booking(flight_values, name, email, phone, selected_seats):
    conn = connect_db()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO bookings (flight_id, user_name, seat_number, contact_email, contact_phone, booking_date, payment_status)
                          VALUES (?, ?, ?, ?, ?, DATE('now'), 'Confirmed')''', (flight_values[0], name, ', '.join(selected_seats), email, phone))
        conn.commit()

        # Booking confirmation message
        message_text = f"Booking Confirmed!\nPassenger: {name}\nFlight: {flight_values[1]}\nSeats: {', '.join(selected_seats)}"
        messagebox.showinfo("Success", message_text)
        
        # Send SMS using Twilio
        send_sms_confirmation(phone, message_text)

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Error while saving booking: {e}")
    finally:
        conn.close()

def send_sms_confirmation(phone, message_text):
    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Send SMS
    message = client.messages.create(
        body=message_text,
        from_=twilio_number,
        to=phone  # Phone number should be in international format (e.g., +1234567890)
    )

    print(f"SMS sent with SID: {message.sid}")
# Root window
root = tk.Tk()
root.title("Flight Booking System")
root.geometry("900x500")
root.configure(bg='#E6E6FA')

# Load and set the background image
background_image = Image.open("background.jpg")  # Replace "background.jpg" with your image file
background_image = background_image.resize((1000, 600), Image.Resampling.LANCZOS)  # Resize to fit window
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)  # Place label to cover the entire window

# Global font settings for consistency
FONT_LARGE = ('Arial', 14)
FONT_MEDIUM = ('Arial', 12)
FONT_SMALL = ('Arial', 10)

# Set default fonts for Label, Button, and Entry widgets
root.option_add("*Label.Font", FONT_MEDIUM)
root.option_add("*Button.Font", FONT_MEDIUM)
root.option_add("*Entry.Font", FONT_SMALL)

tk.Label(root, text="Welcome to Flight Booking System", bg='#E6E6FA', font=('Arial', 18)).pack(pady=20)
tk.Button(root, text="Sign In", command=open_signin_page, bg='#87CEEB', fg='black').pack(pady=15)
tk.Button(root, text="Sign Up", command=open_signup_page, bg='#FFB6C1', fg='black').pack(pady=15)
setup_database()
root.mainloop()


