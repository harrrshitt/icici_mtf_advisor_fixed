from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

from icici_mtf_advisor.data.breeze_client import BreezeClient
from icici_mtf_advisor.domain.filters import is_mtf_position
from icici_mtf_advisor.domain.normalizer import normalize_position
from icici_mtf_advisor.engine.decision import evaluate_position


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_data(cfg: Dict):
    breeze_cfg = cfg["breeze"]
    lookback_days = int(cfg.get("runtime", {}).get("trade_lookback_days", 365))

    client = BreezeClient(
        api_key=breeze_cfg["api_key"],
        api_secret=breeze_cfg["api_secret"],
        session_token=breeze_cfg["session_token"],
    )

    positions = client.get_positions()

    today = date.today()
    from_date = (today - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    trades = client.get_trades(from_date=from_date, to_date=to_date)

    return positions, trades


def build_report_rows(positions: List[Dict], trades: List[Dict], cfg: Dict) -> List[Dict]:
    finance_cfg = cfg["finance"]
    decision_cfg = cfg["decision"]

    mtf_positions = [p for p in positions if is_mtf_position(p)]
    rows = []

    for raw_position in mtf_positions:
        normalized = normalize_position(raw_position, trades)
        row = evaluate_position(
            position=normalized,
            finance_cfg=finance_cfg,
            decision_cfg=decision_cfg,
        )
        rows.append(row)

    return rows


def save_reports(rows: List[Dict], output_dir: str) -> Dict[str, str]:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / f"mtf_advice_{ts}.csv"
    json_path = output_path / f"mtf_advice_{ts}.json"

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, default=str)

    return {"csv": str(csv_path), "json": str(json_path)}


def main():
    parser = argparse.ArgumentParser(description="Run ICICI MTF daily advisor")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    args = parser.parse_args()

    cfg = load_config(args.config)
    positions, trades = fetch_data(cfg)
    rows = build_report_rows(positions, trades, cfg)

    output_dir = cfg.get("reporting", {}).get("output_dir", "outputs")
    paths = save_reports(rows, output_dir=output_dir)

    print(json.dumps({
        "positions_fetched": len(positions),
        "rows_in_report": len(rows),
        "outputs": paths,
    }, indent=2))


if __name__ == "__main__":
    main()
