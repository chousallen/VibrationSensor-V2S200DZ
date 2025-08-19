import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def read_csv_column(path, column=0, skiprows=0):
    # Robust reader using pandas, then convert to numpy array
    df = pd.read_csv(path, header=None, skiprows=skiprows)
    if isinstance(column, int):
        s = df.iloc[:, column]
    else:
        s = df[column]
    x = pd.to_numeric(s, errors='coerce').dropna().to_numpy(dtype=float)
    return x

def detrend_mean(x):
    return x - np.mean(x)

def welch_psd(x, fs, nperseg=4096, overlap=0.5, window='hann', detrend=True):
    """
    Compute Welch's averaged periodogram PSD estimate without SciPy.
    Returns freqs (Hz) and psd (units^2/Hz).
    """
    x = np.asarray(x, dtype=float)
    N = len(x)
    if nperseg > N:
        nperseg = N
    step = int(nperseg * (1.0 - overlap))
    if step <= 0:
        step = 1
    # Window
    if window == 'hann':
        w = np.hanning(nperseg)
    elif window == 'hamming':
        w = np.hamming(nperseg)
    else:
        w = np.ones(nperseg)
    U = (w**2).sum()  # window normalization factor

    segments = []
    for start in range(0, N - nperseg + 1, step):
        seg = x[start:start + nperseg].copy()
        if detrend:
            seg -= seg.mean()
        seg *= w
        X = np.fft.rfft(seg, n=nperseg)
        psd_seg = (np.abs(X)**2) / (fs * U)
        segments.append(psd_seg)

    if len(segments) == 0:
        # Fallback: zero-pad single segment
        seg = x.copy()
        if detrend:
            seg -= seg.mean()
        if len(seg) < nperseg:
            pad = np.zeros(nperseg - len(seg))
            seg = np.concatenate([seg, pad])
        seg *= w
        X = np.fft.rfft(seg, n=nperseg)
        psd = (np.abs(X)**2) / (fs * U)
    else:
        psd = np.mean(np.vstack(segments), axis=0)

    freqs = np.fft.rfftfreq(nperseg, d=1.0/fs)
    return freqs, psd

def amplitude_spectrum(x, fs, window='hann', detrend=True):
    """
    Single-sided amplitude spectrum (linear amplitude per bin, not density).
    Returns freqs (Hz) and amplitude (units).
    """
    x = np.asarray(x, dtype=float)
    N = len(x)
    if detrend:
        x = x - x.mean()
    if window == 'hann':
        w = np.hanning(N)
    elif window == 'hamming':
        w = np.hamming(N)
    else:
        w = np.ones(N)
    xw = x * w
    X = np.fft.rfft(xw)
    # Coherent gain of the window for amplitude correction
    cg = w.mean()
    # Single-sided amplitude (account for discarded negative freqs except DC/Nyquist)
    amp = (np.abs(X) / (N * cg))
    if N % 2 == 0:
        # even N includes Nyquist bin
        amp[1:-1] *= 2.0
    else:
        amp[1:] *= 2.0
    freqs = np.fft.rfftfreq(N, d=1.0/fs)
    return freqs, amp

