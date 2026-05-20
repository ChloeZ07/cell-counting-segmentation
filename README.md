# Cell Counting by Segmentation

This project uses a simple segmentation-based algorithm to count fluorescently labeled cells in microscopy images.

## Method

The algorithm follows these steps:

1. Read the TIFF microscopy image.
2. Extract the target color channel:
   - Olig2: green channel
   - NeuN: blue channel
3. Apply Gaussian smoothing to reduce noise.
4. Use Otsu thresholding to separate bright cell signal from dark background.
5. Remove very small regions that are likely noise.
6. Use watershed segmentation to separate touching cells.
7. Count each segmented region as one cell.

## Results

| Image | Algorithm count | Manual estimate | Error |
|---|---:|---:|---:|
| 9794 Olig2 | 151 | 164 | 7.9% |
| 9794 NeuN | 514 | 546 | 5.9% |
| 9795 Olig2 | 236 | not measured | N/A |
| 9795 NeuN | 574 | not measured | N/A |

## Files

- `simple_cell_count.py`: simplified Python script for cell counting.
- `cell_count.py`: more complete batch-processing script.
- `app.py`: local drag-and-drop web app for running the counter.
- `start_cell_counter.command`: double-click launcher for the local web app on macOS.
- `counts.csv`: output table with cell counts.
- `results/`: overlay images showing detected cell boundaries.

## Web App

To use the local web app:

1. Install the required Python packages:

```bash
python3 -m pip install -r requirements.txt
```

2. Start the app:

```bash
python3 app.py
```

Or on macOS, double-click:

```text
start_cell_counter.command
```

3. Open this local URL in a browser:

```text
http://127.0.0.1:5001
```

4. Drag TIFF images into the page.
5. Check the count table and overlay images.
6. Download `counts.csv` if needed.

If `start_cell_counter.command` does not open after downloading from GitHub, run this once in Terminal:

```bash
chmod +x start_cell_counter.command
```

## Short Description

The algorithm segments bright fluorescent cell signals from the background using thresholding. Small noisy objects are removed, touching cells are separated using watershed segmentation, and the number of segmented regions is used as the final cell count.
