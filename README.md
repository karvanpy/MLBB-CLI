# MLBB-CLI

A command-line interface tool for Mobile Legends: Bang Bang account information retrieval from mobilelegends.com website.

## Features

- Secure login using verification code
- Display account information including:
  - Player Name
  - Level
  - Rank Level
  - Country
  - Account ID (Role ID)
  - Server ID (Zone ID)

## Prerequisites

- Python 3.8 or higher
- uv or pip (uv is recommended)

## Installation and Usage

```bash
git clone https://github.com/karvanpy/MLBB-CLI.git
cd MLBB-CLI
uv venv
uv pip install -r requirements.txt
uv run login.py
```