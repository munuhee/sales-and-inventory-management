# Django Sales and Inventory Management System (POS)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit)
[![Python Version](https://img.shields.io/badge/Python-3.12-green)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.2_LTS-0C4B33)](https://www.djangoproject.com/)

An open-source **sales and inventory management system** built with **Python and Django**. It gives a retail shop a web-based **point of sale (POS)**, **stock control**, **purchase orders**, **PDF receipts and invoices**, **billing** and **customer loyalty points**, with role-based access for admins and staff.

Free to use under the MIT license. Runs with Docker or a plain Python virtualenv, and includes demo data so you can try it in minutes.

## Table of Contents
- [Features](#features)
- [Roles](#roles)
- [Screenshots](#screenshots)
- [Installation](#installation)
  - [With Docker](#with-docker)
  - [Without Docker](#without-docker)
- [Configuration](#configuration)
- [Upgrading an existing database](#upgrading-an-existing-database)
- [Running the tests](#running-the-tests)
- [CI and deployment](#ci-and-deployment)
- [Authors](#authors)

## Features

- **Point of sale.** Search items and customers, see stock while you sell, redeem loyalty points, and get the change worked out. The server prices every sale from the database inside a locked transaction, so totals can't be tampered with and two tills can't oversell the same stock.
- **Receipts and invoices as PDF.** Professional A4 documents rendered with [WeasyPrint](https://weasyprint.org/). **Print** opens the PDF in the browser's viewer; **Download** saves it. A voided sale's receipt carries a VOID watermark.
- **Stock that stays correct.** Purchase orders add stock only when they are received. Editing or deleting an order adjusts stock by the difference. Stock can never go negative.
- **Voids, not deletes.** Voiding a sale returns the items to stock and reverses loyalty points. The sale stays on record.
- **Loyalty points.** Customers earn points on every sale (1 point per Ksh 100 by default) and redeem them as a discount before tax. Every change is logged in a ledger; managers can make recorded corrections.
- **Dashboard.** Revenue today and this month, stock value, low stock alerts, a 30-day sales chart and recent sales.
- **Accounts and security.** Capability-based access by role, separately controlled sign-in access, approval workflow for self sign-ups, staff change history, login throttling, immediate sign-out of deactivated staff, and secure production settings: a Content Security Policy with no inline scripts, SRI hashes on every CDN asset, HttpOnly cookies, HSTS and cross-origin isolation headers.
- **Exports.** Sales, purchases, products and deliveries to Excel (managers only).

## Roles

| Role | Can do |
| --- | --- |
| **Operative** | Sell, print receipts, view stock and invoices, manage customers and deliveries |
| **Executive** | Everything above, plus products, categories, purchase orders, vendors, invoices, bills, exports, voiding sales and point adjustments |
| **Admin** | Everything in Executive, plus staff accounts, account approvals, and staff access management |

Staff sign-in status is separate from employment status. An account can be Active, Inactive, or On leave while sign-in can also be disabled directly. New self sign-ups remain Pending until approved on the **Staff** page. Admins can create Operative and Executive accounts; only a Django superuser can grant the Admin role or modify/delete an Admin account. Role, status, approval, and sign-in changes are recorded in the Staff access activity log. Django superusers are always Admin; the first one is created from the terminal (see [Create the first admin](#create-the-first-admin)).

## Screenshots

Taken from the demo data (`seed_demo`).

| Dashboard | Point of sale |
| --- | --- |
| ![Django inventory management dashboard with sales chart and low stock alerts](docs/screenshots/dashboard.png) | ![Django point of sale (POS) screen](docs/screenshots/point-of-sale.png) |

| Receipt (PDF) | Invoice (PDF) |
| --- | --- |
| ![Receipt](docs/screenshots/receipt.png) | ![Invoice](docs/screenshots/invoice.png) |

<details>
  <summary><b>Sales and customers</b></summary>

  **Sales**, with voided sales flagged
  ![Sales](docs/screenshots/sales.png)

  **Sale detail.** A summary for staff, with Print, Download and Void actions. The receipt itself only appears as the PDF.
  ![Sale detail](docs/screenshots/sale-detail.png)

  **Customers**
  ![Customers](docs/screenshots/customers.png)

  **Customer loyalty history**, with the points ledger and manager adjustments
  ![Customer loyalty](docs/screenshots/customer-loyalty.png)

  **Deliveries**
  ![Deliveries](docs/screenshots/deliveries.png)
</details>

<details>
  <summary><b>Inventory and purchasing</b></summary>

  **Products**, with low stock and out-of-stock flags
  ![Products](docs/screenshots/products.png)

  **Product detail**
  ![Product detail](docs/screenshots/product-detail.png)

  **New product**
  ![New product](docs/screenshots/product-form.png)

  **Categories**
  ![Categories](docs/screenshots/categories.png)

  **Purchase orders.** Stock is added only when an order is received.
  ![Purchase orders](docs/screenshots/purchases.png)

  **New purchase order**
  ![New purchase order](docs/screenshots/purchase-form.png)

  **Vendors**
  ![Vendors](docs/screenshots/vendors.png)
</details>

<details>
  <summary><b>Finance</b></summary>

  **Invoices**
  ![Invoices](docs/screenshots/invoices.png)

  **Invoice detail**, with Print and Download PDF
  ![Invoice detail](docs/screenshots/invoice-detail.png)

  **Bills**
  ![Bills](docs/screenshots/bills.png)
</details>

<details>
  <summary><b>Staff, roles and sign-in</b></summary>

  **Staff management**, with a pending sign-up waiting for approval
  ![Staff](docs/screenshots/staff.png)

  **Editing a staff member's role and access**
  ![Edit staff](docs/screenshots/staff-edit.png)

  **My profile**
  ![Profile](docs/screenshots/profile.png)

  **The cashier's view.** Operatives only see the pages their role allows.
  ![Cashier dashboard](docs/screenshots/cashier-dashboard.png)

  **Sign in**
  ![Sign in](docs/screenshots/login.png)

  **Request an account.** New accounts wait for an Admin to approve them.
  ![Request an account](docs/screenshots/register.png)
</details>

<details>
  <summary><b>Mobile</b></summary>

  <img src="docs/screenshots/mobile.png" alt="Mobile dashboard" width="300"> <img src="docs/screenshots/mobile-menu.png" alt="Mobile menu" width="300">
</details>

## Installation

```bash
git clone https://github.com/munuhee/sales-and-inventory-management.git
cd sales-and-inventory-management
cp .env.example .env    # then edit it
```

### With Docker

The image includes the system libraries WeasyPrint needs.

```bash
docker build -t sales-and-inventory-management .
docker run -d -p 8000:8000 \
  -e SECRET_KEY="change-me" \
  -e ALLOWED_HOSTS="localhost,127.0.0.1" \
  sales-and-inventory-management
```

The container runs migrations, then serves the app with Gunicorn. Add `-e DEBUG=True` for a local trial.

### Without Docker

1. Create a virtual environment and install the dependencies:

    ```bash
    python3 -m venv venv
    source venv/bin/activate          # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2. Install the system libraries WeasyPrint needs to render PDFs:
    - **Debian/Ubuntu:** `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`
    - **macOS:** `brew install pango`
    - **Windows:** install the GTK3 runtime, see the [WeasyPrint guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

    Everything except PDF generation works without them.

3. Set up the database and run the server:

    ```bash
    python manage.py migrate
    python manage.py seed_demo        # optional demo data, empty database only
    python manage.py createsuperuser  # or use the demo accounts
    python manage.py runserver
    ```

`seed_demo` creates the sign-ins `admin`, `manager` and `cashier`, all with the password `demo-pass-123`. It refuses to run when `DEBUG` is off.

### Create the first admin

A new database has no users, and sign-ups made on the "Request an account" page stay pending until an Admin approves them. So before anyone else can get in, create the first Admin from the terminal:

```bash
python manage.py createsuperuser
```

A superuser is always **Active** with the **Admin** role, so it can sign in straight away. Open **Staff** to approve requests and set each person's role.

The same command works wherever the app runs:

```bash
# Docker (use the name or ID shown by "docker ps")
docker exec -it <container> python manage.py createsuperuser

# Azure App Service: open SSH from the portal (Development Tools > SSH).
# The session starts in the app folder, so run
python manage.py createsuperuser

# Terraform VM: SSH in from your admin_cidr range, then
sudo docker exec -it inventory python manage.py createsuperuser
```

For scripted setups, pass the details as environment variables instead of answering prompts:

```bash
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD='a-long-unique-password' \
python manage.py createsuperuser --noinput
```

**Locked out?** `python manage.py changepassword <username>` resets a password. To make an existing account the Admin, run:

```bash
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='<username>'); u.is_superuser = u.is_staff = True; u.save()"
```

Saving the user as a superuser also activates their profile and gives them the Admin role.

To stop public sign-ups entirely, set `ALLOW_REGISTRATION=False`. Admins then add staff themselves from the **Staff** page.

## Configuration

All settings come from environment variables (or a `.env` file). See [.env.example](.env.example) for the full list.

| Variable | Purpose |
| --- | --- |
| `DEBUG` | `True` for development. Defaults to `False`. |
| `SECRET_KEY` | Required when `DEBUG` is off. |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Comma separated. On Azure App Service the site host is added automatically. |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL. SQLite is used when `DB_HOST` is empty. The `AZURE_POSTGRESQL_*` names also work. |
| `ALLOW_REGISTRATION` | Show the "Request an account" page. Defaults to `True`. |
| `BUSINESS_NAME`, `BUSINESS_ADDRESS`, `BUSINESS_PHONE`, `BUSINESS_TAX_PIN`, `BUSINESS_CURRENCY` | Printed on receipts and invoices. |
| `LOYALTY_EARN_PER`, `LOYALTY_POINT_VALUE`, `LOYALTY_MIN_REDEEM`, `LOYALTY_ENABLED` | Loyalty programme rules. |

## Upgrading an existing database

Run `python manage.py migrate`. The migrations:

- convert money fields from floats to exact decimals, and phone numbers to text;
- mark existing staff accounts **Active** so nobody is locked out (only new sign-ups need approval), and make superusers Admin;
- clamp any negative stock or loyalty balance to zero;
- record each customer's existing points as an opening balance in the loyalty ledger;
- repair invoice and bill links that had empty slugs.

## Running the tests

```bash
python manage.py test
```

PDF tests are skipped if WeasyPrint's system libraries are missing. They run in CI and in the Docker image:

```bash
docker run --rm -e DEBUG=True sales-and-inventory-management python manage.py test
```

## CI and deployment

[CI](.github/workflows/ci.yml) runs on every push and pull request to `main`, with two jobs:

- **Lint:** `flake8` with the settings in [.flake8](.flake8).
- **Tests:** `manage.py check`, a check for missing migrations, and the full test suite (PDF tests included).

Deployment is separate from CI. Use the Docker image above, or the Terraform modules:

- [terraform/azure](terraform/azure): an Ubuntu VM that builds the app image, keeps the database on a Docker volume and serves it through Caddy with automatic HTTPS. SSH is open only to `admin_cidr`, and only ports 80 and 443 are public. Point `domain_name` at the `public_ip` output.
- [terraform/docker](terraform/docker): the same image on the local Docker host, published on `127.0.0.1:8080` with the database on a named volume.

Wherever it runs, set `SECRET_KEY` and the database settings, then [create the first admin](#create-the-first-admin).

## Authors

- [Stephen Murichu](https://github.com/munuhee)

                                            Happy coding! 🚀
