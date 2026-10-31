
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "plantcare-development-key"

# Fixed test date for the interview scenario.
# Change to date.today() for live operation.
TEST_DATE = date(2026, 10, 31)


def get_status(equipment):
    today = TEST_DATE

    calibration_status = "NOT REQUIRED"

    if equipment["requires_calibration"]:
        expiry = date.fromisoformat(
            equipment["calibration_expiry_date"]
        )
        calibration_status = (
            "EXPIRED" if expiry <= today else "VALID"
        )

    maintenance_status = "SCHEDULED"

    if equipment["maintenance_type"] == "TIME":
        next_date = date.fromisoformat(
            equipment["next_maintenance_date"]
        )

        if next_date <= today:
            maintenance_status = "OVERDUE"
        elif (next_date - today).days <= 7:
            maintenance_status = "DUE SOON"

    elif equipment["maintenance_type"] == "USAGE":
        if equipment["current_usage"] >= equipment["usage_threshold"]:
            maintenance_status = "OVERDUE"
        elif (
            equipment["usage_threshold"] - equipment["current_usage"]
        ) <= equipment["usage_threshold"] * 0.1:
            maintenance_status = "DUE SOON"

    production_status = (
        "BLOCKED"
        if calibration_status == "EXPIRED"
        else "ELIGIBLE"
    )

    return {
        "calibration_status": calibration_status,
        "maintenance_status": maintenance_status,
        "production_status": production_status,
    }


