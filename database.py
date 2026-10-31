
import sqlite3
from datetime import date, timedelta

DATABASE = "plantcare.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            maintenance_type TEXT NOT NULL,
            maintenance_interval REAL NOT NULL,
            last_maintenance_date TEXT,
            next_maintenance_date TEXT,
            current_usage REAL DEFAULT 0,
            usage_threshold REAL DEFAULT 0,
            last_calibration_date TEXT,
            calibration_expiry_date TEXT,
            requires_calibration INTEGER DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            maintenance_date TEXT NOT NULL,
            description TEXT NOT NULL,
            usage_at_service REAL,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        );

        CREATE TABLE IF NOT EXISTS spare_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            equipment_code TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            minimum_stock INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS downtime_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            breakdown_date TEXT NOT NULL,
            problem TEXT NOT NULL,
            downtime_minutes INTEGER NOT NULL,
            corrective_action TEXT,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        );
    """)

    count = cursor.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]

    if count == 0:
        today = date(2026, 10, 31)

        equipment = [
            ("EQ001", "Moulding Machine 1", "Machine",
             "TIME", 30, 20, 30, 0, None, None, 0,
             "Routine moulding machine inspection"),

            ("EQ002", "Moulding Machine 2", "Machine",
             "USAGE", 500, 25, 0, 420, None, None, 0,
             "Service after operating hours threshold"),

            ("EQ003", "Steam Steriliser 1", "Machine",
             "TIME", 30, 25, 30, 0, None, None, 0,
             "Inspect heating and pressure systems"),

            ("EQ004", "Steam Steriliser 2", "Machine",
             "USAGE", 500, 10, 0, 350, None, None, 0,
             "Service after operating cycles"),

            ("EQ005", "Filling Machine 1", "Machine",
             "TIME", 30, 35, 30, 0, None, None, 0,
             "Inspect filling nozzles and seals"),

            ("EQ006", "Filling Machine 2", "Machine",
             "USAGE", 250, 12, 0, 220, None, None, 0,
             "Check operating hours and moving parts"),

            ("EQ007", "Weighing Balance 1", "Instrument",
             "TIME", 90, 20, 90, 0,
             "2025-10-31", "2026-10-31", 1,
             "Calibration expires on the test date"),

            ("EQ008", "Weighing Balance 2", "Instrument",
             "TIME", 90, 15, 90, 0,
             "2026-05-20", "2026-11-20", 1,
             "Calibration currently valid on test date")
        ]

        for item in equipment:
            (code, name, category, maintenance_type, interval,
             days_ago, next_days, usage, last_cal, expiry,
             requires_cal, notes) = item

            last_date = today - timedelta(days=days_ago)
            next_date = last_date + timedelta(days=next_days)

            cursor.execute("""
                INSERT INTO equipment (
                    equipment_code, name, category,
                    maintenance_type, maintenance_interval,
                    last_maintenance_date, next_maintenance_date,
                    current_usage, usage_threshold,
                    last_calibration_date, calibration_expiry_date,
                    requires_calibration, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, name, category, maintenance_type, interval,
                last_date.isoformat(), next_date.isoformat(),
                usage, interval if maintenance_type == "USAGE" else 0,
                last_cal, expiry, requires_cal, notes
            ))

        spare_parts = [
            ("SP001", "Heating Element", "EQ003", 4, 2),
            ("SP002", "Filling Nozzle", "EQ005", 6, 3),
            ("SP003", "Drive Belt", "EQ001", 0, 2),
            ("SP004", "Load Cell", "EQ007", 1, 2)
        ]

        cursor.executemany("""
            INSERT INTO spare_parts (
                part_code, name, equipment_code, quantity, minimum_stock
            ) VALUES (?, ?, ?, ?, ?)
        """, spare_parts)

        equipment_ids = {
            row["equipment_code"]: row["id"]
            for row in cursor.execute(
                "SELECT id, equipment_code FROM equipment"
            ).fetchall()
        }

        downtime_logs = [
            ("EQ001", "2026-10-20", "Motor overheating",
             120, "Motor inspected and serviced"),
            ("EQ005", "2026-10-24", "Filling nozzle blockage",
             45, "Nozzle cleaned"),
            ("EQ003", "2026-10-28", "Heating issue",
             90, "Heating system inspected")
        ]

        cursor.executemany("""
            INSERT INTO downtime_logs (
                equipment_id, breakdown_date, problem,
                downtime_minutes, corrective_action
            ) VALUES (?, ?, ?, ?, ?)
        """, [
            (equipment_ids[code], dt, problem, minutes, action)
            for code, dt, problem, minutes, action in downtime_logs
        ])

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
