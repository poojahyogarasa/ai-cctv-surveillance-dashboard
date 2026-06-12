from flask import Flask, render_template, request, redirect
from detector import detect_weapon
from database.db import get_connection
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# Dashboard
# =========================
@app.route('/')
def dashboard():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Recent Alerts
    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY alert_time DESC
        LIMIT 10
    """)
    alerts = cursor.fetchall()

    # Total Alerts
    cursor.execute("""
        SELECT COUNT(*) AS total_alerts
        FROM alerts
    """)
    total_alerts = cursor.fetchone()["total_alerts"]

    # Firearm Alerts
    cursor.execute("""
        SELECT COUNT(*) AS firearm_alerts
        FROM alerts
        WHERE weapon_type='firearm'
    """)
    firearm_alerts = cursor.fetchone()["firearm_alerts"]
    # Threat Level
    if firearm_alerts >= 5:
      threat_level = "CRITICAL"
    elif firearm_alerts >= 3:
      threat_level = "HIGH"
    elif firearm_alerts >= 1:
      threat_level = "MEDIUM"
    else:
      threat_level = "LOW"

    # Knife Alerts
    cursor.execute("""
        SELECT COUNT(*) AS knife_alerts
        FROM alerts
        WHERE weapon_type='knife'
    """)
    knife_alerts = cursor.fetchone()["knife_alerts"]

    # Axe Alerts
    cursor.execute("""
        SELECT COUNT(*) AS axe_alerts
        FROM alerts
        WHERE weapon_type='axe'
    """)
    axe_alerts = cursor.fetchone()["axe_alerts"]

    latest_alert = alerts[0] if alerts else None


    # Threat Level Calculation
    if total_alerts >= 6:
      threat_level = "HIGH"
    elif total_alerts >= 1:
      threat_level = "MEDIUM"
    else:
      threat_level = "LOW"



    cursor.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        alerts=alerts,
        total_alerts=total_alerts,
        firearm_alerts=firearm_alerts,
        knife_alerts=knife_alerts,
        axe_alerts=axe_alerts,
        alarm=False,
        threat_level=threat_level,
        latest_alert=latest_alert
    )


@app.route('/detect')
def detect():

    return render_template(
        "detection_console.html"
    )



# =========================
# Feedback Route
# =========================
@app.route('/upload', methods=['POST'])
def upload():

    if 'image' not in request.files:
        return dashboard()

    file = request.files['image']

    if file.filename == '':
        return dashboard()

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    # Save uploaded image
    file.save(filepath)

    # Run detection
    result = detect_weapon(filepath)

    # Alarm status
    alarm = False

    if result["status"] == "Weapon Detected":
        alarm = True

    # Database connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Save only weapon detections
    if result["status"] == "Weapon Detected":

        cursor.execute("""
INSERT INTO alerts
(
    image_name,
    detected_image,
    weapon_type,
    confidence
)
VALUES (%s,%s,%s,%s)
""",(
    file.filename,
    result["detected_image"],
    result["weapon_type"],
    result["confidence"]
))

        conn.commit()

    # Recent Alerts
    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY alert_time DESC
        LIMIT 10
    """)
    alerts = cursor.fetchall()

    # Total Alerts
    cursor.execute("""
        SELECT COUNT(*) AS total_alerts
        FROM alerts
    """)
    total_alerts = cursor.fetchone()["total_alerts"]

    # Firearm Alerts
    cursor.execute("""
        SELECT COUNT(*) AS firearm_alerts
        FROM alerts
        WHERE weapon_type='firearm'
    """)
    firearm_alerts = cursor.fetchone()["firearm_alerts"]

    # Knife Alerts
    cursor.execute("""
        SELECT COUNT(*) AS knife_alerts
        FROM alerts
        WHERE weapon_type='knife'
    """)
    knife_alerts = cursor.fetchone()["knife_alerts"]

    # Axe Alerts
    cursor.execute("""
        SELECT COUNT(*) AS axe_alerts
        FROM alerts
        WHERE weapon_type='axe'
    """)
    axe_alerts = cursor.fetchone()["axe_alerts"]

    cursor.close()
    conn.close()

    return render_template(
        'detection_console.html',
        result=result,
        uploaded_image=file.filename,
        alerts=alerts,
        total_alerts=total_alerts,
        firearm_alerts=firearm_alerts,
        knife_alerts=knife_alerts,
        axe_alerts=axe_alerts,
        alarm=alarm
    )

@app.route('/alerts')
def all_alerts():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY alert_time DESC
    """)

    alerts = cursor.fetchall()

    conn.close()

    return render_template(
        'all_alerts.html',
        alerts=alerts
    )

@app.route('/alert/<int:alert_id>')
def alert_details(alert_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM alerts
        WHERE id = %s
    """, (alert_id,))

    alert = cursor.fetchone()

    conn.close()

    return render_template(
        "alert_details.html",
        alert=alert
    )

@app.route('/verify/<int:alert_id>/correct')
def verify_correct(alert_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET actual_label = weapon_type,
            is_correct = 1
        WHERE id=%s
    """,(alert_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/alert/{alert_id}")


@app.route('/verify/<int:alert_id>/false')
def verify_false(alert_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET is_correct = 0
        WHERE id=%s
    """,(alert_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/alert/{alert_id}")

# =========================
# Run Application
# =========================
if __name__ == '__main__':
    app.run(
        debug=True,
        use_reloader=False
    )