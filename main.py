import tkinter as tk
from tkinter import messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import random
import time

# The file where the data will be stored
DATA_FILE = 'secret_santa_data.json'

# Gmail account details
# User = 'somedude'
# PW = 'somepass'

# Load existing data from the file
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'adults': [], 'children': []}

# Save current data to the file
def save_data(adults, children, pairings=None):
    data = {
        'adults': adults,
        'children': children,
        'pairings': pairings if pairings is not None else []
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# A simple function to add an entry to a list and listbox
def add_entry(name, email, listbox, entries_list, is_child=False):
    if name.strip() and (is_child or email.strip()):
        entry = f"{name} <{email}>" if not is_child else name.strip()
        entries_list.append((name.strip(), email.strip() if not is_child else ''))
        listbox.insert(tk.END, entry)
        name_entry.delete(0, tk.END)
        if not is_child:
            email_entry.delete(0, tk.END)
    else:
        messagebox.showerror("Error", "Name cannot be empty." if is_child else "Name and email cannot be empty.")
    save_data(adults, children)

# Function to remove an entry from a list and listbox
def remove_entry():
    # Check which Listbox has an active selection
    if adults_listbox.curselection():
        listbox = adults_listbox
        entries_list = adults
    elif children_listbox.curselection():
        listbox = children_listbox
        entries_list = children
    else:
        messagebox.showerror("Error", "No item is selected to remove.")
        return
    
    try:
        # Get the index of the selected line
        index = listbox.curselection()[0]
        # Remove the entry from the listbox
        listbox.delete(index)
        # Remove the entry from the data list
        del entries_list[index]
        # Update the saved data
        save_data(adults, children)
    except IndexError:
        messagebox.showerror("Error", "No item is selected to remove.")

def shuffle_and_save_pairings():
    # Shuffle the lists
    random.shuffle(adults)
    random.shuffle(children)
    
    # Pair adults
    adult_pairings = list(zip(adults, adults[1:] + [adults[0]]))
    
    # Create a list of adults that will be paired with children
    # Ensure it's the same length as the children list
    selected_adults = random.sample(adults, k=len(children))
    
    # Assign children to the selected adults
    child_pairings = list(zip(selected_adults, children))
    
    # Combine both pairings
    combined_pairings = {
        'adults': adult_pairings,
        'children': child_pairings
    }
    
    # Save to the JSON file
    save_data(adults, children, combined_pairings)
    
    # Update the UI or notify the user
    messagebox.showinfo("Shuffle", "The adults and children have been shuffled and saved.")

def get_selected_adult_details():
    # Load the data from the file
    data = load_data()
    pairings = data.get('pairings', {})
    adult_pairings = pairings.get('adults', [])
    child_pairings = pairings.get('children', [])

    # Check which adult is currently selected in the adults listbox
    selected_index = adults_listbox.curselection()
    if not selected_index:
        messagebox.showerror("Error", "No adult is selected.")
        return None

    # Retrieve the selected adult's information
    selected_adult = adults[selected_index[0]]
    adult_name, adult_email = selected_adult

    # Find the adult's pairings
    adult_assignment = None
    child_assignment = None
    for adult_pair in adult_pairings:
        if adult_pair[0][0] == adult_name:  # Compare the names
            adult_assignment = adult_pair[1][0]  # Get the name of the adult assignment
            break

    for child_pair in child_pairings:
        if child_pair[0][0] == adult_name:  # Compare the names
            child_assignment = child_pair[1][0]  # Get the name of the child assignment
            break

    # Return the details
    return {
        "name": adult_name,
        "email": adult_email,
        "adult_assignment": adult_assignment,
        "child_assignment": child_assignment
    }

def email_direct_wrapper():
    # Retrieve the details of the selected adult and their assignments
    selected_adult_details = get_selected_adult_details()
    # Now call send_email_direct with the details
    send_email_direct(
        adult_name=selected_adult_details["name"],
        adult_email=selected_adult_details["email"],
        adult_assignment=selected_adult_details["adult_assignment"],
        child_assignment=selected_adult_details["child_assignment"],
        date_of_exchange="December 24th",
        spend_limit="$25"
    )

def send_email_all():
    # Load the data from the file
    data = load_data()
    pairings = data.get('pairings', {})
    adult_pairings = pairings.get('adults', [])
    child_pairings = pairings.get('children', [])

    # Loop through each adult in the adult_pairings list
    for adult_pair in adult_pairings:
        adult_name, adult_email = adult_pair[0]  # Adult's own name and email
        adult_assignment = adult_pair[1][0]      # Adult's assigned person to gift

        # Find if the current adult has a child assigned as well
        child_assignment = None
        for child_pair in child_pairings:
            if child_pair[0][0] == adult_name:
                child_assignment = child_pair[1][0]  # Child's name
                break

        # Send email to the current adult with their assignments
        send_email_direct(
            adult_name=adult_name,
            adult_email=adult_email,
            adult_assignment=adult_assignment,
            child_assignment=child_assignment,
            date_of_exchange="December 24th",
            spend_limit="$25"
        )

        # Delay the next email by 1 second
        time.sleep(1)

    # Notify the user that all emails have been sent
    messagebox.showinfo("Email All", "Emails have been sent to all adults.")

def send_email_direct(adult_name, adult_email, adult_assignment, child_assignment=None, date_of_exchange="December 24th", spend_limit="$25"):
    # Email sender account details
    gmail_user = 'Helper3lf@gmail.com'
    gmail_app_password = 'qmrmarqnkfaiqism'

    # Email content
    subject = '🎄 Black Family Secret Santa Pairing Announcement! 🎅'
    
    # Email body with dynamic content based on the selected adult's name and assignments
    greeting = f"Dear {adult_name.split()[0]},\n\n"
    body_intro = (
        "Ho-Ho-Hello and Season’s Greetings!\n\n"
        "This year, you have the special task of playing Santa to:\n\n\n"
    )
    
    assignments = f"{adult_assignment}"
    if child_assignment:
        assignments += f" and {child_assignment}"
        
    body_outro = (
        f"\n\n\nRemember, the joy is in the giving, not in the value of the gift! We've set a merry spending limit of {spend_limit} for each person to keep things fun and fair.\n\n"
        "📅 Important Dates:\n\n"
        f"Please keep your Secret Santa role under wraps and be sure to have your gifts ready by our family gathering on {date_of_exchange}. "
        "If you are unable to attend or need to send your gift by reindeer post, let us know, and we’ll arrange a sleigh delivery.\n\n"
        "Wishing you all the jingle bells and whistles this holiday season,\n\n"
        "S. Claus\n\n"
        "P.S. Keep an eye on your inbox for any updates or changes to our Secret Santa plans!"
    )

    body = greeting + body_intro + assignments + body_outro
    
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = adult_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Set up the SMTP server and send the email
    try:
        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_app_password)
        smtp_server.send_message(msg)
        smtp_server.close()
        print(f'Email sent to {adult_name}!')
    except Exception as e:
        print(f'An error occurred: {e}')

