# PlantCare — Preventive Maintenance and Calibration Management System

## Overview

PlantCare is a web-based application designed to help manufacturing plants manage equipment maintenance, instrument calibration, spare parts inventory, and machine downtime.

The system helps identify overdue maintenance, monitor calibration expiry dates, highlight spare parts with zero stock, and record breakdown history.

## Problem Statement

Manufacturing plants use different machines and measuring instruments that require periodic maintenance and calibration. Manual tracking using spreadsheets can lead to missed maintenance schedules, expired calibration, unexpected breakdowns, and spare parts shortages.

PlantCare provides a centralized system for monitoring these activities.

## Features

* **Equipment Register:** Maintains equipment details and maintenance plans.
* **Preventive Maintenance:** Supports time-based and usage-based maintenance scheduling.
* **Calibration Management:** Tracks instrument calibration expiry dates.
* **Production Eligibility Check:** Blocks the eligibility check when required calibration has expired.
* **Spare Parts Inventory:** Tracks spare quantities and identifies zero-stock items.
* **Downtime Tracking:** Records breakdown details, downtime duration, and corrective actions.
* **Dashboard:** Displays equipment status, overdue maintenance, expired calibration, production restrictions, spare shortages, and recent downtime.

## Technology Stack

* Python
* Flask
* SQLite
* HTML
* CSS
* Jinja Templates

## Project Structure

```text
novintix/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
├── plantcare.db
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── equipment.html
│   ├── maintenance.html
│   ├── calibration.html
│   ├── spares.html
│   └── downtime.html
└── static/
    └── css/
        └── style.css
```

The database file is generated automatically when the application initializes if it does not already exist.

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Replace the placeholder with the repository URL provided by GitHub.

### 2. Open the project directory

```bash
cd novintix
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000/

## Sample Scenarios

The application initializes sample equipment, spare parts, and downtime records when the database is empty.

The sample data includes an instrument whose calibration expires on the configured test date and a spare part with zero stock.

The application currently uses a fixed test date of 31 October 2026 for demonstrating the required scenarios.

## Important Notes

* The current application is a prototype intended to demonstrate maintenance and calibration tracking.
* Production eligibility checking currently focuses on calibration expiry.
* A real production system should incorporate all applicable safety, maintenance, quality, and product-release requirements.
* Calibration renewal records should be verified against the relevant calibration certificate before equipment or products are released.
