# Vibration Sensor (STM32H755ZI + V2S200DZ)

Firmware and PC tools to acquire vibration data from up to four Syntiant V2S200DZ sensors using an STM32H755ZI (Nucleo-144), then analyze it on a PC.

- **Multi-channel support**: 4 independent DFSDM channels for simultaneous sensor acquisition
- DFSDM captures 1‑bit PDM at 3.2 MHz and converts to 23‑bit PCM at 12.5 kHz per channel
- USB CDC streams framed data to the PC (each channel sends 100 ms frames)
- PC utilities record CSV and perform FFT/Welch PSD/spectrogram analysis

## Features

- **4-channel simultaneous acquisition** via DFSDM1 (Filters 0-3, Channels 1-4)
- DFSDM + DMA double-buffered acquisition per channel
- USB CDC data streaming (virtual COM)
- Channel identification via SOF markers (0x55555555 - 0x55555558)
- Python analysis pipeline (no SciPy required)
- Practical bandwidth (sensor-limited): ~20 Hz – 1 kHz

## Data framing

Each frame (100 ms per channel) consists of 32-bit integers (5012 bytes total):

- **SOF (Start of Frame)**: Channel-specific marker
  - Channel 1: 0x55555555
  - Channel 2: 0x55555556
  - Channel 3: 0x55555557
  - Channel 4: 0x55555558
- **Timestamp**: ms since MCU startup (uint32)
- **PCM samples**: 1250 samples (23-bit signed, right-shifted by 8 bits to fit in 32-bit)
- **EOF (End of Frame)**: 0xAAAAAAAA

Notes:
- 1250 samples/frame ÷ 12,500 Hz = 100 ms per frame
- Full buffer = 2500 samples = 200 ms; each half-buffer DMA interrupt sends 1250 samples (100 ms)
- Channels are round-robin polled in the main loop for fairness
- SOF markers identify which channel the frame belongs to
- If you change SOF/EOF, pick patterns that cannot appear from DFSDM output when viewed as bytes

## Repository structure

```
VibrationSensor-V2S200DZ/
├── README.md                     # This file
├── analyze_vibration.py          # Python frequency analysis tool
├── read_cdc.c                    # C program for USB CDC data acquisition (CSV format)
├── record_cdc.c                  # C program for USB CDC data acquisition (binary format)
├── read_raw.py                   # Python tool to read and analyze binary .raw files
└── vibration_dfsdm/              # STM32 firmware project
		├── vibration_dfsdm.ioc       # STM32CubeMX configuration
		├── .project, .mxproject      # STM32CubeIDE metadata
		├── CM4/                      # Cortex-M4 core files (unused in this project)
		├── CM7/                      # Cortex-M7 core (main application)
		│   ├── Core/                 # App sources/headers/startup
		│   ├── USB_DEVICE/           # USB device (CDC) app/target
		│   └── STM32H755ZITX_*       # Linker scripts
		├── Common/                   # Dual-core boot support
		├── Drivers/                  # HAL, CMSIS, BSP
		└── Middlewares/ST/STM32_USB_Device_Library/
```

## Build and flash (firmware)

Requirements:
- STM32CubeIDE / STM32CubeMX toolchain
- NUCLEO-H755ZI board and USB cable
- Up to 4 V2S200DZ sensors connected to DFSDM1 channels 1-4

Hardware connections:
- All DFSDM channels use 3.2 MHz clock (system clock / 25)
- Each channel requires: DATIN and CKOUT pins (refer to STM32H755ZI pinout)
- Channels 1-4 map to Filters 0-3 respectively

Steps:
1. Open `vibration_dfsdm/vibration_dfsdm.ioc` in STM32CubeIDE and build the CM7 target.
2. Flash the board with ST-Link.
3. Connect the board's USB OTG (not the ST-Link interface) to the PC.
4. Yellow LED toggles on successful USB transmissions; Green LED indicates Filter 0 activity.

## Capture on PC (Linux/WSL)

