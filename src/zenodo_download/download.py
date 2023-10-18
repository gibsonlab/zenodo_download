"""
download.py

main entry point for CLI.
"""
from typing import *
from pathlib import Path

import json
import hashlib
import urllib.request

import requests
from requests.exceptions import ChunkedEncodingError
from tqdm import tqdm

import click


class ChecksumMatchError(BaseException):
    pass


def zenodo_fetch_json(record_id: str) -> Dict:
    url = f'https://zenodo.org/api/records/{record_id}/files'
    contents = urllib.request.urlopen(url).read().decode()
    records = json.loads(contents)
    return records


def zenodo_download_all(record_id: str, out_dir: Path):
    records = zenodo_fetch_json(record_id)
    num_entries = len(records['entries'])
    print("# of total entries = {}".format(num_entries))
    for entry in records['entries']:
        filename = entry['key']
        checksum_str = entry['checksum']
        checksum_alg, checksum_val = checksum_str.split(":")
        out_path = out_dir / filename

        if out_path.exists():
            if check_hash(out_path, checksum_alg, checksum_val):
                print(f"File {out_path.name} already found.")
                continue  # skip this record.
            else:
                print(f"File {out_path.name} exists, but checksums do not match. Redownloading.")
                out_path.unlink()

        done = False
        while not done:
            try:
                zenodo_download_single(record_id, filename, out_path, entry['size'])
                done = True
            except ChunkedEncodingError as e:
                print("Encountered exception: {}".format(str(e)))
                print("Retrying...")
                pass  # retry until done
        if not check_hash(out_path, checksum_alg, checksum_val):
            raise ChecksumMatchError(f"Checksum for newly downloaded file {out_path.name} does not match.")


def check_hash(file_path: Path, checksum_alg: str, checksum_val: str) -> bool:
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")
    h = hashlib.new(checksum_alg)
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            h.update(data)
    digest = h.hexdigest()
    return digest == checksum_val


def zenodo_download_single(record_id: str, filename: str, out_path: Path, total_sz: int, chunk_sz: int = 8192):
    url = f'https://zenodo.org/api/records/{record_id}/files/{filename}/content'

    partial_out_path = out_path.with_suffix(f'{out_path.suffix}.partial')
    if partial_out_path.exists():
        print(f"Resuming download of [{out_path.name}]...")

        dl_size = partial_out_path.stat().st_size

        pbar = tqdm(
            total=total_sz,
            desc=filename,
            unit='B',
            unit_scale=True,
            unit_divisor=1000,
            miniters=1
        )
        pbar.update(dl_size)

        n_chunks = dl_size // chunk_sz
        if dl_size % chunk_sz != 0:
            # Truncate file to nearest chunk.
            print("Applying truncation to nearest chunk size.")
            f = open(partial_out_path, "a")
            f.truncate(chunk_sz * n_chunks)
            f.close()
    else:
        print(f"Downloading [{out_path.name}]...")
        pbar = tqdm(
            total=total_sz,
            desc=filename,
            unit='B',
            unit_scale=True,
            unit_divisor=1000,
            miniters=1
        )

    with requests.get(url, stream=True) as r, open(partial_out_path, 'wb') as f:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_sz):
            f.write(chunk)
            pbar.update(len(chunk))
    partial_out_path.rename(out_path)


@click.command
@click.option(
    '--out-dir', '-o', 'out_dir',
    type=click.Path(path_type=Path, file_okay=True),
    required=False, help="The output directory. If not specified uses the current directory (.)",
    default=Path()
)
@click.option(
    '--record', '-r', 'record_id',
    type=str, required=True,
    help='The zenodo record ID.'
)
def main(record_id: str, out_dir: Path):
    out_dir.mkdir(exist_ok=True, parents=True)
    zenodo_download_all(record_id, out_dir)


if __name__ == "__main__":
    main()
