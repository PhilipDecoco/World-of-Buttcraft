import pytesseract
from PIL import Image
import pyautogui
import io
import asyncio
import logging
import sys
import configparser
from buttplug import Client, WebsocketConnector, ProtocolSpec

#function to strip comments from a config value
def strip_comments(value):
    return value.split(';', 1)[0].strip()

config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')

# Access and process configuration settings
region_str = strip_comments(config['Settings']['region'])
region = tuple(map(int, region_str.split(',')))

top_value = strip_comments(config['Settings']['top_value'])
bottom_value = strip_comments(config['Settings']['bottom_value'])
scale = float(strip_comments(config['Settings']['scale']))
rotationscale =float(strip_comments(config['Settings']['rotationscale'])) 

tesseract_cmd = "Tesseract-OCR\\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

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

async def main():
    client = Client("World of Buttcraft", ProtocolSpec.v3)
    connector = WebsocketConnector("ws://127.0.0.1:12345", logger=client.logger)
    
    try:
        await client.connect(connector)
    except Exception as e:
        logging.error(f"Could not connect to server, exiting: {e}")
        return
    
    # Connect buttplugio devices
    await client.start_scanning()
    print("Scanning Devices...")
    await asyncio.sleep(10)
    await client.stop_scanning()
    client.logger.info(f"Devices: {client.devices}")
    print("Current scale:", scale)

    percentage = 0

    while True:
        try:
            screenshot = pyautogui.screenshot(region=region)
            screenshot_bytes = io.BytesIO()
            screenshot.save(screenshot_bytes, format='PNG')
            screenshot_bytes.seek(0)
            screenshot_image = Image.open(screenshot_bytes)
            extracted_text = pytesseract.image_to_string(screenshot_image).strip()

            if extracted_text and is_valid_text(extracted_text):
                given_value_str = extracted_text
                given_value = parse_value(given_value_str)
                top_value_parsed = parse_value(top_value)
                bottom_value_parsed = parse_value(bottom_value)
                percentage = round(((given_value - bottom_value_parsed) / (top_value_parsed - bottom_value_parsed)) * 100, 1)
                percentage = max(min(percentage, 100), 0)  # Cap the percentage between 0 and 100
                print(f"Current DPS: {extracted_text} - Percentage: {percentage * scale} \n")
            else:
                percentage = max(min(round(percentage, 0) - 5, 100), 0)
                if percentage <= 4.9:
                    percentage = 0
                print(f"Invalid or no combat data found. Percentage: {percentage * scale} \n")

            for device_id, device in client.devices.items():
                if device.actuators:
                    await device.actuators[0].command(float(scale * percentage / 100.0))
                    await device.rotatory_actuators[0].command(rotationscale * percentage / 100.0, True)
        except Exception as e:
            logging.error(f"Error during processing: {e}")

        await asyncio.sleep(0.4)

logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
asyncio.run(main(), debug=True)
