import argparse
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# -------------------------------
# Load tie-up (same as before)
# -------------------------------
def load_tieup(file_path: str):
    df = pd.read_csv(file_path)
    tieup = {}
    for _, row in df.iterrows():
        t = int(row["treadle"])
        shafts = [int(s) for s in str(row["shafts"]).split()]
        tieup[t] = shafts
    return tieup


# -------------------------------
# Load nested treadling sections
# -------------------------------
def load_sectioned_treadling(file_path: str):
    df = pd.read_csv(file_path)
    sections = {}
    main_sequence = []

    for _, row in df.iterrows():
        row_type = str(row["type"]).strip().lower()
        if row_type == "section":
            name = str(row["name"]).strip()
            if not name:
                raise ValueError("Section row missing a name.")
            if name not in sections:
                sections[name] = []
            treadles_str = str(row["treadles"]).strip()
            ref_name = str(row.get("ref_name", "")) if "ref_name" in df.columns else None
            repeat = int(row["repeat"]) if not pd.isna(row["repeat"]) else 1

            if treadles_str and treadles_str.lower() != "nan":
                treadles = [int(t) for t in treadles_str.split()]
                sections[name].append({"type": "pick", "treadles": treadles})
            elif ref_name and ref_name.strip():
                sections[name].append({"type": "ref", "name": ref_name.strip(), "repeat": repeat})
        elif row_type == "main":
            ref_name = str(row["name"]).strip()
            repeat = int(row["repeat"]) if not pd.isna(row["repeat"]) else 1
            main_sequence.append((ref_name, repeat))
        else:
            raise ValueError(f"Unknown row type: {row_type}")

    # Recursive expansion with annotations
    def expand_section(name, depth=0, visited=None):
        if visited is None:
            visited = set()
        if depth > 20:
            raise RecursionError("Too many nested section references.")
        if name not in sections:
            raise ValueError(f"Undefined section name: {name}")
        if name in visited:
            raise RecursionError(f"Circular reference detected: {name}")

        visited.add(name)
        expanded = []
        for entry in sections[name]:
            if entry["type"] == "pick":
                expanded.append({"shafts": entry["treadles"], "label": None})
            elif entry["type"] == "ref":
                for i in range(entry.get("repeat", 1)):
                    expanded.append({"shafts": None, "label": f"Begin section {entry['name']} (repeat {i+1})"})
                    expanded.extend(expand_section(entry["name"], depth + 1, visited.copy()))
                    expanded.append({"shafts": None, "label": f"End section {entry['name']}"})
        return expanded

    expanded = []
    for ref_name, repeat in main_sequence:
        for i in range(repeat):
            expanded.append({"shafts": None, "label": f"Begin section {ref_name} (repeat {i+1})"})
            expanded.extend(expand_section(ref_name))
            expanded.append({"shafts": None, "label": f"End section {ref_name}"})
    return expanded


# -------------------------------
# Auto-detect treadling file format
# -------------------------------
def load_treadling(file_path: str):
    df = pd.read_csv(file_path)
    if "type" in df.columns:
        return load_sectioned_treadling(file_path)
    else:
        # Flat fallback
        df = pd.read_csv(file_path)
        return [{"shafts": [int(t) for t in str(row["treadles"]).split()], "label": None} for _, row in df.iterrows()]


# -------------------------------
# Generate lift plan
# -------------------------------
def generate_lift_plan(treadling, tieup):
    lift_plan = []
    for entry in treadling:
        if entry["shafts"] is None:
            # Annotation row
            lift_plan.append({"shafts": None, "label": entry["label"]})
        else:
            shafts = set()
            for t in entry["shafts"]:
                shafts.update(tieup.get(t, []))
            lift_plan.append({"shafts": sorted(shafts), "label": entry["label"]})
    return lift_plan


# -------------------------------
# Draw annotated PDF
# -------------------------------
def draw_lift_plan_pdf(lift_plan, num_shafts, output_file):
    data = []
    row_styles = []

    for idx, entry in enumerate(lift_plan):
        if entry["shafts"] is None and entry["label"]:
            # Label row
            data.insert(0, [entry["label"]] + [""] * (num_shafts - 1))
            row_styles.append(("SPAN", (0, len(data) - 1), (-1, len(data) - 1)))
            row_styles.append(("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.lightgrey))
            row_styles.append(("ALIGN", (0, len(data) - 1), (-1, len(data) - 1), "CENTER"))
        else:
            row = ["■" if (s + 1) in entry["shafts"] else "" for s in range(num_shafts)]
            data.insert(0, row)  # pick 1 at top

    # PDF layout
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    table = Table(data, colWidths=25, rowHeights=18)

    style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]
        + row_styles
    )

    table.setStyle(style)
    doc.build([table])
    print(f"✅ Annotated lift plan PDF written to: {output_file}")


# -------------------------------
# Main
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate annotated lift plan PDF from nested treadling CSV.")
    parser.add_argument("treadling", help="Path to treadling CSV file")
    parser.add_argument("tieup", help="Path to tie-up CSV file")
    parser.add_argument("--shafts", type=int, default=8)
    parser.add_argument("--output", default="lift_plan_annotated.pdf")
    args = parser.parse_args()

    treadling = load_treadling(args.treadling)
    tieup = load_tieup(args.tieup)
    lift_plan = generate_lift_plan(treadling, tieup)
    draw_lift_plan_pdf(lift_plan, args.shafts, args.output)


if __name__ == "__main__":
    main()
