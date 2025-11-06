import os 

class FolderNotContainingData(Exception):
    def __init__(self, input_dir, message="Folder does not contain the required data files"):
        self.input_dir = input_dir
        self.message = message
        super().__init__(self.message)
    def __str__(self):
        return f"{self.message}. Provided input directory: {self.input_dir}"
    
class BadIndicesInData(ValueError):
    def __init__(self, metadata, iq, filename):
        self.timepartitions = list(metadata['timepartitions'].values())
        self.len_data = len(iq)
        self.filename = filename
    def __str__(self):
        return f"Timepartition indices({self.timepartitions[-1]}) do not match with length of raw data({self.len_data}) in file {self.filename}. Is the file corrupt?"