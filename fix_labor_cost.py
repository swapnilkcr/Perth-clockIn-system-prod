import sqlite3
from datetime import datetime

DB_NAME = "prod_management.db"
hourly_rate = 37.95

def recalc_all_jobs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all job IDs from JOBSFINISHED
    cursor.execute("SELECT PN FROM JOBSFINISHED")
    finished_jobs = [row[0] for row in cursor.fetchall()]

    for job_id in finished_jobs:
        # Non-QC hours
        cursor.execute("""
            SELECT SUM((strftime('%s', COALESCE(StopTime, 'now')) - strftime('%s', StartTime)) / 3600.0)
            FROM ClockInOut WHERE JobID = ? AND LOWER(StaffName) != 'qc'
        """, (job_id,))
        non_qc_hours = cursor.fetchone()[0] or 0.0

        # QC hours
        cursor.execute("""
            SELECT SUM((strftime('%s', COALESCE(StopTime, 'now')) - strftime('%s', StartTime)) / 3600.0)
            FROM ClockInOut WHERE JobID = ? AND LOWER(StaffName) = 'qc'
        """, (job_id,))
        qc_hours = cursor.fetchone()[0] or 0.0

        non_qc_hours = round(non_qc_hours, 2)
        qc_hours = round(qc_hours, 2)
        total_labor_cost = round(non_qc_hours * hourly_rate, 2)

        # Update JOBSFINISHED
        cursor.execute("""
            UPDATE JOBSFINISHED
            SET TotalHoursWorked = ?, "TEST TIME" = ?, TotalLaborCost = ?
            WHERE PN = ?
        """, (non_qc_hours, qc_hours, total_labor_cost, job_id))

        # Update TestRecords if exists
        cursor.execute("SELECT qty, unit_price, bill_price, av FROM TestRecords WHERE PN = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            qty, unit_price, bill_price, av = row
            qty = float(qty or 0)
            unit_price = float(unit_price or 0)
            bill_price = float(bill_price or 0)
            av = float(av or 0)

            estimated_time = round(qty * av, 2)
            remaining_time = round(estimated_time - non_qc_hours, 2)
            profit = round((qty * unit_price) - total_labor_cost - (qty * bill_price), 2)

            cursor.execute("""
                UPDATE TestRecords
                SET total_time = ?, test_time = ?, total_labor_cost = ?,
                    estimated_time = ?, remaining_time = ?, profit = ?
                WHERE PN = ?
            """, (non_qc_hours, qc_hours, total_labor_cost, estimated_time, remaining_time, profit, job_id))

        # Update JobTable if still exists (in-progress jobs)
        cursor.execute("""
            UPDATE JobTable
            SET TotalHoursWorked = ?, TotalLaborCost = ?
            WHERE JobID = ?
        """, (non_qc_hours, total_labor_cost, job_id))

        print(f"✅ Updated job {job_id}: Hours={non_qc_hours}, QC={qc_hours}, Cost={total_labor_cost}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    recalc_all_jobs()