@app.route("/")
def dashboard():
    conn = get_db()
    equipment = conn.execute(
        "SELECT * FROM equipment ORDER BY equipment_code"
    ).fetchall()

    spares = conn.execute(
        "SELECT * FROM spare_parts ORDER BY part_code"
    ).fetchall()

    downtime = conn.execute("""
        SELECT d.*, e.equipment_code, e.name
        FROM downtime_logs d
        JOIN equipment e ON e.id = d.equipment_id
        ORDER BY d.breakdown_date DESC, d.id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    equipment_data = []

    for item in equipment:
        row = dict(item)
        row.update(get_status(item))
        equipment_data.append(row)

    return render_template(
        "dashboard.html",
        equipment=equipment_data,
        spares=spares,
        downtime=downtime,
        total=len(equipment_data),
        overdue=sum(
            e["maintenance_status"] == "OVERDUE"
            for e in equipment_data
        ),
        expired=sum(
            e["calibration_status"] == "EXPIRED"
            for e in equipment_data
        ),
        blocked=sum(
            e["production_status"] == "BLOCKED"
            for e in equipment_data
        ),
        out_of_stock=sum(s["quantity"] == 0 for s in spares),
        test_date=TEST_DATE.isoformat(),
    )


@app.route("/equipment")
def equipment_register():
    conn = get_db()
    records = conn.execute(
        "SELECT * FROM equipment ORDER BY equipment_code"
    ).fetchall()
    conn.close()

    equipment = []

    for item in records:
        row = dict(item)
        row.update(get_status(item))
        equipment.append(row)

    return render_template(
        "equipment.html",
        equipment=equipment
    )


@app.route("/maintenance")
def maintenance():
    conn = get_db()

    records = conn.execute("""
        SELECT * FROM equipment
        ORDER BY equipment_code
    """).fetchall()

    logs = conn.execute("""
        SELECT m.*, e.equipment_code, e.name
        FROM maintenance_logs m
        JOIN equipment e ON e.id = m.equipment_id
        ORDER BY m.maintenance_date DESC, m.id DESC
    """).fetchall()

    conn.close()

    equipment = []

    for item in records:
        row = dict(item)
        row.update(get_status(item))
        equipment.append(row)

    return render_template(
        "maintenance.html",
        equipment=equipment,
        logs=logs
    )


@app.route("/maintenance/complete/<int:equipment_id>", methods=["POST"])
def complete_maintenance(equipment_id):
    conn = get_db()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    if equipment is None:
        conn.close()
        flash("Equipment not found.", "error")
        return redirect(url_for("maintenance"))

    service_date = TEST_DATE.isoformat()
    description = request.form.get(
        "description", ""
    ).strip()

    if not description:
        conn.close()
        flash("Enter a maintenance description.", "error")
        return redirect(url_for("maintenance"))

    usage = float(equipment["current_usage"])
    interval = float(equipment["maintenance_interval"])

    if equipment["maintenance_type"] == "TIME":
        from datetime import timedelta

        next_date = (
            TEST_DATE + timedelta(days=int(interval))
        ).isoformat()

        conn.execute("""
            UPDATE equipment
            SET last_maintenance_date = ?,
                next_maintenance_date = ?
            WHERE id = ?
        """, (service_date, next_date, equipment_id))

    else:
        conn.execute("""
            UPDATE equipment
            SET current_usage = 0
            WHERE id = ?
        """, (equipment_id,))

    conn.execute("""
        INSERT INTO maintenance_logs (
            equipment_id, maintenance_date,
            description, usage_at_service
        ) VALUES (?, ?, ?, ?)
    """, (equipment_id, service_date, description, usage))

    conn.commit()
    conn.close()

    flash("Maintenance recorded successfully.", "success")
    return redirect(url_for("maintenance"))


@app.route("/calibration")
def calibration():
    conn = get_db()

    records = conn.execute("""
        SELECT * FROM equipment
        WHERE requires_calibration = 1
        ORDER BY calibration_expiry_date
    """).fetchall()

    conn.close()

    instruments = []

    for item in records:
        row = dict(item)
        row.update(get_status(item))
        instruments.append(row)

    return render_template(
        "calibration.html",
        instruments=instruments
    )


@app.route("/calibration/renew/<int:equipment_id>", methods=["POST"])
def renew_calibration(equipment_id):
    from datetime import timedelta

    conn = get_db()

    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()

    if equipment is None or not equipment["requires_calibration"]:
        conn.close()
        flash("Calibration record not found.", "error")
        return redirect(url_for("calibration"))

    try:
        new_expiry = date.fromisoformat(
            request.form.get("expiry_date", "")
        )
    except ValueError:
        conn.close()
        flash("Enter a valid expiry date.", "error")
        return redirect(url_for("calibration"))

    if new_expiry <= TEST_DATE:
        conn.close()
        flash("New expiry must be after the test date.", "error")
        return redirect(url_for("calibration"))

    conn.execute("""
        UPDATE equipment
        SET last_calibration_date = ?,
            calibration_expiry_date = ?
        WHERE id = ?
    """, (
        TEST_DATE.isoformat(),
        new_expiry.isoformat(),
        equipment_id
    ))

    conn.commit()
    conn.close()

    flash(
        "Calibration record updated. Verify the certificate before release.",
        "success"
    )
    return redirect(url_for("calibration"))


@app.route("/production-check", methods=["POST"])
def production_check():
    equipment_id = request.form.get("equipment_id", type=int)

    conn = get_db()
    equipment = conn.execute(
        "SELECT * FROM equipment WHERE id = ?",
        (equipment_id,)
    ).fetchone()
    conn.close()

    if equipment is None:
        flash("Equipment not found.", "error")
        return redirect(url_for("equipment_register"))

    status = get_status(equipment)

    if status["production_status"] == "BLOCKED":
        flash(
            f"Production blocked: {equipment['equipment_code']} "
            "has expired calibration.",
            "error"
        )
    else:
        flash(
            f"{equipment['equipment_code']} passes the calibration "
            "check. Other production release checks may still apply.",
            "success"
        )

    return redirect(url_for("equipment_register"))


@app.route("/spares")
def spares():
    conn = get_db()
    parts = conn.execute(
        "SELECT * FROM spare_parts ORDER BY part_code"
    ).fetchall()
    conn.close()

    return render_template("spares.html", parts=parts)


@app.route("/spares/update/<int:part_id>", methods=["POST"])
def update_spare(part_id):
    quantity = request.form.get("quantity", type=int)

    if quantity is None or quantity < 0:
        flash("Quantity must be zero or greater.", "error")
        return redirect(url_for("spares"))

    conn = get_db()
    result = conn.execute(
        "UPDATE spare_parts SET quantity = ? WHERE id = ?",
        (quantity, part_id)
    )

    conn.commit()
    conn.close()

    if result.rowcount == 0:
        flash("Spare part not found.", "error")
    else:
        flash("Stock updated successfully.", "success")

    return redirect(url_for("spares"))


@app.route("/downtime", methods=["GET", "POST"])
def downtime():
    conn = get_db()

    if request.method == "POST":
        equipment_id = request.form.get("equipment_id", type=int)
        problem = request.form.get("problem", "").strip()
        minutes = request.form.get("downtime_minutes", type=int)
        action = request.form.get("corrective_action", "").strip()

        equipment = conn.execute(
            "SELECT id FROM equipment WHERE id = ?",
            (equipment_id,)
        ).fetchone()

        if (
            equipment is None
            or not problem
            or minutes is None
            or minutes < 0
        ):
            conn.close()
            flash("Enter valid downtime details.", "error")
            return redirect(url_for("downtime"))

        conn.execute("""
            INSERT INTO downtime_logs (
                equipment_id, breakdown_date, problem,
                downtime_minutes, corrective_action
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            equipment_id,
            TEST_DATE.isoformat(),
            problem,
            minutes,
            action
        ))

        conn.commit()
        conn.close()

        flash("Downtime entry added.", "success")
        return redirect(url_for("downtime"))

    records = conn.execute("""
        SELECT d.*, e.equipment_code, e.name
        FROM downtime_logs d
        JOIN equipment e ON e.id = d.equipment_id
        ORDER BY d.breakdown_date DESC, d.id DESC
    """).fetchall()

    equipment = conn.execute("""
        SELECT id, equipment_code, name
        FROM equipment ORDER BY equipment_code
    """).fetchall()

    conn.close()

    return render_template(
        "downtime.html",
        records=records,
        equipment=equipment
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)


