import requests
import zipfile
import io
import polars as pl

url = "https://foerderdatenbankdump.fra1.cdn.digitaloceanspaces.com/data/data.zip"

response = requests.get(url)
response.raise_for_status()

with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    file_name = z.namelist()[0]
    with z.open(file_name) as f:
        df = pl.read_parquet(f)

print(df.head())

print(df["funding_type"].to_list()[999])
