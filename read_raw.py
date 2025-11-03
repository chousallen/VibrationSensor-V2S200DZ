"""
Script to read and analyze raw vibration data files containing frames with timestamps and samples.
Each frame consists of:
- 1 timestamp (uint32_t, 4 bytes)
- 1250 samples (int32_    # Save PSD data to CSV (optional)
    psd_csv_path = None
    if not skip_csv:
        psd_csv_path = output_dir / f"{raw_file_path.stem}_psd.csv"
        print(f"Saving PSD data: {psd_csv_path}")
        if pd is not None:
            pd.DataFrame({
                'freq_hz': freqs_psd, 
                'psd_g2_per_hz': psd
            }).to_csv(psd_csv_path, index=False)
        else:
            # Fallback CSV writing without pandas
            with open(psd_csv_path, 'w') as f:
                f.write("freq_hz,psd_g2_per_hz\n")
                for freq, psd_val in zip(freqs_psd, psd):
                    f.write(f"{freq},{psd_val}\n")
    
    results = {

Modes:
1. Timestamp Analysis (default): Validates timestamp gaps and displays sample statistics
   Usage: python read_raw.py <path_to_raw_file> [--gap <expected_gap>]
   
2. PSD Analysis: Performs frequency domain analysis with PSD plots
   Usage: python read_raw.py <path_to_raw_file> --psd [options]
   
Examples:
  python read_raw.py file.raw                           # Timestamp analysis
  python read_raw.py file.raw --psd                     # PSD plot only (default)
  python read_raw.py file.raw --psd -o results/         # PSD plot in custom directory
  python read_raw.py file.raw --psd --save-csv          # PSD plot + CSV data
  python read_raw.py file.raw --psd --save-amplitude    # PSD + amplitude plots
  python read_raw.py file.raw --psd --save-spectrogram  # PSD + spectrogram plots
"""

import sys
import struct
from pathlib import Path
import numpy as np
import argparse
try:
    import pandas as pd
except ImportError:
    print("Warning: pandas not available. PSD mode CSV export will be limited.")
    pd = None

import analyze_vibration

def read_raw_file(file_path):
    """
    Read raw data file and extract timestamps and samples from each frame.
    
    Args:
        file_path (str): Path to the raw data file
        
    Returns:
        tuple: (timestamps_list, samples_array)
            - timestamps_list: List of timestamps
            - samples_array: numpy array of shape (num_frames, 1250) containing all samples
    """
    timestamps = []
    all_samples = []
    
    # Frame structure: 1 uint32_t timestamp + 1250 int32_t samples
    timestamp_size = 4  # uint32_t = 4 bytes
    sample_size = 4     # int32_t = 4 bytes
    samples_per_frame = 1250
    frame_size = timestamp_size + (samples_per_frame * sample_size)
    
    try:
        with file_path.open('rb') as f:
            frame_count = 0
            
            while True:
                # Read timestamp (uint32_t, little-endian)
                timestamp_data = f.read(timestamp_size)
                if len(timestamp_data) < timestamp_size:
                    break  # End of file
                
                timestamp = struct.unpack('<I', timestamp_data)[0]
                timestamps.append(timestamp)
                
                # Read the 1250 samples (1250 * 4 bytes = 5000 bytes)
                samples_data = f.read(samples_per_frame * sample_size)
                if len(samples_data) < samples_per_frame * sample_size:
                    print(f"Warning: Incomplete frame {frame_count + 1} at end of file")
                    break
                
                # Unpack samples (int32_t, little-endian)
                samples = struct.unpack(f'<{samples_per_frame}i', samples_data)
                all_samples.append(samples)
                
                frame_count += 1
                
                # Print progress every 1000 frames
                if frame_count % 1000 == 0:
                    print(f"Processed {frame_count} frames...")
            
            # print(f"\nTotal frames processed: {frame_count}")
            
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return [], np.array([])
    except Exception as e:
        print(f"Error reading file: {e}")
        return [], np.array([])
    
    # Convert samples to numpy array
    samples_array = np.array(all_samples) if all_samples else np.array([])
    
    return timestamps, samples_array


def read_raw_file_timestamps_only(file_path):
    """
    Read raw data file and extract only timestamps (for backward compatibility).
    
    Args:
        file_path (str): Path to the raw data file
        
    Returns:
        list: List of timestamps
    """
    timestamps, _ = read_raw_file(file_path)
    return timestamps