# Now, modify the initialization section to load existing data
data = load_data()
adults = data['adults']
children = data['children']

# Initialize the main window
root = tk.Tk()
root.title("Secret Santa Organizer")

# Create the UI elements
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, padx=10, pady=10)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

# UI for adding people
name_label = tk.Label(left_frame, text="Name:")
name_label.pack()
name_entry = tk.Entry(left_frame, width=50)
name_entry.pack()

email_label = tk.Label(left_frame, text="Email:")
email_label.pack()
email_entry = tk.Entry(left_frame, width=50)
email_entry.pack()

add_adult_button = tk.Button(left_frame, text="Add Adult",
                             command=lambda: add_entry(name_entry.get(), email_entry.get(), adults_listbox, adults))
add_adult_button.pack(pady=5)

add_child_button = tk.Button(left_frame, text="Add Child",
                             command=lambda: add_entry(name_entry.get(), '', children_listbox, children, is_child=True))
add_child_button.pack(pady=5)

remove_button = tk.Button(left_frame, text="Remove Selected",
                          command=remove_entry)
remove_button.pack(pady=5)

left_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Left bottom frame for the Shuffle button
left_bottom_frame = tk.Frame(left_frame)
left_bottom_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

# Right bottom frame for the Email buttons
right_bottom_frame = tk.Frame(left_frame)
right_bottom_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

# Shuffle button
shuffle_button = tk.Button(left_bottom_frame, text="Shuffle", command=shuffle_and_save_pairings)
shuffle_button.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))

# Calculate the height for the email buttons based on the shuffle button's height
root.update_idletasks()  # Update UI to ensure sizes are calculated correctly
shuffle_button_height = shuffle_button.winfo_height()
email_button_height = shuffle_button_height // 2

# Set up the Email Direct button to use the wrapper function
email_direct_button = tk.Button(right_bottom_frame, text="Email Direct", command=email_direct_wrapper)
email_direct_button.pack(fill=tk.X, pady=(0, 2))

# Email All button
email_all_button = tk.Button(right_bottom_frame, text="Email All", command=send_email_all)
email_all_button.pack(fill=tk.X, pady=(2, 0))

# Set the height of the email buttons to match the height of the shuffle button
email_direct_button.pack_propagate(False)  # Prevent the button from shrinking
email_all_button.pack_propagate(False)  # Prevent the button from shrinking
email_direct_button.config(height=email_button_height)
email_all_button.config(height=email_button_height)

# UI for showing added adults and children
adults_listbox_label = tk.Label(right_frame, text="Adults:")
adults_listbox_label.pack()
adults_listbox = tk.Listbox(right_frame, width=50)
adults_listbox.pack()

children_listbox_label = tk.Label(right_frame, text="Children:")
children_listbox_label.pack()
children_listbox = tk.Listbox(right_frame, width=50)
children_listbox.pack()

# When populating the Listboxes, do the following after their creation:
for adult in adults:
    adults_listbox.insert(tk.END, f"{adult[0]} <{adult[1]}>")

for child in children:
    children_listbox.insert(tk.END, f"{child[0]} <{child[1]}>")


# This is where you would add more UI elements for handling the Secret Santa logic and sending emails

# Start the Tkinter event loop
root.mainloop()
