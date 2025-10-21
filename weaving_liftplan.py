import pandas as pd
import argparse
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ============================================================
# 1️⃣ Load SECTIONS
# ============================================================

def load_sections(csv_path):
    """
    Expects a filepath to a CSV file describing the sections.
    
    The format of the CSV file should be (as an example):
        section_name,pick,treadles
        hem,1,1
        hem,2,2
        hem,3,3
        hem,4,4
        hem,5,5
        hem,6,6
        hem,7,7
        hem,8,8
        zinger,1,4
        zinger,2,3
        zinger,3,2
        zinger,4,1
        block,1,8
        block,2,7
        block,3,6
        block,4,5
        
    Returns:
        pd.DataFrame with columns 'section_name','pick','treadles'
    """
    df_raw = pd.read_csv(csv_path, dtype=str).fillna("")
    df_raw.columns = [c.strip().lower() for c in df_raw.columns]
    if "treadles" not in df_raw.columns:
        raise ValueError("Sections CSV must include a 'treadles' column")
    if "section_name" not in df_raw.columns:
        raise ValueError("Sections CSV must include a 'section_name' column")
    if "pick" not in df_raw.columns:
        raise ValueError("Sections CSV must include a 'pick' column")
    return df_raw


# ============================================================
# 1️⃣ Load TREADLING (supports nested sections, repeats, reverse)
# ============================================================

def load_treadling(sections_df, sequence_csv_path):
    """
    Build a flat treadling DataFrame from sections + sequence with repeats.

    Args:
        sections_df (pd.DataFrame): Output of load_sections().
            Columns: 'section_name', 'pick', 'treadles'
        sequence_csv_path (str): Path to CSV describing the sequence of sections.
            CSV format:
                pick,section_name
                1,A x4
                2,B
                3,C

    Returns:
        pd.DataFrame: Columns ['pick','treadles','section_label']
            - pick = 1..N
            - treadles = string of space-separated treadles
            - section_label = name of the section
    """
    sequence_df = pd.read_csv(sequence_csv_path, dtype=str).fillna("")
    sequence_df.columns = [c.strip().lower() for c in sequence_df.columns]
    if "section_name" not in sequence_df.columns:
        raise ValueError("Sequence CSV must include a 'section_name' column")
    
    expanded_rows = []

    for _, row in sequence_df.iterrows():
        seq_name = row["section_name"].strip()
        # Match optional repeats: e.g., "hem x4"
        m = re.match(r"^(.+?)(?:\s+x(\d+))?$", seq_name, re.I)
        if not m:
            raise ValueError(f"Invalid section_name format: '{seq_name}'")
        name = m.group(1).strip()
        repeat = int(m.group(2)) if m.group(2) else 1

        # Select rows from sections_df corresponding to this section
        section_rows = sections_df[sections_df["section_name"].str.lower() == name.lower()]
        if section_rows.empty:
            raise ValueError(f"Section '{name}' not found in sections DataFrame")

        # Repeat the section
        for _ in range(repeat):
            for _, sec_row in section_rows.iterrows():
                expanded_rows.append({
                    "treadles": str(sec_row["treadles"]).strip(),
                    "section_label": sec_row["section_name"]
                })

    # Build final flat DataFrame with picks numbered 1..N
    flat_df = pd.DataFrame(expanded_rows)
    flat_df["pick"] = range(1, len(flat_df) + 1)
    flat_df = flat_df[["pick","treadles","section_label"]]
    return flat_df


# ============================================================
# 2️⃣ Load TIE-UP
# ============================================================

