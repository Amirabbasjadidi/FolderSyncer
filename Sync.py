import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import schedule
import time
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont

appdata_dir = os.path.join(os.getenv('APPDATA'), 'SyncApp')
if not os.path.exists(appdata_dir):
    os.makedirs(appdata_dir)

settings_file = os.path.join(appdata_dir, 'settings.json')
font_file = 'Ubuntu-Regular.ttf'

class SyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sync Folders")
        self.rows = []
        self.notifications = []
        self.global_notifications_enabled = True

        self.sync_status_window = None
        self.sync_progress_vars = {}
        self.sync_progress_labels = {}
        self.sync_threads = {}
        self.row_counter = 0

        self.load_settings()
        self.create_ui()
        self.create_tray_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.schedule_thread = Thread(target=self.run_scheduler)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()

    def create_ui(self):
        self.frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure('TButton', font=('Ubuntu', 10))
        style.configure('TLabel', font=('Ubuntu', 10))
        style.configure('TEntry', font=('Ubuntu', 10))

        self.add_row_button = ttk.Button(self.frame, text="Add New Schedule", command=self.add_row)
        self.add_row_button.grid(row=0, column=0, pady=5)

        self.toggle_all_notifications_button = tk.Button(self.frame, text="All Notifications: ON", command=self.toggle_all_notifications, bg="green", fg="white")
        self.toggle_all_notifications_button.grid(row=0, column=1, pady=5)

        self.sync_status_button = ttk.Button(self.frame, text="Sync Status", command=self.show_sync_status)
        self.sync_status_button.grid(row=0, column=2, pady=5)

        self.load_existing_rows()

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        d = ImageDraw.Draw(image)
        d.rectangle((0, 0, 64, 64), fill=(255, 0, 0))
        menu = (item('Open', self.show_window), item('Exit', self.exit_app))
        self.tray_icon = pystray.Icon("sync_app", image, "Sync App", menu)
        self.tray_icon.run_detached()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.show_notifications()

    def show_notifications(self):
        for notification in self.notifications:
            messagebox.showinfo("Success", notification)
        self.notifications.clear()

    def exit_app(self, icon, item):
        self.tray_icon.stop()
        self.root.quit()

    def add_row(self, folder1='', folder2='', time_str='', notifications_enabled=True):
        row_id = self.row_counter
        self.row_counter += 1

        row = {}
        row['id'] = row_id
        row['folder1'] = ttk.Entry(self.frame, width=30)
        row['folder1'].insert(0, folder1)
        row['folder1'].grid(row=len(self.rows)+1, column=0, padx=5)

        row['select_folder1'] = ttk.Button(self.frame, text="Browse", command=lambda r=row: self.select_folder(r, 'folder1'))
        row['select_folder1'].grid(row=len(self.rows)+1, column=1, padx=5)

        row['folder2'] = ttk.Entry(self.frame, width=30)
        row['folder2'].insert(0, folder2)
        row['folder2'].grid(row=len(self.rows)+1, column=2, padx=5)

        row['select_folder2'] = ttk.Button(self.frame, text="Browse", command=lambda r=row: self.select_folder(r, 'folder2'))
        row['select_folder2'].grid(row=len(self.rows)+1, column=3, padx=5)

        row['time'] = ttk.Entry(self.frame, width=10)
        row['time'].insert(0, time_str)
        row['time'].grid(row=len(self.rows)+1, column=4, padx=5)

        row['select_time'] = ttk.Button(self.frame, text="Set Time", command=lambda r=row: self.select_time(r))
        row['select_time'].grid(row=len(self.rows)+1, column=5, padx=5)

        row['manual_sync'] = ttk.Button(self.frame, text="Sync Now", command=lambda r=row: self.start_sync_thread(r, manual=True))
        row['manual_sync'].grid(row=len(self.rows)+1, column=6, padx=5)

        row['delete'] = ttk.Button(self.frame, text="Delete", command=lambda r=row: self.delete_row(r))
        row['delete'].grid(row=len(self.rows)+1, column=7, padx=5)

        row['notifications_enabled'] = notifications_enabled
        row['toggle_notifications'] = tk.Button(self.frame, text="Notifications: ON" if notifications_enabled else "Notifications: OFF", command=lambda r=row: self.toggle_notifications(r))
        row['toggle_notifications'].grid(row=len(self.rows)+1, column=8, padx=5)
        self.update_toggle_notifications_button(row)

        self.rows.append(row)
        self.schedule_sync()

    def load_existing_rows(self):
        for row in self.rows:
            for widget in row.values():
                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Button) or isinstance(widget, tk.Button):
                    widget.destroy()
        self.rows = []

        for setting in self.settings:
            self.add_row(setting['folder1'], setting['folder2'], setting['time'], setting.get('notifications_enabled', True))

    def delete_row(self, row):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this schedule?")
        if confirm:
            for widget in row.values():
                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Button) or isinstance(widget, tk.Button):
                    widget.destroy()
            self.rows.remove(row)
            self.save_settings()
            self.load_existing_rows()
            self.schedule_sync()

    def select_folder(self, row, folder_key):
        try:
            folder = filedialog.askdirectory()
            if folder:
                row[folder_key].delete(0, tk.END)
                row[folder_key].insert(0, folder)
        except Exception as e:
            messagebox.showerror("Folder Selection Error", f"Error selecting folder:\n{e}")

    def select_time(self, row):
        def stop_sync():
            row['time'].delete(0, tk.END)
            self.schedule_sync()

        dialog = tk.Toplevel(self.root)
        dialog.title("Select Time")

        ttk.Label(dialog, text="Enter time (HH:MM 24-hour format):").grid(row=0, column=0, padx=10, pady=10)
        time_entry = ttk.Entry(dialog, width=10)
        time_entry.grid(row=0, column=1, padx=10, pady=10)

        set_time_button = ttk.Button(dialog, text="Set Time", command=lambda: set_time(time_entry.get()))
        set_time_button.grid(row=1, column=0, padx=10, pady=10)

        stop_time_button = ttk.Button(dialog, text="Stop Auto Sync", command=stop_sync)
        stop_time_button.grid(row=1, column=1, padx=10, pady=10)

        def set_time(time_str):
            if time_str:
                try:
                    valid_time = time.strptime(time_str, "%H:%M")
                    row['time'].delete(0, tk.END)
                    row['time'].insert(0, time_str)
                    self.schedule_sync()
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format")

    def calculate_folder_size(self, folder):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def sync_folders(self, row, manual=False):
        folder1 = row['folder1'].get()
        folder2 = row['folder2'].get()

        if not os.path.exists(folder1):
            messagebox.showerror("Error", f"Source folder does not exist: {folder1}")
            return
        if not os.path.exists(folder2):
            os.makedirs(folder2)

        total_size = self.calculate_folder_size(folder1)
        copied_size = 0

        start_message = f"Sync started: {folder1} to {folder2}"
        if manual or (self.root.state() != 'withdrawn' and row['notifications_enabled'] and self.global_notifications_enabled):
            messagebox.showinfo("Info", start_message)
        elif row['notifications_enabled'] and self.global_notifications_enabled:
            self.notifications.append(start_message)

        def copy_file(s, d):
            nonlocal copied_size
            shutil.copy2(s, d)
            copied_size += os.path.getsize(s)
            progress = int((copied_size / total_size) * 100)
            
            row_id = row['id']
            if row_id in self.sync_progress_vars:
                self.sync_progress_vars[row_id].set(progress)
                self.sync_progress_labels[row_id].config(text=f"{progress}%")

        with ThreadPoolExecutor() as executor:
            futures = []
            for dirpath, dirnames, filenames in os.walk(folder1):
                for f in filenames:
                    s = os.path.join(dirpath, f)
                    d = os.path.join(folder2, os.path.relpath(s, folder1))
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    futures.append(executor.submit(copy_file, s, d))

            for future in futures:
                future.result()  # Wait for all threads to complete

        # Ensure progress reaches 100% at the end
        if total_size > 0:
            self.sync_progress_vars[row['id']].set(100)
            self.sync_progress_labels[row['id']].config(text="100%")

        end_message = f"Sync completed: {folder1} to {folder2} at {time.strftime('%H:%M')}"
        if manual or (self.root.state() != 'withdrawn' and row['notifications_enabled'] and self.global_notifications_enabled):
            messagebox.showinfo("Success", end_message)
        elif row['notifications_enabled'] and self.global_notifications_enabled:
            self.notifications.append(end_message)

    def start_sync_thread(self, row, manual=False):
        row_id = row['id']
        if row_id in self.sync_threads and self.sync_threads[row_id].is_alive():
            messagebox.showinfo("Info", "Sync is already in progress for this row.")
            return

        thread = Thread(target=self.sync_folders, args=(row, manual))
        self.sync_threads[row_id] = thread
        thread.start()

    def schedule_sync(self):
        schedule.clear()
        for row in self.rows:
            time_str = row['time'].get()
            if time_str:
                try:
                    schedule.every().day.at(time_str).do(self.start_sync_thread, row)
                except schedule.ScheduleValueError:
                    messagebox.showerror("Invalid Time", f"Invalid time format: {time_str}")

    def run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def toggle_notifications(self, row):
        row['notifications_enabled'] = not row['notifications_enabled']
        self.update_toggle_notifications_button(row)
        self.save_settings()

    def toggle_all_notifications(self):
        self.global_notifications_enabled = not self.global_notifications_enabled
        for row in self.rows:
            row['notifications_enabled'] = self.global_notifications_enabled
            self.update_toggle_notifications_button(row)
        self.update_toggle_all_notifications_button()
        self.save_settings()

    def update_toggle_notifications_button(self, row):
        if row['notifications_enabled']:
            row['toggle_notifications'].config(text="Notifications: ON", bg="green", fg="white")
        else:
            row['toggle_notifications'].config(text="Notifications: OFF", bg="red", fg="white")

    def update_toggle_all_notifications_button(self):
        if self.global_notifications_enabled:
            self.toggle_all_notifications_button.config(text="All Notifications: ON", bg="green", fg="white")
        else:
            self.toggle_all_notifications_button.config(text="All Notifications: OFF", bg="red", fg="white")

    def save_settings(self):
        self.settings = []
        for row in self.rows:
            setting = {
                'folder1': row['folder1'].get(),
                'folder2': row['folder2'].get(),
                'time': row['time'].get(),
                'notifications_enabled': row['notifications_enabled']
            }
            self.settings.append(setting)
        with open(settings_file, 'w') as f:
            json.dump(self.settings, f)

    def load_settings(self):
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = []

    def show_sync_status(self):
        if self.sync_status_window is None or not self.sync_status_window.winfo_exists():
            self.sync_status_window = tk.Toplevel(self.root)
            self.sync_status_window.title("Sync Status")
            self.sync_status_window.geometry("400x300")

            for i, (row, thread) in enumerate(self.sync_threads.items()):
                label = ttk.Label(self.sync_status_window, text=f"Sync {i + 1}")
                label.grid(row=i, column=0, padx=10, pady=10)
                
                progress_var = tk.DoubleVar(value=0)
                self.sync_progress_vars[row] = progress_var
                
                progress_bar = ttk.Progressbar(self.sync_status_window, orient="horizontal", length=200, mode="determinate", variable=progress_var)
                progress_bar.grid(row=i, column=1, padx=10, pady=10)
                
                percent_label = ttk.Label(self.sync_status_window, text="0%")
                percent_label.grid(row=i, column=2, padx=10, pady=10)
                
                self.sync_progress_labels[row] = percent_label
            
            self.update_sync_status()

    def update_sync_status(self):
        for row, progress_var in self.sync_progress_vars.items():
            # This part is now updated in sync_folders
            pass
        
        if self.sync_status_window is not None and self.sync_status_window.winfo_exists():
            self.sync_status_window.after(1000, self.update_sync_status)

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncApp(root)
    root.mainloop()
