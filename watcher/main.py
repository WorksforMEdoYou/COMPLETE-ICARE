import pymongo
from dotenv import load_dotenv
import os
import logging
from ServiceStartWatcher import ServiceStartWatcher
from ServiceStopWatcher import ServiceStopWatcher
from firebase_config import FirebaseManager
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)

# Path to .env (update if your .env is in watcher/.env)
load_dotenv(dotenv_path=r"watcher/.env")

def main():
    # MYSQL configuration
    mysql_config = {
        'user': os.getenv('USER'),
        'password': os.getenv('PASSWORD'),
        'host': os.getenv('HOST'),
        'database': os.getenv('DATABASE')
    }
    
    # MongoDB configuration
    connection_string = os.getenv('CONNECTION_STRING')
    client = pymongo.MongoClient(connection_string)
    mongodb_connection = client[os.getenv('MONGODB_DB')]
    
    # Firebase configuration
    firebase_manager = FirebaseManager()
    firebase_manager.initialize()
    
    # JOB 1 Service Provider Service Start
    watcher = ServiceStartWatcher(mysql_config, mongodb_connection)
    stopwatcher = ServiceStopWatcher(mysql_config, mongodb_connection)
    
    # Run both watchers concurrently
    t1 = threading.Thread(target=watcher.run)
    t2 = threading.Thread(target=stopwatcher.run)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()