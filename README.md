# jira-csv2taiga
JIRA csv to Taiga

## Installation

### Installation on specific distributions

#### Ubuntu
```bash
sudo apt update
sudo apt install python3 python3-pip
pip3 install requests
```

#### Arch Linux
```bash
sudo pacman -Syu
sudo pacman -S python python-pip
pip install requests
```

Install the required dependencies using pip:

```bash
pip install requests
```

## Usage

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
