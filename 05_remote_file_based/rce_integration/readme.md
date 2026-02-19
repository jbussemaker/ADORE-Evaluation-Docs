# RCE Integration

RCE integration for ADORE installed locally as a Python package, or executed directly from the source code.
Make sure that SBArchOpt has also been installed: `pip install .[opt]`

1. Create a new folder in `C:\Users\<username>\.rce\default\integration\tools\common` called
   `AdoreOpt`
2. If you are running ADORE as a **PYTHON PACKAGE** installed in a Python environment (i.e. after `pip install ...`):
   1. Place files in the new directory: `configuration_python_install.json` and the logo
   2. Rename the json to `configuration.json` and edit it:
      1. Change conda environment name in `commandScriptWindows` to the environment 
         where *ADORE* and *SBArchOpt* have been installed
      2. Change `toolDirectory` in `launchSettings` to the folder containing the `adore`
         package.
         1. To find the path, start Python in you conda environment (`python`) and enter the following command:
            `import adore,pathlib; print(repr(str(pathlib.Path(adore.__file__).parent.parent)).replace("'", '"'))`
         2. Then copy the path including the quotes (") and double backslashes (\\)
   
3. If you are running ADORE directly **FROM THE SOURCE CODE**:
   1. Place files in the new directory: `configuration_source_code.json` and the logo
   2. Rename the json to `configuration.json` and edit it:
      1. Change conda environment name in `commandScriptWindows` to the environment 
         where *ADORE* and *SBArchOpt* have been installed 
      2. Change `toolDirectory` in `launchSettings` to the folder containing the `adore`
         package (as cloned from git)

## Usage

1. Integrate *AdoreOpt* tool in RCE (see above)
2. Refer to "Introduction to ADORE Evaluation Interfaces" (see docs) for how to setup and run RFSAO (Remote File-based
   System Architecture Optimization) problems

After running the workflow, the final `*.adoreopt` file can be obtained from the last run of *AdoreOpt*.
This file can then be opened in the ADORE GUI to inspect the architectures and export results to CSV.

Optimization state is stored: when creating a new `*.adoreopt` file after opening in the GUI, the new file continuous
from the same state as the previously opened file.
