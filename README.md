
<div align="center">
  <img src="https://res.cloudinary.com/murste/image/upload/v1698907632/stevolve_x8ioeu.png" alt="Stephen Murichu's Logo" width="100" />
</div>

# Django-inventory-management
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit)
[![Python Version](https://img.shields.io/badge/Python-3.12-green)](https://www.python.org/downloads/)

## Table of Contents
- [Django-inventory-management](#django-inventory-management)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Clone the Repository](#clone-the-repository)
    - [With Docker](#with-docker)
    - [Without Docker](#without-docker)
      - [On Linux](#on-linux)
      - [On Windows](#on-windows)
  - [Screenshots](#screenshots)
  - [Authors](#authors)

## Description
This Django application offers a solution for managing business operations with an emphasis on user experience and modern web technologies. It integrates Bootstrap for front-end design and employs Ajax for dynamic sales creation. The application features models for user profiles, vendors, customers, and transactions, including billing, invoicing, and inventory management.

## Prerequisites
- **Python installed**: Ensure Python is installed on your system. You can download it from the official [Python website](https://www.python.org/).
- **Understand Python and Django**: Basic understanding of Python programming and familiarity with Django web framework.

## Installation

Follow these steps to install the necessary dependencies and set up the application:

### Clone the Repository

```bash
git clone https://github.com/munuhee/sales-and-inventory-management.git
cd sales-and-inventory-management
```

### With Docker

1. **Build the Docker Image**

    ```bash
    docker build -t sales-and-inventory-management:1.0 .
    ```

2. **Run the Docker Container**

    ```bash
    docker run -d -p 8000:8000 sales-and-inventory-management:1.0
    ```

### Without Docker

#### On Linux

1. **Set Up the Virtual Environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Apply Migrations and Run the Server**

    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

#### On Windows

1. **Set Up the Virtual Environment**

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Apply Migrations and Run the Server**

    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

## Screenshots

<details>
  <summary>Click to view screenshots</summary>

  ![screenshot_1](https://github.com/user-attachments/assets/9bb2f5f9-d456-4681-b5de-8d82a3ef97d8)

  ![screenshot_2](https://github.com/user-attachments/assets/d6e14ba3-8827-41c1-9cdb-8f24add83f4d)

  ![screenshot_3](https://github.com/user-attachments/assets/6be5060e-974b-4289-bcdf-b852771833f8)

  ![screenshot_4](https://github.com/user-attachments/assets/5b176c44-82dd-4080-8259-0976029a496f)

  ![screenshot_5](https://github.com/user-attachments/assets/c9ab8f77-bf2a-4b1e-bc66-986101d4991b)

  ![screenshot_6](https://github.com/user-attachments/assets/3db3ca87-28a8-4fee-8cc7-fcc9481076f4)

  ![screenshot_7](https://github.com/user-attachments/assets/1197a79f-8e11-41e1-a8a8-4ea5f0ac0391)

  ![screenshot_8](https://github.com/user-attachments/assets/a340d85b-76dc-4618-b530-97cd620ef649)

  ![screenshot_9](https://github.com/user-attachments/assets/751fe028-6115-424e-b69c-0fedfa9f321f)

  ![screenshot_10](https://github.com/user-attachments/assets/d3905ec2-c843-468c-bdd4-799955854fd6)

  ![screenshot_11](https://github.com/user-attachments/assets/99bb9f1c-4688-4049-b31e-5de1bd817304)

  ![screenshot_12](https://github.com/user-attachments/assets/a0ea68c0-2969-42e4-81cd-fbf6efffd569)

  ![screenshot_13](https://github.com/user-attachments/assets/9fbd7b1c-d60c-456a-957c-4a033cf76d89)

  ![screenshot_14](https://github.com/user-attachments/assets/b6eabb9a-119a-418d-af56-b44d316bf6be)

  ![screenshot_15](https://github.com/user-attachments/assets/ec117dfd-e0ee-46ff-9486-b5262f58b901)

</details>

## Authors

- [Stephen Murichu](https://github.com/munuhee)

                                            Happy coding! 🚀
