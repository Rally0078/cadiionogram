import numpy as np

def convert_amplitude_to_power(signal: np.ndarray[np.int8, np.int8]):
    sensors_abs = np.empty(shape=(signal.shape[0],signal.shape[1]//2))
    sensors_median = np.empty(shape=(sensors_abs.shape[0],))
    for idx in range(0, signal.shape[1]-1, 2):
        abs_squared = signal[:, idx].astype(np.int16)**2 + signal[:, idx+1].astype(np.int16)**2
        sensors_abs[:, idx//2] = np.sqrt(abs_squared)
    sensors_median = np.median(sensors_abs, axis=1)
    power_median = np.zeros_like(sensors_median)
    power_mask = sensors_median <= 0
    power_median[power_mask] = 0
    power_median[~power_mask] = 20 * np.log10(sensors_median[~power_mask])

    return power_median
