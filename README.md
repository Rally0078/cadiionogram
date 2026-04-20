# CADI Ionogram Plotting Software

Primarily developed to process and plot CADI raw data in various forms. Written in Python using Qt6. 

## Installation

For using the CADI-related libraries, install the conda environment and activate it the following way:

```bash
    conda env create -f environment.yml
    conda activate cadiionogram
```

Then import the libraries in Python to use them:

```py
    #Add these lines to your Python code that requires the CADI library
    import sys
    from pathlib import Path
    #The following two lines are for importing modules from a different folder
    import_path = Path("path/to/the/repo")
    sys.path.append(str(import_path))
```

To build the faster, Rust-based CADI reader(requires an installation of Rust), use

```bash
    conda activate cadiionogram
    cargo build --manifest-path "./rust/Cargo.toml" --release --lib
    # Windows only
    cp "./rust/target/release/mdreader_rs.dll" "./src/ionogramparser/mdreader_rs.pyd"
    # Linux only
    cp "./rust/target/release/libmdreader_rs.so" "./src/ionogramparser/mdreader_rs.so"
```

For manually building the GUI executable, run the following:

```bash
    conda env create -f environment-build.yml
    conda activate cadiionogram-release
    pytest -v
    python -m PyInstaller main.spec
```

The GH Actions should do all these automatically and create a release for each push into the main branch.

When running the GUI executable for the first time, it creates a config.ini file. The config.ini file consists of the directories used by the GUI to save processed data, as well as the default location of the raw data. Edit the configuration so that the program uses the correct directories.

## Running as a python script

To run as a python script, run the following. Run it the same way to debug the GUI.

```
    python -m src.plot.main.py
```
