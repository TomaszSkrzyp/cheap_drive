# 🚗 CheapDrive

A **Django-based web app** designed to calculate **optimal routes with fuel stops**. It helps users find the best route based on time or fuel efficiency, estimates trip costs, and retrieves **real-time gas prices** from a **PostgreSQL database**.

---

## 📌 Features

✅ **Optimal route calculations** with fuel stops  
✅ **Real-time gas price integration** via **PostgreSQL**  
✅ **Supports geographic calculations** with **PostGIS**  
✅ **Trip cost estimation** based on time or fuel consumption  
✅ **Custom styling** with **CSS**  
✅ **Interactive features** powered by **JavaScript**  

---

## 🚀 Installation

### 1. Clone the Repository
```sh
git clone https://github.com/TomaszSkrzyp/cheapdrive.git
cd cheapdrive
```

### 2. Create and Activate the Virtual Environment
#### Linux/macOS:
```sh
python -m venv .venv
source .venv/bin/activate
```
#### Windows:
```sh
python -m venv .venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```
For MacOS:
```sh
brew install gdal
```
For UBUNTU:
```sh
sudo apt-get install libgdal-dev
```
On windows you might need to install GDAL manually 



### 4. Set Up Environment Variables
Create a `.env` file in the project root and define the following variables:
```
SECRET_KEY=your_secret_key
DEBUG=True  # Set to False in production
SESSION_COOKIE_AGE=3600  # Example: 1 hour
DB_NAME=your_database_name
DB_USER=your_user_name
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
GDAL_INCLUDE_DIR=path_to_your_gdal_include
GDAL_LIBRARY_PATH=path_to_your_gdal_library
```

### 5. Run Database Migrations
```sh
cd cheapdrive_web
python manage.py migrate
```

### 6. Run the Application
```sh
python manage.py runserver
```

---

## 🛠 Technologies Used

- **Django 5.1.4**  
- **PostgreSQL with PostGIS**  
- **Google Maps API**  
- **Geopy, BeautifulSoup4** (for route and fuel calculations)  
- **JavaScript** (for interactive features)  
- **CSS** (for styling)  


---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🔗 Contributing

Contributions are welcome! If you’d like to improve **CheapDrive**, please:

1. **Fork** the repository  
2. **Create a feature branch** (`git checkout -b feature-branch`)  
3. **Commit your changes** (`git commit -m "Added new feature"`)  
4. **Push to GitHub** (`git push origin feature-branch`)  
5. **Submit a pull request** 🚀  

---

## 📧 Contact

For questions or support, reach out via **[GitHub Issues](https://github.com/TomaszSkrzyp/cheapdrive/issues)**.
