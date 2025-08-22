import time
import logging
import csv
import argparse
from pathlib import Path

import recorder

# Custom colored formatter for console output
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    # ANSI color codes
    HEADERS = {
        'DEBUG': '\033[92mD: ',      # Green
        'INFO': '\033[97mI: ',       # White  
        'WARNING': '\033[93mW: ',    # Yellow
        'ERROR': '\033[91mE: ',      # Red
        'CRITICAL': '\033[95mC: ',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, recorder):
        log_header = self.HEADERS.get(recorder.levelname, '')
        recorder.levelname = f"{log_header}{recorder.levelname}{self.RESET}"
        recorder.msg = f"{log_header}[%(name)s] {recorder.msg}{self.RESET}"
        return super().format(recorder)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
# Get the root logger which has the handler from basicConfig
logger = logging.getLogger()
handler = logger.handlers[0]
handler.setFormatter(ColoredFormatter())

# Now set up our module logger to use the same handler
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.propagate = False  # Prevent duplicate logs

parser = argparse.ArgumentParser(description='Record vibration of CMG.')
parser.add_argument('-m', '--comment', metavar='comment', help='comment for this execution', default='')
args = parser.parse_args()

vib_port = recorder.det_vib_port()
cmg_port = recorder.det_cmg_port()
snid = recorder.get_cmg_snid(cmg_port)

info_dir = Path.cwd() / 'whsp_gimsp' / 'info.csv'
data_dir = Path.cwd() / 'whsp_gimsp' / time.strftime('%Y%m%d_%H%M%S')
data_dir.mkdir(parents=True, exist_ok=True)
if not info_dir.exists():
    with open(info_dir, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'SNID', 'Title', 'Comment'])
with open(info_dir, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), snid.rstrip('\x00'), 'whsp_gimsp', args.comment])

wheel_speeds = [-100, -90, -80, -70, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
gimbal_speeds = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]

# First 
logger.info(f'Starting recording session with SNID: {snid}')
recorder.rot_wh_gim(wheel_speeds[0], gimbal_speeds[0], cmg_port)
time.sleep(60)  # Allow initial speeds to stabilize

logger.info('wheel speed,\tgimbal speed')
for ws in wheel_speeds:
    for gs in gimbal_speeds:
        logger.info(f'{ws},\t{gs}')
        recorder.rot_wh_gim(ws, gs, cmg_port)
        time.sleep(50)  # Allow speeds to stabilize
        recorder.record(f'{str(data_dir)}/{ws}_{gs}.csv', 10, vib_port)
recorder.stop(cmg_port)