# Test Data Files

This directory contains CSV files with fake/test data that were used during development.

**⚠️ WARNING: These files contain FAKE data only (all rows have `is_fake=True`).**

These files are **NOT** loaded by the runtime application. The application loads data from MDB files via the `load_data_from_mdb.py` management command.

## Files

- `candidates.csv` - Fake candidate data
- `donors.csv` - Fake donor/entity data  
- `expenditures.csv` - Fake expenditure data
- `contributions.csv` - Fake contribution data
- `iecommittees.csv` - Fake IE committee data
- `races.csv` - Fake race data
- `contactlogs.csv` - Fake contact log data
- `candidate.csv` - Alternative candidate data format

## Usage

These files are kept for reference only. If you need to load test data, use the Django management commands in `transparency/management/commands/` instead.