def plot_raw_psd(raw_file_path, fs=12500, calib=0.00000212, nperseg=4096, 
                 overlap=0.5, fmax=None, output_dir=None, title=None,
                 skip_amplitude=True, skip_spectrogram=True, skip_csv=True):
    """
    Read raw file and plot PSD using analyze_vibration tools.
    By default, only saves the PSD plot (psd.png).
    
    Args:
        raw_file_path (str or Path): Path to raw data file
        fs (float): Sampling rate in Hz
        calib (float): Calibration factor (units per count)
        nperseg (int): Welch segment length
        overlap (float): Welch overlap fraction (0-0.95)
        fmax (float): Maximum frequency to display (Hz)
        output_dir (str or Path): Output directory for plots
        title (str): Plot title override
        skip_amplitude (bool): Skip amplitude spectrum plot (default: True)
        skip_spectrogram (bool): Skip spectrogram plot (default: True)
        skip_csv (bool): Skip CSV data export (default: True)
        
    Returns:
        dict: Results containing frequencies, PSD, and file paths
    """
    raw_file_path = Path(raw_file_path)
    
    # Read timestamps and samples from raw file
    print(f"Reading raw file: {raw_file_path}")
    timestamps, samples = read_raw_file(raw_file_path)
    
    if len(timestamps) == 0 or samples.size == 0:
        raise ValueError("No data found in raw file")
    
    print(f"Loaded {len(timestamps)} frames with {samples.shape} samples")
    print(f"Sample data type: {samples.dtype}")
    print(f"Sample range: [{samples.min()}, {samples.max()}]")
    
    # Flatten samples to 1D array (concatenate all frames)
    x = samples.flatten()
    
    # Apply calibration
    x = x * calib
    print(f"Applied calibration factor: {calib}")
    print(f"Calibrated range: [{x.min():.6f}, {x.max():.6f}] g")
    
    # Set up output directory
    if output_dir is None:
        output_dir = raw_file_path.parent / f"{raw_file_path.stem}_psd"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Compute Welch PSD using analyze_vibration function
    print(f"Computing Welch PSD (nperseg={nperseg}, overlap={overlap})")
    freqs_psd, psd = analyze_vibration.welch_psd(
        x, fs=fs, nperseg=nperseg, overlap=overlap, 
        window='hann', detrend=True
    )
    
    # Generate plot title
    if title is None:
        title = f"PSD - {raw_file_path.name}"
    
    # Plot PSD using analyze_vibration function
    psd_plot_path = output_dir / f"{raw_file_path.stem}_psd.png"
    print(f"Saving PSD plot: {psd_plot_path}")
    analyze_vibration.plot_psd(freqs_psd, psd, psd_plot_path, fmax=fmax, title=title)
    
    # Save PSD data to CSV (optional)
    psd_csv_path = None
    if not skip_csv:
        psd_csv_path = output_dir / f"{raw_file_path.stem}_psd.csv"
        print(f"Saving PSD data: {psd_csv_path}")
        if pd is not None:
            pd.DataFrame({
                'freq_hz': freqs_psd, 
                'psd_g2_per_hz': psd
            }).to_csv(psd_csv_path, index=False)
        else:
            # Fallback CSV writing without pandas
            with open(psd_csv_path, 'w') as f:
                f.write("freq_hz,psd_g2_per_hz\n")
                for freq, psd_val in zip(freqs_psd, psd):
                    f.write(f"{freq},{psd_val}\n")
    
    results = {
        'timestamps': timestamps,
        'samples': samples,
        'calibrated_signal': x,
        'frequencies': freqs_psd,
        'psd': psd,
        'output_dir': output_dir,
        'psd_plot': psd_plot_path
    }
    
    if psd_csv_path is not None:
        results['psd_csv'] = psd_csv_path
    
    # Create amplitude spectrum if requested
    if not skip_amplitude:
        freqs_amp, amp = analyze_vibration.amplitude_spectrum(
            x, fs=fs, window='hann', detrend=True
        )
        amp_plot_path = output_dir / f"{raw_file_path.stem}_amplitude.png"
        print(f"Saving amplitude spectrum: {amp_plot_path}")
        analyze_vibration.plot_amplitude(
            freqs_amp, amp, amp_plot_path, fmax=fmax, 
            title=f"Amplitude Spectrum - {raw_file_path.name}"
        )
        results['amplitude_freqs'] = freqs_amp
        results['amplitude'] = amp
        results['amplitude_plot'] = amp_plot_path
    
    # Create spectrogram if requested
    if not skip_spectrogram:
        spec_plot_path = output_dir / f"{raw_file_path.stem}_spectrogram.png"
        print(f"Saving spectrogram: {spec_plot_path}")
        nperseg_spec = min(max(256, nperseg//4), len(x))
        analyze_vibration.plot_spectrogram(
            x, fs=fs, outpath=spec_plot_path, nperseg=nperseg_spec, 
            overlap=0.75, window='hann', detrend=True, fmax=fmax
        )
        results['spectrogram_plot'] = spec_plot_path
    
    # Calculate RMS values
    rms_total = analyze_vibration.calculate_rms(x, detrend=False)  # Total RMS (with DC)
    rms_ac = analyze_vibration.calculate_rms(x, detrend=True)     # AC RMS (without DC)
    
    # Print summary statistics
    duration = len(x) / fs
    freq_res = fs / nperseg
    nyquist = fs / 2
    
    print(f"\nAnalysis Summary:")
    print(f"  Total samples: {len(x):,}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Sampling rate: {fs} Hz")
    print(f"  Signal RMS (total): {rms_total:.6f} g")
    print(f"  Signal RMS (AC only): {rms_ac:.6f} g")
    print(f"  Nyquist frequency: {nyquist} Hz")
    print(f"  Frequency resolution: {freq_res:.2f} Hz")
    print(f"  PSD frequency range: {freqs_psd[0]:.2f} - {freqs_psd[-1]:.2f} Hz")
    print(f"  Peak PSD: {psd.max():.2e} g²/Hz at {freqs_psd[np.argmax(psd)]:.1f} Hz")
    
    return results


def check_timestamp_gaps(timestamps, expected_gap=100):
    """
    Check for gaps in timestamps and report any deviations.
    
    Args:
        timestamps (list): List of timestamps
        expected_gap (int): Expected gap between consecutive timestamps
    """
    if len(timestamps) < 2:
        print("Not enough timestamps to check gaps")
        return
    
    print(f"\nChecking timestamp gaps (expected gap: {expected_gap}):")
    print("-" * 60)
    
    gaps = []
    anomalies = []
    
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i-1]
        gaps.append(gap)
        
        if gap != expected_gap:
            anomalies.append({
                'frame': i,
                'prev_timestamp': timestamps[i-1],
                'curr_timestamp': timestamps[i],
                'gap': gap,
                'expected': expected_gap,
                'difference': gap - expected_gap
            })
    
    # Print statistics
    if gaps:
        min_gap = min(gaps)
        max_gap = max(gaps)
        avg_gap = sum(gaps) / len(gaps)
        
        print(f"Gap statistics:")
        print(f"  Min gap: {min_gap}")
        print(f"  Max gap: {max_gap}")
        print(f"  Average gap: {avg_gap:.2f}")
        print(f"  Expected gap: {expected_gap}")
        print(f"  Total gaps analyzed: {len(gaps)}")
    
    # Report anomalies
    if anomalies:
        print(f"\nFound {len(anomalies)} timestamp gaps that deviate from expected {expected_gap}:")
        print("-" * 80)
        
        for anomaly in anomalies[:20]:  # Show first 20 anomalies
            print(f"Frame {anomaly['frame']:6d}: "
                  f"Gap = {anomaly['gap']:6d} "
                  f"(expected {anomaly['expected']:6d}, "
                  f"diff = {anomaly['difference']:+6d}) "
                  f"[{anomaly['prev_timestamp']} -> {anomaly['curr_timestamp']}]")
        
        if len(anomalies) > 20:
            print(f"... and {len(anomalies) - 20} more anomalies")
    else:
        print(f"✓ All timestamp gaps are exactly {expected_gap} as expected!")


def print_timestamps_summary(timestamps, num_to_show=10):
    """
    Print a summary of timestamps.
    
    Args:
        timestamps (list): List of timestamps
        num_to_show (int): Number of timestamps to show from beginning and end
    """
    if not timestamps:
        return
    
    print(f"\nTimestamp Summary:")
    print("-" * 40)
    print(f"Total timestamps: {len(timestamps)}")
    print(f"First timestamp: {timestamps[0]}")
    print(f"Last timestamp: {timestamps[-1]}")
    
    if len(timestamps) > 1:
        duration = timestamps[-1] - timestamps[0]
        print(f"Duration: {duration} time units")
    
    print(f"\nFirst {num_to_show} timestamps:")
    for i, ts in enumerate(timestamps[:num_to_show]):
        print(f"  Frame {i+1:4d}: {ts}")
    
    if len(timestamps) > num_to_show * 2:
        print("  ...")
        print(f"Last {num_to_show} timestamps:")
        for i, ts in enumerate(timestamps[-num_to_show:]):
            frame_num = len(timestamps) - num_to_show + i + 1
            print(f"  Frame {frame_num:4d}: {ts}")


def main():
    """Main function with enhanced command-line interface for both timestamp analysis and PSD plotting."""
    parser = argparse.ArgumentParser(
        description='Read and analyze raw vibration data files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('raw_file', 
                       help='Path to raw data file')
    
    # Mode selection
    parser.add_argument('--psd', action='store_true',
                       help='Enable PSD analysis and plotting mode')
    
    # PSD-specific options
    parser.add_argument('-fs', '--sampling-rate', type=float, default=12500,
                       help='Sampling rate in Hz (for PSD mode)')
    parser.add_argument('-c', '--calib', type=float, default=0.00000212,
                       help='Calibration factor (units per count, for PSD mode)')
    parser.add_argument('-n', '--nperseg', type=int, default=4096,
                       help='Welch segment length (FFT size, for PSD mode)')
    parser.add_argument('--overlap', type=float, default=0.5,
                       help='Welch overlap fraction (0-0.95, for PSD mode)')
    parser.add_argument('-fmax', '--freq-max', type=float, default=None,
                       help='Maximum frequency to display (Hz, for PSD mode)')
    parser.add_argument('-o', '--output-dir', type=str, default=None,
                       help='Output directory for plots and data (for PSD mode)')
    parser.add_argument('-t', '--title', type=str, default=None,
                       help='Plot title override (for PSD mode)')
    parser.add_argument('--save-amplitude', action='store_true',
                       help='Save amplitude spectrum plot (for PSD mode)')
    parser.add_argument('--save-spectrogram', action='store_true',
                       help='Save spectrogram plot (for PSD mode)')
    parser.add_argument('--save-csv', action='store_true',
                       help='Save PSD data to CSV file (for PSD mode)')
    
    # Timestamp analysis options
    parser.add_argument('--gap', type=int, default=100,
                       help='Expected timestamp gap for validation (default mode)')
    
    args = parser.parse_args()
    
    # Validate input file
    file_path = Path(args.raw_file)
    if not file_path.is_file():
        print(f"Error: File '{file_path}' does not exist")
        sys.exit(1)
    
    print(f"Reading raw data file: {file_path}")
    print(f"File size: {file_path.stat().st_size:,} bytes")
    
    if args.psd:
        # PSD Analysis Mode
        print("=" * 60)
        print("PSD ANALYSIS MODE")
        print("=" * 60)
        
        # Validate PSD parameters
        if args.overlap < 0 or args.overlap >= 1:
            print("Error: Overlap must be between 0 and 0.95")
            sys.exit(1)
        
        if args.nperseg <= 0:
            print("Error: nperseg must be positive")
            sys.exit(1)
        
        if args.sampling_rate <= 0:
            print("Error: Sampling rate must be positive")
            sys.exit(1)
        
        try:
            results = plot_raw_psd(
                raw_file_path=file_path,
                fs=args.sampling_rate,
                calib=args.calib,
                nperseg=args.nperseg,
                overlap=args.overlap,
                fmax=args.freq_max,
                output_dir=args.output_dir,
                title=args.title,
                skip_amplitude=not args.save_amplitude,
                skip_spectrogram=not args.save_spectrogram,
                skip_csv=not args.save_csv
            )
            
            print(f"\n✅ PSD analysis completed successfully!")
            print(f"📁 Output directory: {results['output_dir']}")
            print(f"📊 PSD plot: {results['psd_plot'].name}")
            if 'psd_csv' in results:
                print(f"📄 PSD data: {results['psd_csv'].name}")
            if args.save_amplitude and 'amplitude_plot' in results:
                print(f"📈 Amplitude plot: {results['amplitude_plot'].name}")
            if args.save_spectrogram and 'spectrogram_plot' in results:
                print(f"🎵 Spectrogram: {results['spectrogram_plot'].name}")
                
        except Exception as e:
            print(f"❌ Error during PSD analysis: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        # Default Timestamp Analysis Mode
        print("=" * 60)
        print("TIMESTAMP ANALYSIS MODE")
        print("=" * 60)
        
        # Read timestamps and samples from the file
        timestamps, samples = read_raw_file(file_path)
        
        if not timestamps:
            print("No timestamps found or error reading file")
            sys.exit(1)
        
        print(f"Samples array shape: {samples.shape}")
        if samples.size > 0:
            print(f"Sample data type: {samples.dtype}")
            print(f"Sample value range: [{samples.min()}, {samples.max()}]")
            print(f"Sample statistics - Mean: {samples.mean():.2f}, Std: {samples.std():.2f}")
            
            # Calculate RMS for raw samples
            flat_samples = samples.flatten()
            rms_raw_total = analyze_vibration.calculate_rms(flat_samples, detrend=False)
            rms_raw_ac = analyze_vibration.calculate_rms(flat_samples, detrend=True)
            print(f"Sample RMS (total): {rms_raw_total:.2f} counts")
            print(f"Sample RMS (AC only): {rms_raw_ac:.2f} counts")
        
        # Print timestamp summary
        print_timestamps_summary(timestamps)
        
        # Check for gaps
        check_timestamp_gaps(timestamps, expected_gap=args.gap)


if __name__ == "__main__":
    main()