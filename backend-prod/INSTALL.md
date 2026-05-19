# DeepTutor Backend Installation Guide

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Installation Steps

1. Extract the package to your desired location

2. Install dependencies manually (requires internet or local packages):
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the backend:
   ```bash
   # Windows
   start_backend.bat

   # Linux/Mac
   ./start_backend.sh
   ```

5. Access the API at http://localhost:8001
