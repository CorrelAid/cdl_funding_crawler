# Funding Crawler

The `Funding Crawler` project is a Python-based web crawling tool and pipeline developed to extract funding programs from the [Förderdatenbank website](https://www.foerderdatenbank.de/FDB/DE/Home/home.html) of the BMWE. The results are stored as `.parquet` and `.csv` files, which can be downloaded via a separate link:


**[Link to parquet data](https://foerderdatenbankdump.fra1.cdn.digitaloceanspaces.com/data/parquet_data.zip)** (does include all columns)

**[Link to csv data](https://foerderdatenbankdump.fra1.cdn.digitaloceanspaces.com/data/csv_data.zip)** (does not include all available columns and list and struct data was converted to string)

- The Crawler runs following cron syntax: `0 2 */2 * *`. First run occured on Jun 19 25.
- The data includes programs currently available on the website, but also deleted programs.

**[Live notebook with some descriptive stats](https://correlaid.github.io/cdl_funding_crawler/)** (updated weekly)

## License
### Code 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

see `LICENSE-CODE`

### Data 

We refer to the [imprint of foerderdatenbank.de](https://www.foerderdatenbank.de/FDB/DE/Meta/Impressum/impressum.html) of the German Federal Ministry for Economic Affairs and Energy which indicates [CC BY-ND 3.0 DE](https://creativecommons.org/licenses/by-nd/3.0/de/deed.de) as the license for all texts of the website. The dataset provided in this repository transfers information on each funding program into a machine-readable format. No copyright-relevant changes are made to texts or content.


## Data Structure Description

The columns of the linked dataset correspond to the standardized fields of the detail pages on the scraped website and are defined in the `funding_crawler/models.py` file, but without the checksum and including three additional meta fields `last_updated`,  `on_website_from`, `previous_update_dates` and `offline` (dates correspond to the date of the pipeline run when changes were detected).

## Functionality

- In this project, [Scrapy](https://scrapy.org/) serves as the input for [dlt](https://dlthub.com/). A Scrapy spider iterates over all pages of the funding program overview and extracts data from the respective detail page of each funding program.

- Global settings for scraping, such as scraping frequency and parallelism, can be found and adjusted in the `scrapy_settings.py` file.

- To identify funding programs over the long term, a hash is calculated from the URL.

- Since the website does not provide information on the update or creation date, the [scd2 strategy](https://dlthub.com/docs/general-usage/incremental-loading#scd2-strategy) was chosen for updating the dataset.
    - All funding programs are always scraped.
    - A checksum is calculated from certain fields of a program, which is compared with already existing programs matched by an ID. In case of a discrepancy, the data point is updated, and a value is added to a column that records update dates.
    - New funding programs are added to the dataset.
    - Funding programs that are no longer on the website are retained in the dataset, but the date of their removal, or the last scraping date, is recorded.

- The output from DLT is stored in a serverless Postgres database ([Neon](https://neon.tech/)) and transformed using a query (the DLT output contains one entry per update), so that in the end, there is one row per program.

- The pipeline is orchestrated and operated with [Modal](https://modal.com/). It runs every two days at 2 AM (UTC).

- The Output is saved in a S3 bucket, that can be downloaded and loaded as demonstrated in `load_example.py`.


## Project Structure

The following describes the structure of the relevant folders and files.

```bash
├── dlt_config.toml            # Configuration file for the DLT pipeline
├── scrapy_settings.py         # Configuration settings for Scrapy
├── funding_crawler            # Main project folder for the funding crawler Python code
│   ├── dlt_utils              # Utility module containing code for DLT to use Scrapy as a resource
│   ├── helpers.py             # Helper functions for the core logic of the crawler
│   ├── models.py              # Data models used for validation
│   ├── spider.py              # Contains the scraping logic in the form of a Scrapy spider
├── main.py                    # Entry point of the pipeline
├── pyproject.toml             # uv project configuration
├── tests                      # Test folder containing unit and integration tests
│   ├── test_dlt               # Tests related to the DLT pipeline
│   └── test_scrapy            # Tests related to Scrapy spiders
```

## Development Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/awodigital/funding_crawler.git
   cd funding_crawler
   ```

2. **Install uv:**

   Follow [these instructions](https://docs.astral.sh/uv/getting-started/installation/).

3. **Install Python Requirements:**

   ```bash
   uv sync
   ```

4. **Set Up Pre-commit:**

   ```bash
   uv run pre-commit install
   ```

5. To access modal, the serverless database and DigitalOcean, where the final dataset is uploaded to, either ask a CorrelAid admin for the credentials or use your own infrastructure by exporting the following environment variabels:
    ```
     export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID=""
     export DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY=""
     export DESTINATION__FILESYSTEM__CREDENTIALS__ENDPOINT_URL=""
     export POSTGRES_CONN_STR="postgresql://....."
    ##### Make sure this does not end up in your shell history
    ```
## Redeploy pipeline
Requires the env vars to be set described above:
```
uv run modal deploy main.py
```

## Tests
This repository contains a limited number of tests.
You can run a spcific test with:

```bash
uv run pytest tests/test_spider.py -s -vv
```

## Contact

For any questions or suggestions, feel free to open an issue in the GitHub repository.