def load_tieup(csv_path):
    """
    Load a tie-up CSV into a DataFrame.

    Example CSV:
        treadle,shafts
        1,"1 2"
        2,"3 4"
        3,"2 3"
        4,"1 4"

    Returns:
        pd.DataFrame with columns ['treadle', 'shafts']
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "treadle" not in df.columns or "shafts" not in df.columns:
        raise ValueError("Tie-up CSV must have columns 'treadle' and 'shafts'")

    df["treadle"] = df["treadle"].apply(lambda x: int(float(x)))
    df["shafts"] = df["shafts"].astype(str).str.strip()
    return df


# ============================================================
# 3️⃣ Generate Lift Plan
# ============================================================
def generate_lift_plan(treadling_df, tieup_df, num_shafts):
    """
    Generate a lift plan DataFrame mapping picks × shafts.

    Returns:
        pd.DataFrame of shape (num_picks, num_shafts)
        with True where shaft is lifted.
    """
    # Build tie-up mapping
    tieup_map = {
        int(row.treadle): [int(s) for s in str(row.shafts).split()]
        for _, row in tieup_df.iterrows()
    }

    lift_plan_data = []
    for _, row in treadling_df.iterrows():
        treadle_str = row.treadles.strip()
        treadle_nums = []
        if treadle_str:
            for t in treadle_str.split():
                try:
                    treadle_nums.append(int(float(t)))
                except ValueError:
                    # Skip non-numeric entries gracefully
                    continue

        shafts_lifted = set()
        for t in treadle_nums:
            shafts_lifted.update(tieup_map.get(t, []))
        lift_plan_data.append([s in shafts_lifted for s in range(1, num_shafts + 1)])

    lift_plan_df = pd.DataFrame(lift_plan_data, columns=[f"Shaft {i}" for i in range(1, num_shafts + 1)])
    lift_plan_df["pick"] = range(1, len(lift_plan_df) + 1)
    lift_plan_df["section_label"] = treadling_df["section_label"]
    return lift_plan_df


# ============================================================
# 4️⃣ Draw PDF Liftplan (with section labels)
# ============================================================

def draw_liftplan_pdf(lift_plan_df, pdf_path, cell_size=15):
    """
    Draw a liftplan grid where only lifted shafts have their numbers shown.
    Sections are labeled on the right.
    """
    num_picks = len(lift_plan_df)
    num_shafts = len([c for c in lift_plan_df.columns if c.startswith("Shaft")])

    width = num_shafts * cell_size + 120
    height = num_picks * cell_size + 150
    c = canvas.Canvas(pdf_path, pagesize=(width, height))

    x_origin = 50
    y_origin = height - 100  # Top margin
    c.setFont("Helvetica", 8)

    current_section = None

    for i, row in lift_plan_df.iterrows():
        pick_y = y_origin - i * cell_size

        section_name = row["section_label"]

        # Draw lift cells
        for j in range(num_shafts):
            x = x_origin + j * cell_size
            c.rect(x, pick_y - cell_size, cell_size, cell_size, fill=0)
            if row[f"Shaft {j+1}"]:
                c.drawCentredString(x + cell_size / 2, pick_y - cell_size / 2 - 3, str(j + 1))
        
        # Draw section label once per section change
        if section_name != current_section:
            current_section = section_name
            c.drawString(x_origin + num_shafts * cell_size + 10,
                         pick_y - cell_size / 2 - 3, str(current_section))

    # Compute section boundaries
    section_bounds = lift_plan_df.groupby("section_label").agg(first_pick=("pick","first"),
                                                          last_pick=("pick","last")).reset_index()

    # Draw thick horizontal lines for section boundaries
    line_thickness = 2
    c.setLineWidth(line_thickness)
    for _, sec in section_bounds.iterrows():
        # Top of the first pick
        top_y = y_origin - (sec.first_pick - 1) * cell_size
        c.line(x_origin, top_y, x_origin + num_shafts * cell_size, top_y)
        # Bottom of the last pick
        bottom_y = y_origin - sec.last_pick * cell_size
        c.line(x_origin, bottom_y, x_origin + num_shafts * cell_size, bottom_y)


    # Draw axes labels
    c.setFont("Helvetica-Bold", 10)
    for j in range(num_shafts):
        x = x_origin + j * cell_size + cell_size / 2
        c.drawCentredString(x, y_origin + 10, str(j + 1))

    c.drawString(x_origin - 40, y_origin + 10, "Shafts →")
    c.drawString(50, 20, "Pick 1 starts at top")

    c.save()
    print(f"✅ Liftplan PDF saved to {pdf_path}")


# ============================================================
# 5️⃣ Example Main Entry
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate annotated lift plan PDF from nested treadling CSV.")
    parser.add_argument("sections", help="Path to CSV describing sections")
    parser.add_argument("treadling", help="Path to treadling CSV file of section repeats")
    parser.add_argument("tieup", help="Path to tie-up CSV file")
    parser.add_argument("--shafts", type=int, default=8)
    parser.add_argument("--output", default="lift_plan_annotated.pdf")
    args = parser.parse_args()
    
    sections_df = load_sections(args.sections)
    treadling_df = load_treadling(sections_df, args.treadling)
    tieup_df = load_tieup(args.tieup)
    lift_plan_df = generate_lift_plan(treadling_df, tieup_df, num_shafts=args.shafts)
    draw_liftplan_pdf(lift_plan_df, args.output)
