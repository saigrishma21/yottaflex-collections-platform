"""Data Exporter: Exports synthetic datasets to CSV, SQL seed script, JSON, and source manifest.
"""

import os
import csv
import json
import hashlib
from datetime import datetime, date, timezone
from decimal import Decimal
from backend.app.database import engine, Base, SessionLocal


def serialize_val(val):
    """Serialize values for CSV and JSON representation."""
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, bool):
        return "1" if val else "0"
    if val is None:
        return ""
    return str(val)


def export_all(data_dict, ground_truth, output_dir: str, seed: int, scale: str, populate_db: bool = True):
    """Export all generated tables to CSVs, SQL, JSON, and source manifest."""
    os.makedirs(os.path.join(output_dir, "generated"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "exports"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "ground_truth"), exist_ok=True)

    csv_dir = os.path.join(output_dir, "generated")
    exports_dir = os.path.join(output_dir, "exports")
    gt_dir = os.path.join(output_dir, "ground_truth")

    file_checksums = {}
    table_counts = {}

    # 1. EXPORT INDIVIDUAL CSVs
    print("Exporting CSV files...")
    for table_name, records in data_dict.items():
        if not records:
            continue
        csv_path = os.path.join(csv_dir, f"{table_name}.csv")
        sample = records[0]
        # Extract column names from SQLAlchemy model columns
        columns = [c.name for c in sample.__table__.columns]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for rec in records:
                row = [serialize_val(getattr(rec, col)) for col in columns]
                writer.writerow(row)

        table_counts[table_name] = len(records)
        # Compute SHA-256 for reproducibility check
        with open(csv_path, "rb") as f:
            file_checksums[f"{table_name}.csv"] = hashlib.sha256(f.read()).hexdigest()

    # 2. POPULATE SQLITE DATABASE (Only for primary dataset destination)
    if populate_db and output_dir == "data":
        print("Writing records to SQLite database (hackathon.db)...")
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        try:
            # Clear existing rows in reverse dependency order
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()

            # Insert new rows in forward dependency order
            for table_name in [
                "customers",
                "accounts",
                "loans",
                "contact_preferences",
                "installments",
                "payments",
                "payment_allocations",
                "delinquency_snapshots",
                "collection_cases",
                "contact_attempts",
                "promises_to_pay",
                "case_events",
            ]:
                records = data_dict.get(table_name, [])
                if records:
                    session.bulk_save_objects(records)
                    session.commit()
            print("Database population complete.")
        finally:
            session.close()

    # 3. EXPORT SEED_DATA.SQL
    print("Generating seed_data.sql...")
    sql_path = os.path.join(exports_dir, "seed_data.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- YottaFlex Hackathon Seed Data Script\n")
        f.write(f"-- Generated on: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"-- Random Seed: {seed} | Scale: {scale}\n\n")

        for table_name, records in data_dict.items():
            if not records:
                continue
            sample = records[0]
            columns = [c.name for c in sample.__table__.columns]
            cols_str = ", ".join(columns)

            for rec in records:
                val_strs = []
                for col in columns:
                    v = getattr(rec, col)
                    if v is None:
                        val_strs.append("NULL")
                    elif isinstance(v, (int, float, Decimal)):
                        val_strs.append(str(v))
                    elif isinstance(v, bool):
                        val_strs.append("1" if v else "0")
                    else:
                        escaped = str(serialize_val(v)).replace("'", "''")
                        val_strs.append(f"'{escaped}'")
                f.write(f"INSERT INTO {table_name} ({cols_str}) VALUES ({', '.join(val_strs)});\n")

    with open(sql_path, "rb") as f:
        file_checksums["seed_data.sql"] = hashlib.sha256(f.read()).hexdigest()

    # 4. EXPORT DATASET.JSON
    print("Generating dataset.json...")
    json_path = os.path.join(exports_dir, "dataset.json")
    dataset_dict = {}
    for table_name, records in data_dict.items():
        table_rows = []
        if records:
            columns = [c.name for c in records[0].__table__.columns]
            for rec in records:
                table_rows.append({col: serialize_val(getattr(rec, col)) for col in columns})
        dataset_dict[table_name] = table_rows

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset_dict, f, indent=2)

    with open(json_path, "rb") as f:
        file_checksums["dataset.json"] = hashlib.sha256(f.read()).hexdigest()

    # 5. EXPORT SOURCE MANIFEST
    print("Generating source_manifest.json...")
    manifest_path = os.path.join(exports_dir, "source_manifest.json")
    manifest = {
        "dataset_name": "YottaFlex Loan Delinquency & Collections Dataset",
        "version": "1.0.0",
        "generator_version": "1.0.0",
        "random_seed": seed,
        "scale": scale,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "Synthetic (Parametric Amortization & Behavior Simulation)",
        "external_data_sources": "None (Fully lawful, self-contained synthetic data)",
        "entity_counts": table_counts,
        "ground_truth_anomalies_count": len(ground_truth),
        "checksums_sha256": file_checksums,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Export summary successfully written to {manifest_path}")
    return manifest

