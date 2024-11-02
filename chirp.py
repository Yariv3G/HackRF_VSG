import numpy as np


def generate_chirp_bin(filename, sample_rate=10e6, f_min=-10e6, f_max=10e6, dwell_time=1e-3, bit_depth=8):
    """
    Generate a frequency chirp in a triangle pattern and save it as a .bin file in 8-bit or 16-bit IQ format.

    Args:
    - filename: Output .bin file path
    - sample_rate: Sample rate in Hz
    - f_min: Minimum frequency offset from center (negative for downward shift)
    - f_max: Maximum frequency offset from center
    - dwell_time: Time to dwell at each frequency step (in seconds)
    - bit_depth: Bit depth for IQ data (8 or 16)
    """
    # Validate bit depth
    if bit_depth not in [8, 16]:
        raise ValueError("bit_depth must be 8 or 16")

    # Number of samples per frequency step
    samples_per_step = int(dwell_time * sample_rate)

    # Create the triangle frequency pattern
    frequency_steps = np.linspace(f_min, f_max, int(20e6 / samples_per_step))
    frequency_pattern = np.concatenate([frequency_steps, frequency_steps[::-1]])

    # Initialize signal array with preallocated size
    signal = np.zeros(samples_per_step * len(frequency_pattern), dtype=np.complex64)

    # Generate the waveform for each frequency step
    for i, f in enumerate(frequency_pattern):
        t = np.arange(samples_per_step) / sample_rate
        phase = 2 * np.pi * f * t
        signal[i * samples_per_step: (i + 1) * samples_per_step] = np.exp(1j * phase)

    # Convert to IQ format
    if bit_depth == 8:
        # Scale to 8-bit signed integers
        iq_data = np.stack((signal.real, signal.imag), axis=1).flatten()
        iq_data = np.clip(iq_data * 127, -128, 127).astype(np.int8)
    elif bit_depth == 16:
        # Scale to 16-bit signed integers
        iq_data = np.stack((signal.real, signal.imag), axis=1).flatten()
        iq_data = np.clip(iq_data * 32767, -32768, 32767).astype(np.int16)

    # Save to binary file
    with open(filename, "wb") as f:
        iq_data.tofile(f)

    print(f"Chirp signal saved to {filename} in {bit_depth}-bit IQ format")


# Example usage
generate_chirp_bin(r"C:\Users\Lab\PycharmProjects\HackRFVSG\triangle_chirp.bin", bit_depth=8, dwell_time=10e-3)  # For 8-bit IQ
