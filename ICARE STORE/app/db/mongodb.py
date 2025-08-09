    
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Access the environment variables
MONGO_DETAILS = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
database_name = os.getenv("DATABASE_NAME", "istores")

# MongoDB client and database
client = None
database = None

# Function to connect to MongoDB with retry logic
async def connect_to_mongodb():
    global client, database
    retries = 3
    for attempt in range(retries):
        try:
            client = AsyncIOMotorClient(MONGO_DETAILS)
            database = client[database_name]
            logger.info("Successfully connected to MongoDB.")
            break
        except Exception as e:
            logger.error(f"Error connecting to MongoDB on attempt {attempt + 1}: {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                database = None
                raise RuntimeError("Failed to connect to MongoDB after multiple attempts")

# Function to get the MongoDB database
def get_database():
    if database is None:
        logger.error("Mongodb connection is not established.")
        raise RuntimeError("Mongodb connection is not established.")
    return database

# Example of calling the connect_to_mongodb function
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_to_mongodb())