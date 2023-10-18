# zenodo_download

This is a python executable developed by Younhun Kim (ykim78@bwh.harvard.edu), meant for downloading a complete 
collection of files from a zenodo record.

It has built-in an automatic "resume-download" feature, checksum verification and an automatic "retry-until-finished".

It relies on Zenodo's REST API https://zenodo.org/api/records/<record_id>/files, which outputs a JSON format.
If this program ever breaks, the API has likely changed and the parser needs to be updated.


## Installation / Usage

Clone using git, then install using pip:

```bash
git clone <this_repo_url>
cd zenodo_download
pip install .
```

To run, use
```bash
zenodo_download -r <record_id> -o <out_dir>
```

Display help using
```bash
zenodo_download --help
```
