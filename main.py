import json
import argparse
import pandas as pd
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a lift plan for a table loom from a treadling sequence and tie-up mapping written for a floor loom."
    )
    parser.add_argument("--treadling", required=True, help="Path to treadling sequence CSV")
    parser.add_argument("--tieup", required=True, help="Path to tie-up JSON file.")
    parser.add_argument("--output", required=True, help="Path to output lift plan CSV file.")
    return parser.parse_args()

def load_treadling_file(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    if "treadles" not in df.columns:
        raise ValueError("Treadling CSV must have a 'treadles' column.")
    return df

def load_tieup(file_path: str) -> dict:
    with open(file_path, "r") as f:
        tieup = json.load(f)
    return {int(k): v for k,v in tieup.items()}

def generate_lift_plan(treadling_df: pd.DataFrame, tieup: dict) -> pd.DataFrame:
    lift_plan = []
    for _, row in treadling_df.iterrows():
        treadles_str = str(row["treadles"]).strip()
        if not treadles_str:
            lift_plan.append([])
            continue
        treadles = [int(t) for t in treadles_str.split()]
        shafts = set()
        for t in treadles:
            shafts.update(tieup.get(t, []))
        lift_plan.append(sorted(shafts))
        
    lift_df = pd.DataFrame({
        "pick": range(1, len(lift_plan) + 1),
        "shafts": [" ".join(map(str, s)) for s in lift_plan]
    })
    return lift_df

def main():
    args = parse_args()
    treadling_df = load_treadling_file(args.treadling)
    tieup = load_tieup(args.tieup)
    lift_df = generate_lift_plan(treadling_df, tieup)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    lift_df.to_csv(args.output, index=False)
    print(f"✅ Lift plan saved to {args.output}")
    
if __name__ == "__main__":
    main()