import pytesseract
from PIL import Image
import pyautogui
import io
import asyncio
import logging
import sys
import configparser
import threading
import sv_ttk
import tkinter as tk
from tkinter import ttk, messagebox
from buttplug import Client, WebsocketConnector, ProtocolSpec

class App:

    root = None  # Define root as a class variable
    def __init__(self, master=None):
        if App.root is None:  # Check if root has been initialized
            App.root = tk.Tk()  # Initialize root if it's None
        else:
            self.root = master  # Use the existing root if it's already initialized
        
        self.root.title("World of Buttcraft")
        sv_ttk.set_theme("dark")

        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read('config.ini')
        self.create_widgets()

    def create_widgets(self):
        self.help_button = ttk.Button(self.root, text="Help", command=self.open_help_window)
        self.help_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        tk.Label(self.root, text="Region:", anchor="w").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.region_entry = tk.Entry(self.root)
        self.region_entry.grid(row=1, column=1, padx=5, pady=5)
        self.region_entry.insert(0, strip_comments(self.config['Settings']['region']))

        tk.Label(self.root, text="Top Value:", anchor="w").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.top_value_entry = tk.Entry(self.root)
        self.top_value_entry.grid(row=2, column=1, padx=5, pady=5)
        self.top_value_entry.insert(0, strip_comments(self.config['Settings']['top_value']))

        tk.Label(self.root, text="Bottom Value:", anchor="w").grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        self.bottom_value_entry = tk.Entry(self.root)
        self.bottom_value_entry.grid(row=3, column=1, padx=5, pady=5)
        self.bottom_value_entry.insert(0, strip_comments(self.config['Settings']['bottom_value']))

        tk.Label(self.root, text="Scale:", anchor="w").grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.scale_entry = tk.Entry(self.root)
        self.scale_entry.grid(row=4, column=1, padx=5, pady=5)
        self.scale_entry.insert(0, strip_comments(self.config['Settings']['scale']))

        tk.Label(self.root, text="Rotation Scale:", anchor="w").grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        self.rotationscale_entry = tk.Entry(self.root)
        self.rotationscale_entry.grid(row=5, column=1, padx=5, pady=5)
        self.rotationscale_entry.insert(0, strip_comments(self.config['Settings']['rotationscale']))

        tk.Label(self.root, text="Vibe on death:", anchor="w").grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        self.vibe_on_death_var = tk.BooleanVar()
        self.vibe_on_death_check = tk.Checkbutton(self.root, variable=self.vibe_on_death_var)
        self.vibe_on_death_check.grid(row=6, column=1, padx=5, pady=5)
        self.vibe_on_death_var.set(strip_comments(self.config['Settings']['vibe_on_death']).lower() == 'true')

        tk.Label(self.root, text="Vibe on boss kill:", anchor="w").grid(row=7, column=0, padx=5, pady=5, sticky="ew")
        self.vibe_on_win_var = tk.BooleanVar()
        self.vibe_on_win_check = tk.Checkbutton(self.root, variable=self.vibe_on_win_var)
        self.vibe_on_win_check.grid(row=7, column=1, padx=5, pady=5)
        self.vibe_on_win_var.set(strip_comments(self.config['Settings']['vibe_on_win']).lower() == 'true')

        self.apply_button = ttk.Button(self.root, text="Apply", command=self.update_config, width= 15)
        self.apply_button.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.start_button = ttk.Button(self.root, text="Start", command=self.start_process, width=10)
        self.start_button.grid(row=9, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop_process, width=10)
        self.stop_button.grid(row=9, column=1, padx=5, pady=5, sticky="e")

        tk.Label(self.root, text="Status:", anchor="w").grid(row=10, column=0, padx=5, pady=5, sticky="ew")
        self.status_label = tk.Label(self.root, text="Idle")
        self.status_label.grid(row=10, column=1, padx=5, pady=5)

        self.extracted_text_label = tk.Label(self.root, text="")
        self.extracted_text_label.grid(row=11, column=0, columnspan=2, padx=0, pady=0)

        self.process_running = False
        self.update_config()

    def open_help_window(self):
        # Create a new window for help
        help_window = tk.Toplevel(self.root)
        help_window.title("Instructions")

        # Create a Text widget for instructions
        instructions_text = tk.Text(help_window, wrap="word", height=20, width=80)
        instructions_text.pack(padx=10, pady=10)

        # Insert instructions text
        instructions = (
            "Region:\n"
            "Screen coordinates (in px) of the weak aura (left, top, width, height)\n"
            "I recommend using this app: https://github.com/jabbalaci/ShowMousePosition\n"
            "Measure the left border of the black background (first value)\n"
            "Measure the top of the black background (second value) \nWidth and height should be consistent\n"

            "\nHealing can be toggled in the weak aura custom options\n"

            "\nTop Value:\n"
            "At this dps the toy will vibrate at 100% (Modifier K or M)\n"

            "\nBottom Value:\n"
            "At this dps the toy will vibrate at 0% (Modifier K or M)\n"

            "\nScale:\n"
            "Global scale of the vibrations 0.1 - 1; 0 to disable\n"
        )
        instructions_text.insert(tk.END, instructions)
        instructions_text.config(state=tk.DISABLED)  # Make the text read-only

        # Close button
        close_button = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_button.pack(padx=10, pady=10)

    def start_process(self):
        if self.process_running:
            messagebox.showinfo("Information", "Process is already running")
            return

        self.process_running = True
        self.status_label.config(text="Running")
        threading.Thread(target=self.run_asyncio).start()
        self.update_config()  

    def stop_process(self):
        self.process_running = False
        self.status_label.config(text="Stopped")
        self.update_config()  

    def update_config(self):
        # Read the original configuration file and preserve the comments
        with open('config.ini', 'r') as file:
            lines = file.readlines()

        # Update config values from GUI entries
        self.config['Settings']['region'] = self.region_entry.get()
        self.config['Settings']['top_value'] = self.top_value_entry.get()
        self.config['Settings']['bottom_value'] = self.bottom_value_entry.get()
        self.config['Settings']['scale'] = self.scale_entry.get()
        self.config['Settings']['rotationscale'] = self.rotationscale_entry.get()
        self.config['Settings']['vibe_on_death'] = str(self.vibe_on_death_var.get())
        self.config['Settings']['vibe_on_win'] = str(self.vibe_on_win_var.get())

        # Write back to the configuration file preserving the comments
        with open('config.ini', 'w') as file:
            for line in lines:
                # If the line starts with a section header, write it directly
                if line.startswith('['):
                    file.write(line)
                    continue
                
                # Otherwise, check if the line corresponds to an option in the Settings section
                for option in self.config['Settings']:
                    if line.startswith(option):
                        # Write the option and its value
                        file.write(f'{option} = {self.config["Settings"][option]}\n')
                        break
                else:
                    # If the line doesn't correspond to any option in the Settings section, write it as is
                    file.write(line)
        
    def run_asyncio(self):
        asyncio.run(self.main())

    async def main(self):
        client = Client("World of Buttcraft", ProtocolSpec.v3)
        connector = WebsocketConnector("ws://127.0.0.1:12345", logger=client.logger)
        
        try:
            await client.connect(connector)
        except Exception as e:
            logging.error(f"Could not connect to server, exiting: {e}")
            self.process_running = False
            self.status_label.config(text="Error")
            return
        
        await client.start_scanning()
        await asyncio.sleep(5)
        await client.stop_scanning()
        self.status_label.config(text="Devices Connected")

        region_str = self.region_entry.get()
        region = tuple(map(int, region_str.split(',')))

        top_value = self.top_value_entry.get()
        bottom_value = self.bottom_value_entry.get()
        scale = float(self.scale_entry.get())
        rotationscale = float(self.rotationscale_entry.get())
        vibe_on_death = self.vibe_on_death_var.get()
        vibe_on_win = self.vibe_on_win_var.get()

        percentage = 0

        while self.process_running:
            screenshot = pyautogui.screenshot(region=region)
            screenshot_bytes = io.BytesIO()
            screenshot.save(screenshot_bytes, format='PNG')
            screenshot_bytes.seek(0)
            screenshot_image = Image.open(screenshot_bytes)
            extracted_text = pytesseract.image_to_string(screenshot_image).strip()

            self.extracted_text_label.config(text=extracted_text)

            if extracted_text == "DEAD" and vibe_on_death:
                for _ in range(10):
                    for device_id, device in client.devices.items():
                        if device.actuators and len(device.actuators) > 0:
                            await device.actuators[0].command(scale * 1)
                        if device.rotatory_actuators and len(device.rotatory_actuators) > 0:
                            await device.rotatory_actuators[0].command(rotationscale * 1)
                    await asyncio.sleep(0.8)

                    for device_id, device in client.devices.items():
                        if device.actuators and len(device.actuators) > 0:
                            await device.actuators[0].command(0)
                        if device.rotatory_actuators and len(device.rotatory_actuators) > 0:
                            await device.rotatory_actuators[0].command(0)
                    await asyncio.sleep(0.2)
                percentage = 0

            elif extracted_text == "WIN" and vibe_on_win:
                for _ in range(10):
                    for device_id, device in client.devices.items():
                        if device.actuators and len(device.actuators) > 0:
                            await device.actuators[0].command(scale * 1)
                        if device.rotatory_actuators and len(device.rotatory_actuators) > 0:
                            await device.rotatory_actuators[0].command(rotationscale * 1)
                    await asyncio.sleep(0.8)

                    for device_id, device in client.devices.items():
                        if device.actuators and len(device.actuators) > 0:
                            await device.actuators[0].command(scale * 0.8)
                        if device.rotatory_actuators and len(device.rotatory_actuators) > 0:
                            await device.rotatory_actuators[0].command(rotationscale * 0.8)
                    await asyncio.sleep(0.2)

            elif extracted_text and is_valid_text(extracted_text):
                given_value_str = extracted_text
                given_value = parse_value(given_value_str)
                top_value_parsed = parse_value(top_value)
                bottom_value_parsed = parse_value(bottom_value)
                percentage = round(((given_value - bottom_value_parsed) / (top_value_parsed - bottom_value_parsed)) * 100)
                percentage = max(min(percentage, 100), 0)
                self.extracted_text_label.config(text=f"Current value: {extracted_text} - Percentage: {round(percentage * scale)}")
            else:
                percentage = max(min(round(percentage, 0) - 5, 100), 0)
                if percentage <= 4.9:
                    percentage = 0
                self.extracted_text_label.config(text=f"Invalid or no combat - Percentage: {round(percentage * scale)}")

            for device_id, device in client.devices.items():
                if device.actuators and len(device.actuators) > 0:
                    await device.actuators[0].command(float(scale * percentage / 100.0))
                if device.rotatory_actuators and len(device.rotatory_actuators) > 0:
                    await device.rotatory_actuators[0].command(rotationscale * percentage / 100.0, True)

            await asyncio.sleep(0.5)

        await client.disconnect()
        self.status_label.config(text="Stopped")


def strip_comments(value):
    return value.split(';', 1)[0].strip()

def is_valid_text(text):
    valid_chars = set("0123456789.MkK")
    return all(char in valid_chars for char in text)

def parse_value(value_str):
    value_str = value_str.strip()
    suffix = value_str[-1].upper()
    if suffix == 'K':
        value = float(value_str[:-1]) * 1e3
    elif suffix == 'M':
        value = float(value_str[:-1]) * 1e6
    else:
        value = float(value_str)
    return int(value)

if __name__ == "__main__":
    tesseract_cmd = "Tesseract-OCR\\tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    root = None  
    app = App(root)
    root = app.root  
    root.mainloop()


