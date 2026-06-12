from ultralytics import YOLO
import os

# Load Models
model1 = YOLO("models/Model_01_best.pt")
model2 = YOLO("models/Model_02_best.pt")


def detect_weapon(image_path):

    # =========================
    # Model 1 - Weapon / No Weapon
    # =========================
    results1 = model1(
        image_path,
        conf=0.20
    )

    print("Model 1 detections:", len(results1[0].boxes))

    for box in results1[0].boxes:
        print(
            "Model1 Confidence:",
            float(box.conf[0])
        )

    if len(results1[0].boxes) == 0:
        return {
            "status": "No Weapon",
            "weapon_type": None,
            "confidence": 0,
            "detected_image": None
        }

    # =========================
    # Model 2 - Weapon Classification
    # =========================
    results2 = model2(
    image_path,
    conf=0.20
)

    detected_filename = (
        "detected_" + os.path.basename(image_path)
    )

    detected_path = os.path.join(
        "static/detected",
        detected_filename
    )

    # Save detection image with bounding boxes
    results2[0].save(filename=detected_path)

    # Debug information
    print("Model 2 detections:", len(results2[0].boxes))

    if len(results2[0].boxes) > 0:

        for box in results2[0].boxes:
            print(
                "Class:",
                int(box.cls[0]),
                "Confidence:",
                float(box.conf[0])
            )

        box = results2[0].boxes[0]

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        weapon_name = model2.names[class_id]

        return {
            "status": "Weapon Detected",
            "weapon_type": weapon_name,
            "confidence": round(confidence * 100, 2),
            "detected_image": detected_filename
        }

    # Model 1 detected weapon but Model 2 failed
    return {
    "status": "No Weapon",
    "weapon_type": None,
    "confidence": 0,
    "detected_image": None
}