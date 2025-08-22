#!/usr/bin/env python3
"""
record.py - Functions for recording vibration and CMG data
"""

import subprocess
import re
import glob


def det_vib_port():
    """
    Detects the tty port of the vibration sensor by identifying the TensorTech device.
    
    Returns:
        str: The tty device path (e.g., '/dev/ttyACM0') or None if not found
    """
    try:
        # Get all ttyACM devices
        tty_devices = glob.glob('/dev/ttyACM*')
        
        for device in tty_devices:
            try:
                # Run udevadm to get device properties
                result = subprocess.run(
                    ['udevadm', 'info', '-q', 'property', '-n', device],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Check if this device has ID_USB_VENDOR=TensorTech
                if 'ID_USB_VENDOR=TensorTech' in result.stdout:
                    return device
                    
            except subprocess.CalledProcessError:
                # Skip this device if udevadm fails
                continue
                
        return None
        
    except Exception as e:
        print(f"Error detecting vibration port: {e}")
        return None


def det_cmg_port():
    """
    Detects the tty port of the CMG by choosing the first available ttyAMA device.
    
    Returns:
        str: The first tty device path (e.g., '/dev/ttyAMA4') or None if not found
    """
    try:
        # Get all ttyAMA devices
        tty_devices = glob.glob('/dev/ttyAMA*')
        
        if not tty_devices:
            return None
            
        # Sort to ensure consistent ordering
        tty_devices.sort()
        
        # Return the first device
        return tty_devices[0]
        
    except Exception as e:
        print(f"Error detecting CMG port: {e}")
        return None


def get_cmg_snid(tty_dev):
    """
    Reads the SNID of the CMG from the specified tty port.
    
    Args:
        tty_dev (str): The tty device path (e.g., '/dev/ttyACM0')
        
    Returns:
        str: The SNID of the CMG (e.g., 'TCM102052') or None if not found
    """
    if not tty_dev:
        return None
        
    try:
        # Run cmg-cli command to get device info
        result = subprocess.run(
            ['/home/tt/.local/bin/cmg-cli', 'get', '-n', '-p', tty_dev],
            capture_output=True,
            text=True,
            check=True,
            timeout=10  # Add timeout to prevent hanging
        )
        
        # Search for SNID in the output
        for line in result.stdout.splitlines():
            if 'SNID:' in line:
                # Extract SNID value (format: "SNID: TCM102052")
                match = re.search(r'SNID:\s*(\S+)', line)
                if match:
                    return match.group(1)
                    
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"Error running cmg-cli: {e}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Timeout waiting for cmg-cli response on {tty_dev}")
        return None
    except Exception as e:
        print(f"Error getting CMG SNID: {e}")
        return None


if __name__ == "__main__":
    """Test the functions"""
    print("Testing device detection functions...")
    
    # Test vibration port detection
    vib_port = det_vib_port()
    print(f"Vibration sensor port: {vib_port}")
    
    # Test CMG port detection
    cmg_port = det_cmg_port()
    print(f"CMG port: {cmg_port}")
    
    # Test CMG SNID reading
    if cmg_port:
        snid = get_cmg_snid(cmg_port)
        print(f"CMG SNID: {snid}")
    else:
        print("No CMG port found for SNID test")
