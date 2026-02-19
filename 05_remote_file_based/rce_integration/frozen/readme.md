# RCE Integration

RCE integration for ADORE running as a frozen deployment.

1. Create a new folder in `C:\Users\<username>\.rce\default\integration\tools\common` called
   `AdoreOpt`
2. Place files in the new directory: `configuration.json` and the logo
3. Edit the configuration file:
   1. Change `toolDirectory` in `launchSettings` to the folder containing the `adore_opt_cli` executable.

## Usage

1. Integrate *AdoreOpt* tool in RCE (see above)
2. Refer to "Introduction to ADORE Evaluation Interfaces" (see docs) for how to setup and run RFSAO (Remote File-based
   System Architecture Optimization) problems

After running the workflow, the final `*.adoreopt` file can be obtained from the last run of *AdoreOpt*.
This file can then be opened in the ADORE GUI to inspect the architectures and export results to CSV.

Optimization state is stored: when creating a new `*.adoreopt` file after opening in the GUI, the new file continuous
from the same state as the previously opened file.
