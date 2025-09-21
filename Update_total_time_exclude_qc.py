import sqlite3

DB_NAME = "prod_management.db"  # Change if your DB name is different

def update_total_time_exclude_qc():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all PNs in TestRecords
    cursor.execute("SELECT PN FROM TestRecords")
    all_pns = [row[0] for row in cursor.fetchall()]

    for pn in all_pns:
        # Calculate total hours worked (excluding QC)
        cursor.execute('''
            SELECT COALESCE(SUM(
                CASE WHEN StopTime IS NOT NULL THEN 
                    (strftime('%s', StopTime) - strftime('%s', StartTime)) / 3600.0
                ELSE
                    (strftime('%s', 'now') - strftime('%s', StartTime)) / 3600.0
                END
            ), 0.0)
            FROM ClockInOut WHERE JobID = ? AND StaffName != 'QC'
        ''', (pn,))
        total_time = cursor.fetchone()[0] or 0.0

        # Update TestRecords
        cursor.execute('''
            UPDATE TestRecords SET total_time = ? WHERE PN = ?
        ''', (round(total_time, 2), pn))

    conn.commit()
    conn.close()
    print("✅ All TestRecords updated to exclude QC hours in total_time.")

if __name__ == "__main__":
    update_total_time_exclude_qc()