def plot_psd(freqs, psd, outpath, fmax=None, title='Welch PSD'):
    plt.figure()
    if fmax is not None:
        mask = freqs <= fmax
        freqs_plot = freqs[mask]
        psd_plot = psd[mask]
    else:
        freqs_plot = freqs
        psd_plot = psd
    plt.semilogy(freqs_plot, psd_plot)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('PSD (units²/Hz)')
    plt.title(title)
    plt.grid(True, which='both', linestyle=':')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_amplitude(freqs, amp, outpath, fmax=None, title='Single-Sided Amplitude Spectrum'):
    plt.figure()
    if fmax is not None:
        mask = freqs <= fmax
        freqs_plot = freqs[mask]
        amp_plot = amp[mask]
    else:
        freqs_plot = freqs
        amp_plot = amp
    plt.plot(freqs_plot, amp_plot)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude (units)')
    plt.title(title)
    plt.grid(True, which='both', linestyle=':')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_spectrogram(x, fs, outpath, nperseg=1024, overlap=0.75, window='hann', detrend=True, fmax=None, vmax=None):
    x = np.asarray(x, dtype=float)
    if detrend:
        x = x - x.mean()
    if window == 'hann':
        w = np.hanning(nperseg)
    elif window == 'hamming':
        w = np.hamming(nperseg)
    else:
        w = np.ones(nperseg)
    step = int(nperseg * (1.0 - overlap))
    if step <= 0:
        step = 1

    segments = []
    for start in range(0, len(x) - nperseg + 1, step):
        seg = x[start:start + nperseg].copy()
        seg -= seg.mean()
        seg *= w
        X = np.fft.rfft(seg, n=nperseg)
        psd_seg = (np.abs(X)**2) / ((w**2).sum() * fs)  # units^2/Hz
        segments.append(psd_seg)

    Sxx = np.array(segments).T  # shape: [freqs, times]
    freqs = np.fft.rfftfreq(nperseg, d=1.0/fs)
    times = np.arange(Sxx.shape[1]) * (step / fs)

    if fmax is not None:
        fmask = freqs <= fmax
        freqs = freqs[fmask]
        Sxx = Sxx[fmask, :]

    # Convert to dB for display
    Sxx_dB = 10.0 * np.log10(np.maximum(Sxx, np.finfo(float).eps))

    plt.figure()
    extent = [times[0], times[-1], freqs[0], freqs[-1]] if times.size > 0 else [0, 0, freqs[0], freqs[-1]]
    aspect = 'auto'
    plt.imshow(Sxx_dB, origin='lower', extent=extent, aspect=aspect, vmin=None, vmax=vmax)
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Spectrogram (PSD, dB re units²/Hz)')
    plt.colorbar(label='dB')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def main():
    ap = argparse.ArgumentParser(description='Frequency-domain analysis of vibration CSV data (no SciPy).')
    ap.add_argument('--input', required=True, help='Path to CSV file with samples')
    ap.add_argument('--fs', type=float, required=True, help='Sampling rate in Hz (e.g., 12500)')
    ap.add_argument('--column', default=1, help='Column index or name to read (default: 0)')
    ap.add_argument('--skiprows', type=int, default=1, help='Number of header rows to skip (default: 0)')
    ap.add_argument('--calib', type=float, default=1.0, help='Calibration factor to scale raw counts to engineering units (e.g., g per count)')
    ap.add_argument('--nperseg', type=int, default=4096, help='Welch segment length (default: 4096)')
    ap.add_argument('--overlap', type=float, default=0.5, help='Welch overlap fraction 0..0.95 (default: 0.5)')
    ap.add_argument('--fmax', type=float, default=None, help='Max frequency to display (Hz)')
    ap.add_argument('--outdir', default='out', help='Output directory for plots and CSV')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load data
    x = read_csv_column(args.input, column=int(args.column) if str(args.column).isdigit() else args.column, skiprows=args.skiprows)
    x = x * args.calib  # apply calibration if provided

    # Welch PSD
    freqs_psd, psd = welch_psd(x, fs=args.fs, nperseg=args.nperseg, overlap=args.overlap, window='hann', detrend=True)
    psd_csv = os.path.join(args.outdir, 'psd_welch.csv')
    pd.DataFrame({'freq_hz': freqs_psd, 'psd_units2_per_hz': psd}).to_csv(psd_csv, index=False)
    psd_png = os.path.join(args.outdir, 'psd_welch.png')
    plot_psd(freqs_psd, psd, psd_png, fmax=args.fmax)

    # Amplitude spectrum
    freqs_amp, amp = amplitude_spectrum(x, fs=args.fs, window='hann', detrend=True)
    amp_png = os.path.join(args.outdir, 'amplitude_spectrum.png')
    plot_amplitude(freqs_amp, amp, amp_png, fmax=args.fmax)

    # Spectrogram
    spec_png = os.path.join(args.outdir, 'spectrogram.png')
    nperseg_spec = min(max(256, args.nperseg//4), len(x))
    plot_spectrogram(x, fs=args.fs, outpath=spec_png, nperseg=nperseg_spec, overlap=0.75, window='hann', detrend=True, fmax=args.fmax)

    # Quick summary
    dur = len(x) / args.fs
    print(f'Analyzed {len(x)} samples ({dur:.2f} s) @ {args.fs} Hz.')
    print(f'Outputs written to: {os.path.abspath(args.outdir)}')
    print(f'- PSD (CSV): {psd_csv}')
    print(f'- PSD plot: {psd_png}')
    print(f'- Amplitude spectrum plot: {amp_png}')
    print(f'- Spectrogram plot: {spec_png}')

if __name__ == "__main__":
    main()