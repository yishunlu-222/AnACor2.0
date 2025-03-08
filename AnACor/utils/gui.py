import tkinter as tk
from tkinter import filedialog, ttk
import os
import re


def find_reflexp(root_directory):
    refl_list=[]
    exp_list=[]
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if filename.endswith(".refl") and "scaled" not in filename:
                # Build the full file path
                
                refl_list.append(full_path)
            if filename.endswith(".expt") and "scaled" not in filename:
                exp_list.append(full_path)
    return refl_list,exp_list
import tkinter as tk
from tkinter import filedialog, ttk
import os
import tkinterdnd2

def select_multiple_folders():
    root = tkinterdnd2.TkinterDnD.Tk()  # Enable Drag and Drop
    root.title("Select Multiple Folders")

    folder_paths = []  # List to store selected folder paths
    current_directory = tk.StringVar()  # Store the currently opened directory

    # Function to open a directory and list folders without entering them
    def browse_directory():
        directory = filedialog.askdirectory(title="Select Parent Folder")
        if directory:
            current_directory.set(directory)  # Store selected parent directory
            list_folders(directory)  # Update listbox with available folders

    # Function to list only folders in the selected directory
    def list_folders(directory):
        listbox.delete(0, tk.END)  # Clear previous entries
        try:
            folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
            for folder in folders:
                listbox.insert(tk.END, folder)  # Display folders
        except Exception as e:
            print(f"Error accessing directory: {e}")

    # Function to add selected folders to the selected list
    def add_selected_folders():
        selected_indices = listbox.curselection()  # Get selected items
        if current_directory.get():
            for index in selected_indices:
                folder_name = listbox.get(index)
                folder_path = os.path.join(current_directory.get(), folder_name)
                if folder_path not in folder_paths:  # Avoid duplicates
                    folder_paths.append(folder_path)
        update_selected_listbox()

    # Function to update the selected folders listbox
    def update_selected_listbox():
        selected_listbox.delete(0, tk.END)  # Clear the listbox
        for path in folder_paths:
            selected_listbox.insert(tk.END, path)
        label_selected.config(text=f"Selected folders: {len(folder_paths)}")

    # Function to delete selected folder paths
    def delete_selected():
        selected_indices = selected_listbox.curselection()  # Get selected indices
        for index in reversed(selected_indices):  # Remove in reverse order
            del folder_paths[index]
        update_selected_listbox()

    # Function to select all items in the listbox
    def select_all():
        listbox.select_set(0, tk.END)  # Select all items

    # Function to return the selected paths when the user clicks "Finish"
    def on_finish():
        root.destroy()  # Close the GUI window

    # Drag-and-Drop event handler (for selected folders)
    def on_drop(event):
        dropped_paths = root.tk.splitlist(event.data)  # Handle multiple folders
        for path in dropped_paths:
            if os.path.isdir(path) and path not in folder_paths:  # Ensure only directories
                folder_paths.append(path)
        update_selected_listbox()

    # Create a frame for the UI
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Button to open parent directory
    browse_button = ttk.Button(frame, text="Browse Parent Folder", command=browse_directory)
    browse_button.grid(row=0, column=0, columnspan=3, pady=5, sticky=tk.W)

    # Label and Listbox for available folders
    label_available = ttk.Label(frame, text="Available folders:")
    label_available.grid(row=1, column=0, columnspan=3, sticky=tk.W)

    listbox = tk.Listbox(frame, height=10, width=50, selectmode=tk.MULTIPLE)  # Enable multiple selection
    listbox.grid(row=2, column=0, columnspan=3, pady=5)

    # Button to add selected folders
    add_button = ttk.Button(frame, text="Add Selected", command=add_selected_folders)
    add_button.grid(row=3, column=0, pady=5, sticky=tk.W)

    # Label and Listbox for selected folders
    label_selected = ttk.Label(frame, text="Selected folders: 0")
    label_selected.grid(row=4, column=0, columnspan=3, sticky=tk.W)

    selected_listbox = tk.Listbox(frame, height=10, width=50, selectmode=tk.MULTIPLE)
    selected_listbox.grid(row=5, column=0, columnspan=3, pady=5)

    # Button to delete selected folder paths
    delete_button = ttk.Button(frame, text="Delete Selected", command=delete_selected)
    delete_button.grid(row=6, column=0, pady=5, sticky=tk.W)

    # Button to finish and return paths
    finish_button = ttk.Button(frame, text="Finish", command=on_finish)
    finish_button.grid(row=6, column=2, pady=5, sticky=tk.E)

    # Register the selected_listbox as a drop target for drag-and-drop
    selected_listbox.drop_target_register(tkinterdnd2.DND_FILES)
    selected_listbox.dnd_bind('<<Drop>>', on_drop)

    # Start the Tkinter event loop
    root.mainloop()

    # Return the folder paths after the GUI is closed
    return folder_paths

# Ensure tkinterdnd2 is installed before running
if __name__ == "__main__":
    selected_folders = select_multiple_folders()
    print("Selected Folders:", selected_folders)
