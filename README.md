# ICICI MTF Advisor

A small Python package that can run daily, fetch ICICI Direct Breeze positions/trades,
identify likely MTF positions, compute carry costs, and generate HOLD / SELL suggestions.

## What this package does
- Connects to ICICI Direct Breeze API
- Pulls portfolio positions and trade history
- Filters likely MTF positions
- Computes:
  - MTF interest cost
  - FD opportunity cost
  - inflation hurdle
- Emits a CSV and JSON report with a suggestion

## What this package does NOT do
- It does not guarantee a profitable signal.
- It does not include a true alpha model by default.
- It uses a configurable expected return assumption unless you replace it with your own signal.

## Install
```bash
pip install -r requirements.txt
```

## Configure
Copy and edit:
```bash
cp config/config.example.yaml config/config.yaml
```

Fill in your Breeze credentials.

## Run
```bash
python -m icici_mtf_advisor.jobs.daily_run --config config/config.yaml
```

## Notes
- `data/` owns API access only
- `domain/` owns normalization and MTF filtering
- `engine/` owns finance calculations and decisions
- `jobs/` orchestrates daily execution