**Windows users:** Attach the USB port to WSL using `usbipd`. This is the recommended approach for Windows. See [Reference 5](#references) for detailed instructions.

### Option 1: CSV Format (read_cdc.c)

Compile and run the USB CDC reader for CSV output:

```bash
gcc read_cdc.c -O3 -o read_cdc
timeout 5 ./read_cdc -p /dev/ttyACM0 -o data.csv
```

The CSV output format depends on the `read_cdc.c` implementation:
- May include channel identification from SOF markers
- Typical columns: `timestamp_us, data` (or `timestamp_us, channel, data` if multi-channel parsing is implemented)
- You may need to update `read_cdc.c` to parse channel-specific SOF values (0x55555555-0x55555558 for channels 1-4)

### Option 2: Binary Format (record_cdc.c) - Recommended for Long Recordings

For smaller, more predictable file sizes, use `record_cdc.c` which writes raw binary data:

```bash
gcc record_cdc.c -O3 -o record_cdc
# Record from a specific channel (1-4)
timeout 60 ./record_cdc -p /dev/ttyACM0 -c 1 -o data/channel1.raw
```

**Arguments:**
- `-p`: USB CDC port (default: `/dev/ttyACM1`)
- `-c`: Channel number to capture (1-4, selects SOF marker 0x55555555-0x55555558)
- `-o`: Output binary file (default: `data/vibration_data.raw`)

**Advantages of binary format:**
- **Compact storage**: ~40% smaller than CSV (4 bytes per sample vs ~7 bytes in text)
- **Predictable file size**: Exactly 5004 bytes per frame (4-byte timestamp + 1250 × 4-byte samples)
- **Faster I/O**: No text conversion overhead
- **Frame validation**: Automatically checks SOF/EOF markers and frame timing

**File format:**
- Continuous binary stream of frames without SOF/EOF markers
- Each frame: 4-byte timestamp (uint32, milliseconds) + 1250 × 4-byte samples (int32)
- Total: 5004 bytes per 100 ms frame = ~50 KB/second per channel

## Analyze on PC

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install numpy pandas matplotlib
```

### For CSV files (from read_cdc.c)

Run the analysis (required arguments shown):

```bash
python analyze_vibration.py \
	--input data.csv \
	--fs 12500 \
	--calib 0.00000212 \
	--outdir ./analysis
```

Outputs in `--outdir`:
- `psd_welch.csv` — frequency vs PSD
- `psd_welch.png` — PSD plot (Welch)
- `amplitude_spectrum.png` — single-sided amplitude spectrum
- `spectrogram.png` — PSD spectrogram

Argument notes:
- `--input`: CSV from `read_cdc.c`
- `--fs`: sampling rate in Hz (default pipeline: 12500)
- `--calib`: counts→g (example provided)
- `--outdir`: output directory for plots/CSV

### For binary files (from record_cdc.c)

Use `read_raw.py` to analyze binary `.raw` files directly:

#### Quick PSD Analysis (recommended)

```bash
# Basic PSD plot (default settings)
python read_raw.py data/channel1.raw --psd

# Custom output directory and frequency range
python read_raw.py data/channel1.raw --psd -o results/ -fmax 2000

# Generate all plots (PSD + amplitude + spectrogram) and CSV
python read_raw.py data/channel1.raw --psd --save-amplitude --save-spectrogram --save-csv

# Custom analysis parameters
python read_raw.py data/channel1.raw --psd \
    --fs 12500 \
    --calib 0.00000212 \
    --nperseg 4096 \
    --overlap 0.5 \
    -o results/
```

**PSD mode options:**
- `--psd`: Enable PSD analysis mode
- `--fs`: Sampling rate in Hz (default: 12500)
- `--calib`: Calibration factor counts→g (default: 0.00000212)
- `--nperseg`: FFT segment length (default: 4096)
- `--overlap`: Welch overlap fraction 0-0.95 (default: 0.5)
- `-fmax`: Maximum frequency to display in Hz
- `-o`: Output directory for plots
- `--save-amplitude`: Also generate amplitude spectrum plot
- `--save-spectrogram`: Also generate spectrogram plot
- `--save-csv`: Export PSD data to CSV file

#### Timestamp Validation (default mode)

```bash
# Check timestamp gaps (default: 100 ms expected)
python read_raw.py data/channel1.raw

# Specify custom expected gap
python read_raw.py data/channel1.raw --gap 100
```

This mode validates frame timing and reports any timestamp anomalies.

#### Using as a Python Module

You can also import `read_raw.py` in your own scripts:

```python
from read_raw import read_raw_file, plot_raw_psd

# Read timestamps and samples
timestamps, samples = read_raw_file('data/channel1.raw')
print(f"Loaded {len(timestamps)} frames")
print(f"Sample array shape: {samples.shape}")  # (num_frames, 1250)

# Generate PSD analysis
results = plot_raw_psd(
    raw_file_path='data/channel1.raw',
    fs=12500,
    calib=0.00000212,
    nperseg=4096,
    output_dir='results/',
    skip_amplitude=False,      # Generate amplitude plot
    skip_spectrogram=False,    # Generate spectrogram
    skip_csv=False             # Export CSV
)

# Access results
print(f"PSD plot saved to: {results['psd_plot']}")
print(f"Peak frequency: {results['frequencies'][results['psd'].argmax()]:.1f} Hz")
```

## Calibration note

Approximate acceleration from counts (example scaling):

accel[g] ≈ pcm × (17.7828 / 2^23)

Adjust to your calibrated chain.

## Troubleshooting

- **No data on /dev/ttyACM0**: ensure OTG port is used and firmware is running.
- **Frame interval/size warnings**: may indicate dropped/partial USB packets.
- **Mixed channel data**: Check SOF values in captured frames - each frame should start with 0x55555555-0x55555558 indicating channels 1-4.
- **LED behavior**:
  - Yellow LED toggles: successful USB transmissions
  - Yellow LED off: USB transmission failures (check `usb_drop` counter)
  - Green LED: Filter 0 (Channel 1) half-buffer complete events
- **Channel synchronization**: All 4 channels start with 20ms delays between them to stagger DMA operations.
- If you change sample rate, number of channels, or SOF/EOF markers, update both firmware and PC tools accordingly.

## References

1. V2S200DZ Datasheet — https://static1.squarespace.com/static/6488b0b8150a045d2d112999/t/67521f2adb4a8e0c75ecfd53/1733435181145/V2S200DZ.pdf
2. AN4990 — https://www.st.com/resource/en/application_note/an4990-getting-started-with-sigmadelta-digital-interface-on-applicable-stm32-microcontrollers-stmicroelectronics.pdf
3. RM0399 — https://www.st.com/resource/en/reference_manual/rm0399-stm32h745755-and-stm32h747757-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
4. STM32 USB Wiki — https://wiki.st.com/stm32mcu/wiki/Category:USB
5. WSL USB passthrough — https://learn.microsoft.com/en-us/windows/wsl/connect-usb

