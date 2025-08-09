import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'yourdb connection string here')

# Create async engine and session
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

# Function to initialize the database connection
async def init_db():
    try:
        async with engine.begin() as conn:
            # Optionally, perform any setup tasks here (e.g., create tables)
            pass
        logger.info("MYSQL Database connection for backoffice app is established successfully.")
    except OperationalError as e:
        logger.error(f"Operational error connecting to the MYSQL database for backoffice app: {str(e)}")
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the MYSQL database for backoffice app: {str(e)}")