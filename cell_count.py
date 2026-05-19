from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tifffile as tiff
from scipy import ndimage as ndi
from skimage import exposure, feature, filters, measure, morphology, segmentation
from skimage.segmentation import find_boundaries


def dominant_channel(image: np.ndarray) -> int:
    """Return the RGB channel with the strongest high-intensity signal."""
    scores = [
        np.percentile(image[..., channel], 99.5) - np.percentile(image[..., channel], 50)
        for channel in range(3)
    ]
    return int(np.argmax(scores))


def marker_from_name(path: Path) -> str:
    name = path.name.lower()
    if "olig2" in name:
        return "Olig2"
    if "neun" in name:
        return "NeuN"
    return "unknown"


def marker_params(marker: str) -> dict[str, float | int]:
    if marker == "Olig2":
        return {
            "threshold_factor": 0.95,
            "min_size": 18,
            "min_distance": 8,
            "min_area": 20,
            "max_area": 500,
        }
    return {
        "threshold_factor": 0.82,
        "min_size": 35,
        "min_distance": 7,
        "min_area": 45,
        "max_area": 900,
    }


def segment_cells(image: np.ndarray, marker: str) -> tuple[np.ndarray, int]:
    if image.ndim != 3 or image.shape[-1] < 3:
        raise ValueError("Expected an RGB TIFF image.")

    params = marker_params(marker)
    channel = dominant_channel(image)
    gray = image[..., channel].astype(float) / 255.0

    background = filters.gaussian(gray, sigma=18, preserve_range=True)
    corrected = np.clip(gray - background, 0, None)
    corrected = exposure.rescale_intensity(corrected, in_range="image", out_range=(0, 1))
    smooth = filters.gaussian(corrected, sigma=1.0, preserve_range=True)

    threshold = filters.threshold_otsu(smooth) * float(params["threshold_factor"])
    binary = smooth > threshold
    binary = morphology.remove_small_objects(binary, min_size=int(params["min_size"]))
    binary = morphology.remove_small_holes(binary, area_threshold=25)
    binary = morphology.binary_opening(binary, morphology.disk(1))

    distance = ndi.distance_transform_edt(binary)
    peaks = feature.peak_local_max(
        distance,
        labels=binary,
        min_distance=int(params["min_distance"]),
        exclude_border=False,
    )
    markers = np.zeros(distance.shape, dtype=np.int32)
    if len(peaks):
        markers[tuple(peaks.T)] = np.arange(1, len(peaks) + 1)

    labels = segmentation.watershed(-distance, markers, mask=binary)
    props = measure.regionprops(labels, intensity_image=gray)
    keep = [
        prop.label
        for prop in props
        if int(params["min_area"]) <= prop.area <= int(params["max_area"])
    ]
    return measure.label(np.isin(labels, keep)), channel


def save_overlay(image: np.ndarray, labels: np.ndarray, count: int, output_path: Path) -> None:
    display = image[..., :3].astype(float) / 255.0
    overlay = display.copy()
    overlay[find_boundaries(labels, mode="outer")] = [1.0, 0.0, 0.0]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), dpi=160)
    axes[0].imshow(display)
    axes[0].set_title(output_path.stem.replace("_overlay", ""))
    axes[0].axis("off")
    axes[1].imshow(overlay)
    axes[1].set_title(f"count={count}")
    axes[1].axis("off")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Count NeuN/Olig2 positive cells in RGB TIFF images.")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for image_path in args.images:
        marker = marker_from_name(image_path)
        image = tiff.imread(image_path)
        labels, channel = segment_cells(image, marker)
        props = measure.regionprops(labels)
        areas = np.array([prop.area for prop in props], dtype=float)
        count = len(props)
        rows.append(
            {
                "image": image_path.name,
                "marker": marker,
                "channel": channel,
                "count": count,
                "mean_area": round(float(areas.mean()), 1) if len(areas) else 0,
                "median_area": round(float(np.median(areas)), 1) if len(areas) else 0,
            }
        )
        save_overlay(image, labels, count, args.out / f"{image_path.stem}_overlay.png")

    with (args.out / "counts.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["image", "marker", "channel", "count", "mean_area", "median_area"],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
