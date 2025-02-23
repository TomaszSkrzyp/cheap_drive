# 🚗 **CheapDrive**

**CheapDrive** is a **Django-based web application** designed to help users find **optimal driving routes** with necessary **fuel stops**. Whether you're focused on **saving time** or maximizing **fuel efficiency**, the app calculates the best route for your journey. It provides **real-time gas prices** and uses a **PostgreSQL database** with **PostGIS** integration for precise geographic calculations.

With **advanced trip cost estimations**, **CheapDrive** considers both **time** and **fuel consumption** to estimate journey costs. Frequently requested routes are **cached for up to 2 hours**, reducing load on external APIs while keeping results reasonably up-to-date.

---

## 📌 **Features**

- **Optimal Route Calculation:** Find the best driving route with fuel stop suggestions based on time or fuel efficiency.
- **Real-Time Gas Prices:** Access the latest fuel prices integrated into route planning.
- **PostGIS Integration:** Leverage geographic calculations for accurate distance, route, and fuel estimations.
- **Trip Cost Estimation:** Estimate trip costs based on **time** or **fuel consumption**.
- **Efficient API Usage:** Cached route calculations for 2 hours to minimize API calls.
- **Custom Styling:** Responsive, user-friendly design with **CSS**.
- **Interactive Features:** Engaging elements powered by **JavaScript**.

---

## 🚀 **Installation**

### **Prerequisites**
- **Python 3.x**
- **PostgreSQL** with **PostGIS** enabled
- **GDAL** and **GEOS** libraries for geospatial functionality

### **1. Clone the Repository**
Clone the repository to your local machine:

```bash
git clone https://github.com/TomaszSkrzyp/cheapdrive.git
cd cheapdrive
```

### **2. Create and Activate a Virtual Environment**

For **Linux/macOS**:
```bash
python -m venv .venv
source .venv/bin/activate
```

For **Windows**:
```bash
python -m venv .venv
.\venv\Scripts\activate
```

### **3. Install Dependencies**
Install the required Python packages:

```bash
pip install -r requirements.txt
```

For geospatial support, install **GDAL**:
- **macOS**: `brew install gdal`
- **Ubuntu**: `sudo apt-get install libgdal-dev`
- **Windows**: Install manually (see [GDAL installation guide](https://gdal.org/download.html)).

### **4. Set Up PostgreSQL with PostGIS**
- Install **PostgreSQL**:
  - **Ubuntu**: `sudo apt-get install postgresql`
  - **macOS**: `brew install postgresql`
  - **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/).
- Install **PostGIS**:
  - **Ubuntu**: `sudo apt-get install postgresql-XX-postgis-XX` (replace `XX` with your version, e.g., `15`).
  - **macOS**: `brew install postgis`
  - **Windows**: Use Stack Builder during PostgreSQL installation.
- Create and configure the database:
  ```bash
  psql -U postgres
  CREATE DATABASE your_database_name;
  \c your_database_name
  CREATE EXTENSION postgis;
  ```
  Verify with: `SELECT PostGIS_Version();`

### **5. Configure Environment Variables**
Create a `.env` file in the project root with the following:

```bash
SECRET_KEY=your_secret_key
DEBUG=True  # Set to False in production
SESSION_COOKIE_AGE=600  # Session timeout in seconds (e.g., 10 minutes)
DB_NAME=your_database_name
DB_USER=your_db_user_name
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
GDAL_INCLUDE_DIR=path_to_your_gdal_include
GDAL_LIBRARY_PATH=path_to_your_gdal_library
GEOS_LIBRARY_PATH=path_to_your_geos_library
```

### **6. Run Database Migrations**
Set up the database tables:

```bash
cd cheapdrive_web
python manage.py makemigrations
python manage.py migrate
```

### **7. Collect Static Files**
Prepare static assets (**CSS**, **JavaScript**):

```bash
python manage.py collectstatic
```

### **8. Run the Application**
Start the development server:

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to use **CheapDrive**.

---

## 🛠️ **Additional Setup**

### **Testing the Application**
To ensure **CheapDrive** works as expected:

- Create an admin user to access the Django admin interface:
  ```bash
  python manage.py createsuperuser
  ```
- Test core functionality by planning a sample trip (e.g., from one city to another) to confirm that routing, gas price integration, and cost estimations display correctly.
- Verify caching by requesting the same route within 2 hours; subsequent requests should return faster, cached results.

### **Production Deployment (Optional)**
To deploy **CheapDrive** in a production environment:

- Update `.env` for security:
  - Set `DEBUG=False` to disable debug mode.
  - Use a strong, unique `SECRET_KEY`.
- Install and configure a WSGI server:
  ```bash
  pip install gunicorn
  gunicorn cheapdrive_web.wsgi
  ```
- Set up a web server (e.g., **Nginx**) to serve static files and proxy requests to Gunicorn. Example Nginx config snippet:
  ```
  server {
      listen 80;
      server_name your_domain.com;

      location /static/ {
          alias /path/to/cheapdrive/static/;
      }

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host host;
          proxy_set_header X-Real-IP remote_addr;
      }
  }
  ```
- Consider using a managed database service (e.g., AWS RDS or Heroku Postgres) with **PostGIS** enabled for scalability.

---

## 🛠 **Technologies Used**

- **Django 5.1.4** – A high-level Python web framework that drives **CheapDrive**, offering robust tools for rapid development and scalability.
- **PostgreSQL with PostGIS** – An advanced open-source database with spatial extensions, enabling precise geographic queries for routes and fuel stops.
- **Google Maps API** – Powers route calculations, providing accurate distances, travel times, and directions based on real-time data.
- **Geopy** – A Python library for geocoding and distance calculations, enhancing location-based features in route planning.
- **BeautifulSoup4** – A web scraping tool used to extract real-time fuel prices from online sources, integrated into cost estimations.
- **JavaScript** – Drives dynamic frontend interactions, such as map updates and responsive UI elements.
- **CSS** – Custom styles for a polished, responsive design that ensures a seamless user experience across devices.

---

## 📜 **License**

This project is licensed under the **MIT License**, allowing for free use, modification, and distribution. See the [LICENSE](LICENSE) file for full details.

---

## 🔗 **Contributing**

We welcome contributions to enhance **CheapDrive**! To contribute, please follow these steps:

1. **Fork** the repository to your GitHub account.
2. Create a new feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes (e.g., bug fixes, new features, or documentation improvements).
4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add your concise description here"
   ```
5. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. Open a **Pull Request** on the main repository, detailing your changes and their purpose.

All contributions are appreciated—thank you for helping improve **CheapDrive**!

---

## 📧 **Contact**

For questions, bug reports, or suggestions, please reach out via the **[GitHub Issues](https://github.com/TomaszSkrzyp/cheapdrive/issues)** page. We’re here to assist and value your feedback!