import os 

class FolderNotContainingData(Exception):
    def __init__(self, input_dir, message="Folder does not contain the required data files"):
      self.input_dir = input_dir
      self.message = message
      super().__init__(self.message)
    def __str__(self):
      return f"{self.message}. Provided input directory: {self.input_dir}"