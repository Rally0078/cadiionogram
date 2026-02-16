#State class to determine the correct lines and scaled values for each region

class ScaleRegionValues:
    def __init__(self, ax):
        self._state = {
            'F': {'h': float('nan'), 'f': float('nan'), 'hline': None, 'fline': None}, 
            'E': {'h': float('nan'), 'f': float('nan'), 'hline': None, 'fline': None}, 
            'IE': {'h': float('nan'), 'f': float('nan'), 'hline': None, 'fline': None}
        }
        self._colors = {
            'F': {'h': 'red', 'f': 'blue'},
            'E': {'h': 'green', 'f': 'yellow'},
            'IE': {'h': 'black', 'f': 'pink'}
        }
        self._current_region = None
        self._ax = ax
    @property
    def h(self):
        if self._current_region is None:
            return None
        return self._state[self._current_region]['h']
    @h.setter
    def h(self, h_val):
        if self._current_region is None:
            raise ValueError("Region not set. Set current region first")
        s = self._state[self._current_region]
        hline = s['hline']
        if hline is not None and hline in self._ax.lines:
            hline.remove()
        s['hline'] = self._ax.axhline(h_val, color=self._colors[self._current_region]['h'], linewidth=2, linestyle='--', label=fr"$h'{self._current_region}$ = {h_val:.2f} km")
        s['h'] = h_val
            
    @property
    def f(self):
        if self._current_region is None:
            return None
        return self._state[self._current_region]['f']
    @f.setter
    def f(self, f_val):
        if self._current_region is None:
            raise ValueError("Region not set. Set current region first")
        s = self._state[self._current_region]
        fline = s['fline']
        if fline is not None and fline in self._ax.lines:
            fline.remove()
        s['fline'] = self._ax.axvline(f_val, color=self._colors[self._current_region]['f'], linewidth=2, linestyle='--', label=fr"$f_o{self._current_region}$ = {f_val:.2f} MHz")
        s['f'] = f_val

    def _check_region(self):
        if self._current_region is None:
            raise Exception("Scale region not set!")
    def set_region(self, region):
        if region not in ['E', 'F', 'IE']:
            raise KeyError("Not a valid region!")
        self._current_region = region

    def clear_all(self):
        for s in self._state.values():
            if s['hline'] is not None and s['hline'] in self._ax.lines:
                s['hline'].remove()
            s['hline'] = None
            s['h'] = float('nan')
            if s['fline'] is not None and s['fline'] in self._ax.lines:
                s['fline'].remove()
            s['fline'] = None
            s['f'] = float('nan')