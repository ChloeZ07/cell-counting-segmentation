from __future__ import annotations

import csv
import shutil
import uuid
from pathlib import Path

import numpy as np
import tifffile as tiff
from flask import Flask, jsonify, render_template, request, send_from_directory
from skimage import measure

from cell_count import marker_from_name, save_overlay, segment_cells


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "web_results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/count", methods=["POST"])
def count_images():
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "No images uploaded."}), 400

    run_id = uuid.uuid4().hex[:10]
    upload_run_dir = UPLOAD_DIR / run_id
    result_run_dir = RESULT_DIR / run_id
    upload_run_dir.mkdir(parents=True, exist_ok=True)
    result_run_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for uploaded_file in files:
        filename = Path(uploaded_file.filename).name
        if not filename.lower().endswith((".tif", ".tiff")):
            continue

        image_path = upload_run_dir / filename
        uploaded_file.save(image_path)

        marker = marker_from_name(image_path)
        image = tiff.imread(image_path)
        labels, channel = segment_cells(image, marker)
        props = measure.regionprops(labels)
        areas = np.array([prop.area for prop in props], dtype=float)
        count = len(props)

        overlay_name = f"{image_path.stem}_overlay.png"
        save_overlay(image, labels, count, result_run_dir / overlay_name)

        rows.append(
            {
                "image": filename,
                "marker": marker,
                "channel": int(channel),
                "count": int(count),
                "mean_area": round(float(areas.mean()), 1) if len(areas) else 0,
                "median_area": round(float(np.median(areas)), 1) if len(areas) else 0,
                "overlay_url": f"/results/{run_id}/{overlay_name}",
            }
        )

    if not rows:
        shutil.rmtree(upload_run_dir, ignore_errors=True)
        shutil.rmtree(result_run_dir, ignore_errors=True)
        return jsonify({"error": "Please upload TIFF images only."}), 400

    csv_path = result_run_dir / "counts.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["image", "marker", "channel", "count", "mean_area", "median_area"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    return jsonify(
        {
            "run_id": run_id,
            "rows": rows,
            "csv_url": f"/results/{run_id}/counts.csv",
        }
    )


@app.route("/results/<run_id>/<path:filename>")
def results(run_id: str, filename: str):
    return send_from_directory(RESULT_DIR / run_id, filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
