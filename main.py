import network
import urequests as requests
import ujson as json
from utime import sleep, ticks_us, time, mktime
from uQR import QRCode
import ntptime
import machine
import gc
from machine import Pin, I2C
import ssd1306
import math
# ESP32 Pin assignment 
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

oled.poweron()

def crc16(data: str) -> str:
    crc_table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
        0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
        0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
        0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
        0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
        0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
        0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
        0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
        0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
        0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
        0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
        0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
        0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
        0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
        0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0,
    ]
    crc = 0xFFFF
    for c in data.encode():
        j = (c ^ (crc >> 8)) & 0xFF
        crc = crc_table[j] ^ (crc << 8)
    
    final_crc = crc & 0xFFFF
    return '{:04X}'.format(final_crc)


# MD5 implementation for MicroPython
import struct

# Constants and Left Rotate Function
S = [7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 + [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4
K = [
    0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
    0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
    0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
    0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
    0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c, 0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
    0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
    0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
    0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
]

def left_rotate(x, amount):
    x &= 0xFFFFFFFF
    return ((x << amount) | (x >> (32 - amount))) & 0xFFFFFFFF

def md5(message):
    # Initialize variables
    a0, b0, c0, d0 = 0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476

    # Pre-processing: Padding the message
    original_byte_len = len(message)
    original_bit_len = original_byte_len * 8
    message += b'\x80'
    message += b'\x00' * ((56 - len(message) % 64) % 64)
    message += struct.pack('<Q', original_bit_len)

    # Process the message in 512-bit (64-byte) chunks
    for i in range(0, len(message), 64):
        chunk = message[i:i + 64]
        M = struct.unpack('<' + 'I' * 16, chunk)
        
        # Initialize hash value for this chunk
        A, B, C, D = a0, b0, c0, d0

        # Main loop
        for j in range(64):
            if j < 16:
                F = (B & C) | (~B & D)
                g = j
            elif j < 32:
                F = (D & B) | (~D & C)
                g = (5 * j + 1) % 16
            elif j < 48:
                F = B ^ C ^ D
                g = (3 * j + 5) % 16
            else:
                F = C ^ (B | ~D)
                g = (7 * j) % 16
            
            F = (F + A + K[j] + M[g]) & 0xFFFFFFFF
            A, D, C, B = D, C, B, (B + left_rotate(F, S[j])) & 0xFFFFFFFF
        
        # Add this chunk's hash to result so far
        a0 = (a0 + A) & 0xFFFFFFFF
        b0 = (b0 + B) & 0xFFFFFFFF
        c0 = (c0 + C) & 0xFFFFFFFF
        d0 = (d0 + D) & 0xFFFFFFFF

    # Produce the final hash value (digest) as a 128-bit number
    return struct.pack('<IIII', a0, b0, c0, d0).hex()

PayloadFormatIndicator = "00"
PointOfInitiationMethod = "01"
UnionPayMerchant = "15"
GlobalUniqueIdentifier = "29"
MerchantCategoryCode = "52"
TransactionCurrency = "53"
TransactionAmount = "54"
CountryCode = "58"
MerchantName = "59"
MerchantCity = "60"
AdditionalData = "62"
MerchantInformationLanguageTemplate = "64"
TimeStamp = "99"
CRC = "63"

KHQRData = {
    "currency": {
        "usd": "840",
        "khr": "116",
    },
    "merchantType": {
        "merchant": "merchant",
        "individual": "individual",
    },
}

# config 
qr_version = "01"   
PointOfInitiationMethod = "11"     #static qr
account_info = "kimhoir_na_2002@abaa"       # bakong
MCC = "5999"    # by default
Transaction_Currency = KHQRData["currency"]["khr"]    # by default
CountryCode_ = "KH"
City = "Phnom Penh"     # tag 60
Transaction_Amount = "100"    # tag 54 
name = "Kimhoir"    # tag 59
# create qr data
def create_qr():
# Get current time in seconds since Unix epoch
    timestamp = 1000000000000 + int(round(time() * 1000) + ticks_us() / 1000)
    print(timestamp)
    str_timestamp = str(timestamp)

    data_string = (PayloadFormatIndicator + f"{len(qr_version):02d}" + qr_version
                + PointOfInitiationMethod + f"{len(PointOfInitiationMethod):02d}" + PointOfInitiationMethod
                + GlobalUniqueIdentifier + f"{4 + len(account_info):02d}00{len(account_info)}" + account_info
                + MerchantCategoryCode + f"{len(MCC):02d}" + MCC
                + TransactionCurrency + f"{len(Transaction_Currency):02d}" + Transaction_Currency
                + CountryCode + f"{len(CountryCode_):02d}" + CountryCode_
                + MerchantName + f"{len(name):02d}" + name
                + MerchantCity + f"{len(City)}" + City
                + TransactionAmount + f"{len(Transaction_Amount):02d}" + Transaction_Amount
                + TimeStamp + "1700" + f"{len(str_timestamp):02d}" + str_timestamp)
    
    khqr = data_string + "63" + "04"
    crc = crc16(khqr)
    khqr += crc
    return khqr

def connect_wifi():
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect("Wokwi-GUEST", "")

    while not station.isconnected():
        print('Connecting to Wi-Fi...')
        sleep(1)

    print('Connected to Wi-Fi')
    print(station.ifconfig())



# Connect to Wi-Fi
connect_wifi()

# Set the RTC using NTP
ntptime.settime()

# Get the current time from RTC
rtc = machine.RTC()
current_time = rtc.datetime()

print("RTC time after NTP sync:", current_time)
local_hour = current_time[4] + 7

# Handle day overflow
if local_hour >= 24:
    local_hour -= 24
    # Increment the day, and handle month/year overflow if needed
    # Simplified: does not handle month/year changes
    local_day = current_time[2] + 1
else:
    local_day = current_time[2]

time_tuple = (current_time[0], current_time[1], local_hour, current_time[4], current_time[5], current_time[6], current_time[7], 0)

# Convert to Unix timestamp (seconds since epoch)
unix_time = mktime(time_tuple)

print("Current time in seconds since the Unix epoch:", unix_time * 1000)

data_string = create_qr()
# print(data_string)
# print(qr_to_md5(data_string))
# Generate and print QR code

qr_code = QRCode()
qr_code.add_data(data_string)
matrix = qr_code.get_matrix()
# print(qr_code.render_matrix())
for y in range(len(matrix)):                   # Scaling the bitmap by 2
    for x in range(len(matrix[0])):            # because my screen is tiny.
        value = not matrix[int(y)][int(x)]   # Inverting the values because
        oled.pixel(x, y, value)
oled.show()

url = 'https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5'
# Headers for the POST request
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiZWYyNjdhYmZmMGEwNDA2In0sImlhdCI6MTcyMTEyMjkxNywiZXhwIjoxNzI4ODk4OTE3fQ.4SvMc05C_DQNx9e2F2t0U9a_OrPjmttDxyxQP9LAc0U'
}

data = {
    'md5': md5(data_string.encode('utf-8'))
}
data_json = json.dumps(data)
# Explicitly call garbage collection to free up memory
gc.collect()
# Check the status code and print the response
get_money = False
while not get_money:
    try:
        response = requests.post(url, headers=headers, data=data_json)
        if response.status_code == 200:
            data = response.json()
            if data['responseMessage'] == "Success":
                get_money = True
            try:
                print('Hash:', data['data']['hash'])
                print('From Account ID:', data['data']['fromAccountId'])
                print('To Account ID:', data['data']['toAccountId'])
                print('Currency:', data['data']['currency'])
                print('Amount:', data['data']['amount'])
                print('Description:', data['data']['description'])
                print('Created Date (ms):', data['data']['createdDateMs'])
                print('Acknowledged Date (ms):', data['data']['acknowledgedDateMs'])
            except KeyError:
                print("No data")
        else:
            print(f'POST request failed with status code {response.status_code}.')
        response.close()  # Close the response to free up memory
    except OSError as e:
        print(f'Network error: {e}')
        sleep(5)  # Wait before retrying
    except Exception as e:
        print(f'Error: {e}')
    sleep(1)
    gc.collect()  # Call garbage collection after each iteration

if get_money:
    print("I got money HAHHAHAHHAHAHHAHAH")