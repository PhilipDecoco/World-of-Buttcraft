import pytesseract
from PIL import Image
import pyautogui
import io
import asyncio
import logging
import sys
import configparser
from buttplug import Client, WebsocketConnector, ProtocolSpec

# Function to strip comments from a config value
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
    #connect buttplugio devices
    await client.start_scanning()
    print("Scanning Devices...")
    await asyncio.sleep(10)
    await client.stop_scanning()
    client.logger.info(f"Devices: {client.devices}")

    percentage = 0

    while True:
        screenshot = pyautogui.screenshot(region=region)
        screenshot_bytes = io.BytesIO()
        screenshot.save(screenshot_bytes, format='PNG')
        screenshot_bytes.seek(0)
        screenshot_image = Image.open(screenshot_bytes)
        extracted_text = pytesseract.image_to_string(screenshot_image)

        if extracted_text.strip() and is_valid_text(extracted_text.strip()):
            given_value_str = extracted_text
            given_value = parse_value(given_value_str)
            percentage = round(((given_value - parse_value(bottom_value)) / (parse_value(top_value) - parse_value(bottom_value))) * 100, 1)
            percentage = max(min(percentage, 100), 0)  # Cap the percentage between 0 and 100
            print(f"Current DPS: {extracted_text} - Percentage: {percentage} \n")

        else:
                percentage = round(percentage, 0) - 5
                if percentage == -5:
                    print("Invalid or no combat data found. Percentage:", "0")
                else:
                    print(f"Invalid or no combat data found. Percentage: {percentage} \n")
                
                percentage = max(min(percentage, 100), 0)
                if percentage <= 4.9:
                    percentage = 0
                await asyncio.sleep(1)

        if len(client.devices) != 0:
            device = client.devices[0]

            if len(device.actuators) != 0:
                await device.actuators[0].command(float(percentage * scale / 100.0 ))
            if len(device.actuators) != 1:
                await device.actuators[1].command(float(percentage * scale / 100.0 ))
                

        await asyncio.sleep(0.4)

logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
asyncio.run(main(), debug=True)
