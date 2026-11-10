"""Download and extract the UCI Online Retail workbook."""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
DATA_DIR = Path(__file__).resolve().parent / "data"
TARGET = DATA_DIR / "Online Retail.xlsx"

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        print(f"Dataset already exists: {TARGET}")
        return
    print("Downloading UCI Online Retail dataset...")
    try:
        with urlopen(URL, timeout=60) as response:
            archive_bytes = response.read()
        with ZipFile(BytesIO(archive_bytes)) as archive:
            candidates = [n for n in archive.namelist() if n.lower().endswith(".xlsx")]
            if not candidates:
                raise RuntimeError("No Excel workbook was found in the downloaded archive.")
            chosen = candidates[0]
            TARGET.write_bytes(archive.read(chosen))
        print(f"Dataset saved to: {TARGET}")
    except Exception as exc:
        print(f"Download failed: {exc}")
        print("Download the Online Retail.xlsx file manually from:")
        print("https://archive.ics.uci.edu/dataset/352/online+retail")
        print(f"Then place it at: {TARGET}")
        raise

if __name__ == "__main__":
    main()
