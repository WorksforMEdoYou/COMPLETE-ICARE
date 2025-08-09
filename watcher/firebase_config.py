import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
import firebase_admin
from firebase_admin import credentials

# Load environment variables from .env
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """
    A singleton-style manager to initialize Firebase Admin SDK once per application runtime.
    """
    _initialized = False

    def __init__(self):
        """
        Set up credential path from environment or default location.
        """
        path = os.path.dirname(os.path.abspath(__file__))
        default_cred_path = os.path.join(path, '.', 'traveller-10f69-firebase-adminsdk-fbsvc-ab6ff30e39.json')
        self.credential_path = os.getenv('FIREBASE_CRED_PATH', default_cred_path)

        if not os.path.exists(self.credential_path):
            raise FileNotFoundError(f"Firebase credentials file not found at {self.credential_path}")

    def initialize(self):
        """
        Initialize Firebase Admin SDK if not already initialized.
        """
        if FirebaseManager._initialized:
            logger.info("Firebase app already initialized. Skipping re-initialization.")
            return

        try:
            cred = credentials.Certificate(self.credential_path)
            firebase_admin.initialize_app(cred)
            FirebaseManager._initialized = True
            logger.info("Firebase in Watcher initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Firebase in Watcher: {e}")
            raise HTTPException(status_code=500, detail="Error initializing Firebase in Watcher")
