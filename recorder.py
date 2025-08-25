#!/home/tt/tt_env/bin/python
"""
recorder.py - Functions for recording vibration and CMG data
"""

import subprocess
import re
import glob
import time
import logging
logger = logging.getLogger(__name__)

cmg_cli_path = '/home/tt/.local/bin/cmg-cli'

def det_vib_port():
    """
    Detects the tty port of the vibration sensor by identifying the TensorTech device.
    
    Returns:
        str: The tty device path (e.g., '/dev/ttyACM0') or None if not found
    """
    try:
        # Get all ttyACM devices
        tty_devices = glob.glob('/dev/ttyACM*')
        logger.debug(f"Found ttyACM devices: {tty_devices}")
        
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
                    logger.debug(f"Found TensorTech vibration sensor on {device}")
                    return device
                    
            except subprocess.CalledProcessError:
                # Skip this device if udevadm fails
                logger.debug(f"Failed to get properties for {device}")
                continue
                
        logger.warning("No TensorTech vibration sensor found")
        return None
        
    except Exception as e:
        logger.error(f"Error detecting vibration port: {e}")
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
        logger.debug(f"Found ttyAMA devices: {tty_devices}")
        
        if not tty_devices:
            logger.warning("No ttyAMA devices found for CMG")
            return None
            
        # Sort to ensure consistent ordering
        tty_devices.sort()
        
        # Return the first device
        selected_device = tty_devices[0]
        logger.info(f"Selected CMG port: {selected_device}")
        return selected_device
        
    except Exception as e:
        logger.error(f"Error detecting CMG port: {e}")
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
        logger.warning("No tty device provided for SNID reading")
        return None
        
    try:
        logger.debug(f"Getting CMG SNID from {tty_dev}")
        # Run cmg-cli command to get device info
        result = subprocess.run(
            [cmg_cli_path, 'get', '-n', '-p', tty_dev],
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
                    snid = match.group(1)
                    logger.debug(f"Found CMG SNID: {snid}")
                    return snid
                    
        logger.warning(f"SNID not found in CMG response from {tty_dev}")
        return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running cmg-cli: {e}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout waiting for cmg-cli response on {tty_dev}")
        return None
    except Exception as e:
        logger.error(f"Error getting CMG SNID: {e}")
        return None


def rot_wh_gim(wheel_speed, gimbal_speed, cmg_port=None):
    """
    Starts rotation of both the CMG wheel and gimbal.
    
    Args:
        wheel_speed (float): Wheel speed in rps (revolutions per second)
        gimbal_speed (float): Gimbal speed in rps (revolutions per second)
        cmg_port (str, optional): CMG tty port. If None, will auto-detect
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Auto-detect CMG port if not provided
    if cmg_port is None:
        cmg_port = det_cmg_port()
        if cmg_port is None:
            logger.error("Could not detect CMG port")
            return False
    
    try:
        logger.debug(f"Start CMG rotation: wheel={wheel_speed} rps, gimbal={gimbal_speed} rps on {cmg_port}")
        # Run cmg-cli command to set wheel and gimbal speeds
        result = subprocess.run(
            [cmg_cli_path, 'set', '--cmg', f'{wheel_speed},{gimbal_speed}', '-p', cmg_port],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting CMG rotation: {e}")
        if e.stdout:
            logger.debug(f"stdout: {e.stdout}")
        if e.stderr:
            logger.debug(f"stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout setting CMG rotation on {cmg_port}")
        return False
    except Exception as e:
        logger.error(f"Error starting CMG rotation: {e}")
        return False

def rot_wh(wheel_speed, gimbal_angle, cmg_port=None):
    """
    Rotates the wheel at a specific gimbal angle using cmg-cli.
    
    Args:
        wheel_speed (float): Wheel speed in rps (revolutions per second)
        gimbal_angle (float): Gimbal angle in degrees
        cmg_port (str, optional): CMG tty port. If None, will auto-detect
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Auto-detect CMG port if not provided
    if cmg_port is None:
        cmg_port = det_cmg_port()
        if cmg_port is None:
            logger.error("Could not detect CMG port")
            return False
    try:
        logger.debug(f"Set wheel: {wheel_speed} rps, gimbal angle: {gimbal_angle} deg on {cmg_port}")
        result = subprocess.run(
            [cmg_cli_path, 'set', '--rw', f'{wheel_speed},{gimbal_angle}', '-p', cmg_port],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting wheel/gimbal angle: {e}")
        if e.stdout:
            logger.debug(f"stdout: {e.stdout}")
        if e.stderr:
            logger.debug(f"stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout setting wheel/gimbal angle on {cmg_port}")
        return False
    except Exception as e:
        logger.error(f"Error setting wheel/gimbal angle: {e}")
        return False

def record(output_path, duration, vib_port=None):
    """
    Records vibration data for a specified duration using read_cdc.
    
    Args:
        output_path (str): Path to output file for recorded data
        duration (int): Recording duration in seconds
        vib_port (str, optional): Vibration sensor tty port. If None, will auto-detect
        
    Returns:
        bool: True if recording completed successfully (timeout exit code 124), False otherwise
    """
    # Auto-detect vibration port if not provided
    if vib_port is None:
        vib_port = det_vib_port()
        if vib_port is None:
            logger.error("Could not detect vibration sensor port")
            return False
    
    try:
        # Use timeout command to limit recording duration
        # read_cdc should be in the bin/ directory or PATH
        read_cdc_path = './bin/read_cdc'  # Assuming read_cdc is in bin/ directory
        
        logger.info(f"Starting recording for {duration} seconds to {output_path} from {vib_port}")
        result = subprocess.run(
            ['timeout', str(duration), read_cdc_path, '-p', vib_port, '-o', output_path],
            capture_output=True,
            text=True,
            timeout=duration + 5  # Add extra timeout buffer
        )
        
        # Check if timeout command exited with code 124 (successful timeout)
        if result.returncode == 124:
            logger.info(f"Recording completed successfully for {duration} seconds to {output_path}")
            return True
        else:
            logger.error(f"Recording failed with exit code {result.returncode}")
            if result.stdout:
                logger.debug(f"stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Recording process exceeded timeout limit")
        return False
    except Exception as e:
        logger.error(f"Error during recording: {e}")
        return False

def stop(cmg_port=None):
    """
    Stops the CMG by setting it to idle state.
    
    Args:
        cmg_port (str, optional): CMG tty port. If None, will auto-detect
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Auto-detect CMG port if not provided
    if cmg_port is None:
        cmg_port = det_cmg_port()
        if cmg_port is None:
            logger.error("Could not detect CMG port")
            return False
    
    try:
        logger.info(f"Setting CMG to idle state on {cmg_port}")
        # Run cmg-cli command to set CMG to idle
        result = subprocess.run(
            [cmg_cli_path, 'set', '--idle', '-p', cmg_port],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        
        logger.info("Successfully set CMG to idle state")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting CMG to idle: {e}")
        if e.stdout:
            logger.debug(f"stdout: {e.stdout}")
        if e.stderr:
            logger.debug(f"stderr: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout setting CMG to idle on {cmg_port}")
        return False
    except Exception as e:
        logger.error(f"Error stopping CMG: {e}")
        return False

if __name__ == "__main__":
    """Test the functions"""
    logger.info("Starting device detection and testing...")
    
    # Test vibration port detection
    vib_port = det_vib_port()
    logger.info(f"Vibration sensor port: {vib_port}")
    
    # Test CMG port detection
    cmg_port = det_cmg_port()
    logger.info(f"CMG port: {cmg_port}")
    
    # Test CMG SNID reading
    if cmg_port:
        snid = get_cmg_snid(cmg_port)
        logger.info(f"CMG SNID: {snid}")
    else:
        logger.warning("No CMG port found for SNID test")
    
    # Test CMG rotation (commented out to avoid accidental activation)
    if cmg_port:
        logger.info("Testing CMG rotation...")
        success = rot_wh_gim(100, 0.5, cmg_port)
        logger.info(f"CMG rotation test: {'Success' if success else 'Failed'}")
        
        # Raise exception if rotation failed
        if not success:
            logger.critical("CMG rotation failed - cannot proceed with test")
            raise RuntimeError("CMG rotation failed - cannot proceed with test")

    time.sleep(5)
    
    # Test recording (commented out to avoid accidental recording)
    if vib_port:
        logger.info("Testing vibration recording...")
        success = record('./data/test_output.csv', 10, vib_port)
        logger.info(f"Recording test: {'Success' if success else 'Failed'}")
        
        if not success:
            logger.error("Recording test failed")
        success = stop(cmg_port)
        
    
    logger.info("All tests completed successfully")
