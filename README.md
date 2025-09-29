# jira-csv2taiga
JIRA csv to Taiga

## Installation

### Installation on specific distributions

#### Ubuntu
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install requests
```

#### Arch Linux
```bash
sudo pacman -Syu
sudo pacman -S python python-pip
python -m venv venv
source venv/bin/activate
pip install requests
```

Install the required dependencies using pip:

```bash
pip install requests
```

If your system uses PEP 668 (externally managed environment), create a virtual environment first:

```bash
python -m venv venv
source venv/bin/activate
pip install requests
```

## Usage

If you used a virtual environment during installation, activate it first:

```bash
source venv/bin/activate
```

To run the script, use the following command:

```bash
python3 jiracsv2taiga.py
```

Make sure to set the required environment variables:

- `TAIGA_URL`: URL of your Taiga instance
- `TAIGA_USERNAME`: Your Taiga username
- `TAIGA_PASSWORD`: Your Taiga password
- `PROJECT_SLUG`: Slug of the Taiga project
- `CSV_FILE`: Path to the JIRA CSV file (default: Jira_fixed.csv)
- `USER_CSV_FILE`: Path to the users CSV file (default: export-users.csv). If the file exists, users are created before importing tasks. The CSV should have columns: `username`, `email`, `full_name`.
- `RATE_LIMIT`: Rate limit for API calls (default: 0.3 seconds)

### Example

Set environment variables and run:

```bash
export TAIGA_URL="http://taiga.site.az:9000"
export TAIGA_USERNAME="your_username"
export TAIGA_PASSWORD="your_password"
export PROJECT_SLUG="your_project_slug"
export CSV_FILE="Jira_fixed.csv"
python3 jiracsv2taiga.py
```

Or run with inline variables:

```bash
TAIGA_URL="http://taiga.site.az:9000" TAIGA_USERNAME="your_username" TAIGA_PASSWORD="your_password" PROJECT_SLUG="your_project_slug" CSV_FILE="Jira_fixed.csv" python3 jiracsv2taiga.py
```
