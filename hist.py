import numpy as np

def find_histogram_signal_segment(bin_heights, max_gap=20):
    """
    Finds the start and end indices of the main signal segment in a histogram.

    Parameters:
    - bin_heights: array-like of histogram bin counts
    - max_gap: maximum allowed consecutive zero bins within a signal

    Returns:
    - start_idx, end_idx: indices marking the start and end of the signal segment
      Returns (-1, -1) if no signal is found
    """
    bin_heights = np.asarray(bin_heights)
    n = len(bin_heights)

    start_idx = -1
    end_idx = -1
    gap_count = 0
    in_signal = False

    for i in range(n):
        if bin_heights[i] > 0:
            if not in_signal:
                in_signal = True
                start_idx = i
            gap_count = 0
            end_idx = i
        elif in_signal:
            gap_count += 1
            if gap_count > max_gap:
                break  # too many zeros — end of signal

    if start_idx == -1:
        return -1, -1  # no signal found
    else:
        return start_idx, end_idx
