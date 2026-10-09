import urllib.request
import sys
from pathlib import Path

def main():
    url = "https://zenodo.org/records/13350497/files/ReplogleWeissman2022_K562_gwps.h5ad"
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ReplogleWeissman2022_K562_gwps.h5ad"
    
    print(f"Starting download from: {url}")
    print(f"Saving to: {out_path}")
    
    def reporthook(blocknum, blocksize, totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = readsofar * 100.0 / totalsize
            # Print progress every ~100MB (approx 12200 blocks of 8192 bytes)
            if blocknum % 12200 == 0 or readsofar >= totalsize:
                s = f"Downloaded {readsofar / (1024**2):.1f} MB / {totalsize / (1024**2):.1f} MB ({percent:.1f}%)\n"
                sys.stdout.write(s)
                sys.stdout.flush()
        else:
            if blocknum % 12200 == 0:
                sys.stdout.write(f"Read {readsofar / (1024**2):.1f} MB\n")
                sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, out_path, reporthook)
        print("Download completed successfully!")
    except Exception as e:
        print(f"Error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
