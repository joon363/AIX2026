Grid Search for Calibration

Usage:

1. (Optional) Dry run to see commands without executing:

   python3 tools/grid_search.py --dry-run

2. Full run (will rebuild and execute tests; may take long):

   python3 tools/grid_search.py

The script now tries two calibration methods:

- **percentile**: dynamic histogram & percentile threshold (default).
- **minmax**: simple min/max scaling without histogram computation.

In the log and best_params.txt the chosen method is included alongside other parameters.

Results:
- tools/best_params.txt — best found combination (overwritten as improvements found)
- tools/grid_search_log.txt — appended log of all runs

Notes:
- The script overwrites `src/calib_config.h` for each run.
- Ensure the environment has the required build tools and that `bin/*.sh` scripts are executable.
