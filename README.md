# 🚗 CheapDrive
CheapDrive is a **Django-based web application** designed to help users find the **optimal driving routes** that include necessary **fuel stops**. Whether you're concerned about **saving time** or maximizing **fuel efficiency**, the app can calculate the best route for your journey based on either factor. It also provides **real-time gas prices** sourced from a **PostgreSQL database** with **PostGIS** integration for geographic calculations.

With **advanced trip cost estimations**, CheapDrive can calculate the potential cost of your journey by considering both **time** and **fuel consumption**. The app reduces unnecessary load on external APIs by **caching frequently requested routes for up to 2 hours**, ensuring faster responses for commonly traveled paths. 

---

## 📌 Features

- **Optimal Route Calculation:** Get the best driving route with fuel stop suggestions based on time or fuel efficiency.
- **Real-time Gas Prices:** Fetch the latest fuel prices from various sources, stored in a **PostgreSQL database**.
- **PostGIS Integration:** Supports geographic calculations for accurate distance, route, and fuel estimations.
- **Trip Cost Estimation:** Calculate estimated costs for your trip based on either **time** or **fuel consumption**.
- **Efficient API Usage:** Route calculations are cached for a default of **2 hours** to avoid excessive API calls.
- **Custom Styling:** Responsive, user-friendly design styled with **CSS**.
- **Interactive Features:** Engaging interactive elements using **JavaScript**.

---
## 🚀 Installation

### 1. Clone the Repository
Start by cloning the repository to your local machine:

```bash
 git clone https://github.com/TomaszSkrzyp/cheapdrive.git
 cd cheapdrive
 ```

### 2. Create and Activate the Virtual Environment

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

### 3. Install Dependencies
Install the required Python dependencies:

 ```bash
 pip install -r requirements.txt
 ```

For **macOS**:

 ```bash
 brew install gdal
 ```

For **Ubuntu**:

 ```bash
 sudo apt-get install libgdal-dev
 ```

For **Windows**:

You may need to install **GDAL** manually. Please refer to the [GDAL installation guide](https://gdal.org/download.html) for assistance.

### 4. Set Up Environment Variables
Create a `.env` file in the root directory of the project and define the following variables:

 ```bash
 SECRET_KEY=your_secret_key
 DEBUG=True  # Set to False in production for better security
 SESSION_COOKIE_AGE=3600  # Example: Set session timeout to 1 hour
 DB_NAME=your_database_name
 DB_USER=your_db_user_name
 DB_PASSWORD=your_db_password
 DB_HOST=your_db_host
 DB_PORT=your_db_port
 GDAL_INCLUDE_DIR=path_to_your_gdal_include
 GDAL_LIBRARY_PATH=path_to_your_gdal_library
 GEOS_LIBRARY_PATH=path_to_your_geos_library
 ```

### 5. Run Database Migrations
Run the database migrations to set up the necessary tables:

 ```bash
 cd cheapdrive_web
 python manage.py migrate
 ```

### 6. Run the Application
Finally, start the application:

 ```bash
 python manage.py runserver
 ```

Once the server starts, open your browser and go to `http://127.0.0.1:8000/` to use the application.

---

## 🛠 Technologies Used

- **Django 5.1.4** – The core web framework that powers CheapDrive, providing a robust environment for building scalable web applications.  
- **PostgreSQL with PostGIS** – A powerful relational database used for storing and querying data, with PostGIS providing spatial extensions to handle geographic information for route and fuel stop calculations.  
- **Google Maps API** – Utilized for routing and calculating distances, times, and directions based on user input and geographic data.  
- **Geopy** – A Python library used to handle geocoding, reverse geocoding, and distance calculations to assist in route planning.  
- **BeautifulSoup4** – A Python package used to scrape web pages and extract real-time fuel prices from online sources to integrate into route calculations.  
- **JavaScript** – Powers dynamic and interactive features on the frontend, providing a seamless user experience.  
- **CSS** – Custom styling to ensure an attractive and user-friendly interface, enhancing the overall look and feel of the application.  

---

## 📜 License

This project is licensed under the **MIT License**. See the full details in the [LICENSE](LICENSE) file.

---

## 🔗 Contributing

We welcome contributions to improve **CheapDrive**! If you're interested in adding a feature, fixing bugs, or improving documentation, please follow the steps below:

1. **Fork** the repository to your GitHub account.  
2. **Create a new feature branch**:  
    ```bash
   git checkout -b feature-branch
     ```
Make your changes (fixes, new features, improvements).
Commit your changes with a meaningful message:
 ```bash git commit -m "Add feature or fix"
Push your changes to your forked repository:
 ```bash 
 git push origin feature-branch
  ```

Open a pull request from your feature branch to the main repository, describing your changes.
We appreciate your contributions!

---

## 📧 Contact
If you have any questions, encounter issues, or have suggestions, please feel free to reach out via the **[GitHub Issues](https://github.com/TomaszSkrzyp/cheapdrive/issues)** page. We're happy to assist!
