import tkinter as tk
from tkinter import filedialog, ttk

def select_multiple_folders():
    # Initialize the main window
    root = tk.Tk()
    root.title("Select Multiple Folders")
    folder_paths = []  # List to store selected folder paths

    # Function to open a dialog and add a folder path
    def add_folder():
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            folder_paths.append(folder_path)
            update_listbox()

    # Function to update the listbox and label
    def update_listbox():
        listbox.delete(0, tk.END)  # Clear the listbox
        for path in folder_paths:
            listbox.insert(tk.END, path)
        label.config(text=f"Selected folders: {len(folder_paths)}")

    # Function to return the selected paths when the user clicks "Finish"
    def on_finish():
        root.destroy()  # Close the GUI window

    # Create a frame for the UI
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Label to show the number of selected folders
    label = ttk.Label(frame, text="Selected folders: 0")
    label.grid(row=0, column=0, columnspan=2, sticky=tk.W)

    # Listbox to display the selected folder paths
    listbox = tk.Listbox(frame, height=10, width=50)
    listbox.grid(row=1, column=0, columnspan=2, pady=5)

    # Button to add a new folder
    add_button = ttk.Button(frame, text="Add Folder", command=add_folder)
    add_button.grid(row=2, column=0, pady=5, sticky=tk.W)

    # Button to finish and return paths
    finish_button = ttk.Button(frame, text="Finish", command=on_finish)
    finish_button.grid(row=2, column=1, pady=5, sticky=tk.E)

    # Start the Tkinter event loop
    root.mainloop()

    # Return the folder paths after the GUI is closed
    return folder_paths

if __name__ == "__main__":
    selected_folders = select_multiple_folders()
    print("Selected folder paths:")
    for path in selected_folders:
        print(path)
