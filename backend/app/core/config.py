import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    raise ValueError("No ORS_API_KEY found in environment variables. Please set it in the .env file.")