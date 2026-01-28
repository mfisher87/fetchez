# 🧪 Fetchez Workflows, Examples & User Scripts

This directory contains standalone scripts and "recipes" that demonstrate how to use `fetchez` as a Python library to build powerful geospatial workflows.

Unlike the core `fetchez` CLI, these scripts may require additional dependencies (like `gdal`, `pandas`, `rasterio`, or `geopandas`).

## 📂 Available Recipes

| Script | Description | Dependencies |
| :--- | :--- | :--- |
| `process_bing.py` | Downloads Microsoft Building Footprints and merges them into a single GeoPackage. | `fetchez`, `gdal` |
| `visualize_tides.py` | Fetches NOAA Tide data and generates a generic plot. | `fetchez`, `matplotlib`, `pandas` |

## 💻 How to Run

1.  Ensure you have `fetchez` installed (`pip install fetchez`).
2.  Install any script-specific dependencies (e.g., `conda install gdal`).
3.  Run the script directly:
    ```bash
    python process_bing.py -R -105.5/-104.5/39.5/40.5 -o my_data.gpkg
    ```

## 🤝 How to Contribute

Have a cool script? We'd love to see it!

1.  **Keep it focused:** The script should solve one specific problem well.
2.  **Use `fetchez`:** The script must use `fetchez` for the data acquisition step.
3.  **Document imports:** If you use libraries outside of `fetchez` core, please list them at the top of your file.