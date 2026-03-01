🍸 ReelSpirit - AI Powered Instagram Analyzer
    
ReelSpirit is a comprehensive web application that analyses Instagram content creators' profiles, monitors shared Reels videos using Google Gemini AI, and automatically categorises them based on their content (particularly cocktail and drink recipes).

🎯 Project Objective and Approach
    
There are thousands of fantastic cocktail and gastronomy posts on Instagram, but finding a specific recipe (such as ‘vodka-based cocktails’) requires watching hundreds of videos one by one.

ReelSpirit was created to solve this problem:
- It takes an Instagram profile link from the user.
- It extracts the descriptions and metadata from the videos.
- It analyses the content using Artificial Intelligence (Gemini).
- It determines whether the content is a cocktail recipe and, if so, which base spirit (Whisky, Gin, Tequila, etc.) it contains.
- It provides the user with a statistical dashboard and a filterable gallery.

🚀 Features

🔍 Profile Analysis: Can analyse any public Instagram profile (Business/Creator).

🤖 AI-Powered Classification: Intelligently tags videos with Google Gemini integration.

📊 Visual Statistics: A graphical interface showing how many videos are in each category.

⚡ Background Tasks: FastAPI Background Tasks continues to scan large profiles in the background.

🐳 Full Docker Support: Frontend, Backend and Database are up and running with a single command.

📱 Responsive Design: A modern and mobile-friendly interface with Angular Material.

🛠 Technologies Used
Backend
- Python & FastAPI: High performance asynchronous API.
- Google Gemini AI: Content analysis and summarization.
- Instagram Graph API: Data extraction operations.
- PostgreSQL & SQLAlchemy: Database and ORM structure.
- Pydantic: Data validation.

front end
- Angular 18+: Modern SPA architecture.
- RxJS: Reactive programming and polling mechanisms.
- SCSS: Customized styles.

DevOps
- Docker & Docker Compose: Containerization.
- Nginx: Frontend server and Reverse Proxy.

⚙️Installation and Execution
To run this project in your local environment, you only need to have Docker and the Docker Desktop application installed on your computer.

1. Clone the Project
```
git clone https://github.com/yourusername/ReelSpirit.git
cd ReelSpirit-Project
```

2. Configure Environment Variables (Optional)
Within the project, there is a ready-made .env file in the ReelSpirit-Backend folder. This file contains the default API keys and tokens required for the project to run.

To quickly test the project, you can proceed to the next step without making any changes to this file.
However, if you wish to use the project with your own accounts (your own Instagram Business account or your own Google Gemini quota), you can customise these values as follows:

- Open the .env file in the ReelSpirit-Backend folder using any text editor (Notepad, VS Code, etc.).

- Replace the following fields with your own values:
```
# ---Instagram Settings ---
# Enter the ID and Token you obtained from your Facebook Developer portal here
INSTAGRAM_BUSINESS_ID=YOUR_BUSINESS_ID_VALUE
ACCESS_TOKEN=YOUR_FACEBOOK_ACCESS_TOKEN_VALUE

# --- Google AI Settings ---
# Enter the API key you obtained from Google AI Studio here
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_VALUE

# --- Database Settings (Can remain default for Docker) ---
DATABASE_URL=postgresql://postgres:1029@db:5432/ReelSpiritDB
```
Note: Using your own API keys prevents you from hitting the limits (quotas) of the default keys.

3. Start with a Single Command 🚀
Open the terminal in the root directory (where the docker-compose.yml file is located) and enter the following command:

```
docker-compose up --build
```
This process performs the following steps:

- It installs the PostgreSQL database.

- It creates the backend image and starts the API.

- It compiles (builds) the Angular application and serves it with Nginx.

4. Access the Application
Once the installation is complete, go to the following address in your browser:
👉 http://localhost:4200/

For API Documentation (Swagger): 
👉 http://localhost:8000/docs

📂 Project Structure
```
ReelSpirit-Project/
├── docker-compose.yml       # Orchestrates all services
│
├── ReelSpirit-Backend/      # Python FastAPI Service
│   ├── Dockerfile
│   ├── .env                 # API Keys
│   ├── app/
│   │   ├── main.py          # API Entry Point
│   │   ├── services/        # AI and Instagram services
│   │   ├── routers/         # API Endpoint definitions
│   │   └── models.py        # Database models
│   └── requirements.txt
│
└── ReelSpirit-Frontend/     # Angular Application
    ├── Dockerfile
    ├── nginx.conf           # Server settings
    └── src/
        ├── app/
        │   ├── components/  # Page components (Home, Results)
        │   └── services/    # Backend connection services
        └── assets/
```

<img width="757" height="657" alt="image" src="https://github.com/user-attachments/assets/027f519e-6884-48df-bb43-d6ac9d2429c4" />


<img width="813" height="875" alt="image" src="https://github.com/user-attachments/assets/54d62cb8-27bf-4cbe-8f3b-e3b88ea14ece" />


🤝 Contribute
Fork this project.

Create a new feature branch.

Commit your changes.

Push your branch.

Create a Pull Request.

📞 Contact and Developer

Developer: Ozan Muharrem Şahin

Contact: ozanmuharrem9@gmail.com
