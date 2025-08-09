import datetime
import pytz
import time
import mysql.connector
import logging
from notification import send_push_notification

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceStartWatcher:
    """
    Watcher class to monitor upcoming service appointments and notify relevant parties.
    """

    def __init__(self, mysql_config: dict, mongodb_connection):
        """
        Initialize the watcher with MySQL and MongoDB connection info.
        """
        self.mysql_config = mysql_config
        self.mongodb = mongodb_connection
        self.timezone = pytz.timezone("Asia/Kolkata")

    def connect_mysql(self):
        """
        Creates a MySQL connection using the configuration.
        """
        try:
            return mysql.connector.connect(**self.mysql_config)
        except mysql.connector.Error as err:
            logger.error(f"MySQL connection failed: {err}")
            return None

    def fetch_appointments_started_10_minutes_ago(self):
        now = datetime.datetime.now(tz=self.timezone)
        target_time = (now + datetime.timedelta(minutes=10)).strftime("%H:%M")
        today = now.date().strftime("%Y-%m-%d")

        logger.info(f"Querying with today={today}, target_time={target_time}")

        query = """
            SELECT spap.*, sp.sp_mobilenumber 
            FROM tbl_sp_appointments AS spap
            JOIN tbl_serviceprovider AS sp ON spap.sp_id = sp.sp_id
            WHERE %s BETWEEN spap.start_date AND spap.end_date
            AND LEFT(spap.start_time, 5) = %s
            AND spap.active_flag = 1
        """

        conn = self.connect_mysql()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, (today, target_time))
            return cursor.fetchall()
        except mysql.connector.Error as err:
            logger.error(f"Failed to fetch appointments: {err}")
            return []
        finally:
            cursor.close()
            conn.close()

    def fetch_employee_for_appointment(self, appointment_id):
        query = """
            SELECT spas.sp_employee_id, spemp.employee_name, spemp.employee_mobile
            FROM tbl_sp_assignment AS spas
            JOIN tbl_sp_employee AS spemp 
            ON spas.sp_employee_id = spemp.sp_employee_id
            WHERE spas.appointment_id = %s
        """

        conn = self.connect_mysql()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute(query, (appointment_id,))
            result = cursor.fetchone()
            # Add this line to clear any unread results
            while cursor.nextset():
                pass
            return result
        except mysql.connector.Error as err:
            logger.error(f"Error fetching employee for appointment {appointment_id}: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def fetch_device_token(self, mobile_number):
        """
        Fetch the device token for a given mobile number from tbl_user_devices.
        """
        query = """
            SELECT token FROM tbl_user_devices
            WHERE mobile_number = %s AND active_flag = 1
            ORDER BY updated_at DESC LIMIT 1
        """
        conn = self.connect_mysql()
        if not conn:
            return None

        cursor = conn.cursor()
        try:
            cursor.execute(query, (mobile_number,))
            result = cursor.fetchone()
            # Ensure active_flag is checked (already in SQL), just return token if found
            return result[0] if result else None
        except mysql.connector.Error as err:
            logger.error(f"Error fetching device token for {mobile_number}: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def store_to_mongo(self, appointment, employee):
        """
        Store service start data to MongoDB.
        """
        servicestart_collection = self.mongodb["servicestart"]
        servicestart_collection.insert_one({
            "appointment_id": appointment.get("appointment_id") or appointment.get("sp_appointment_id"),
            "start_date": appointment["start_date"],
            "end_date": appointment["end_date"],
            "start_time": appointment["start_time"],
            "end_time": appointment["end_time"],
            "visit_type": appointment.get("visit_type") or appointment.get("visittype"),
            "employee_id": employee[0] if employee else None,
            "employee_name": employee[1] if employee else None,
            "employee_mobile": employee[2] if employee else None,
            "serviceprovider_mobile": appointment["sp_mobilenumber"],
            "inserted_at": datetime.datetime.now(tz=self.timezone)
        })

    def run(self):
        """
        Runs the appointment watcher indefinitely with 1-minute intervals.
        """
        logger.info("Starting ServiceStartWatcher loop.")
        while True:
            try:
                appointments = self.fetch_appointments_started_10_minutes_ago()

                if not appointments:
                    logger.info("No appointments found.")
                else:
                    for appointment in appointments:
                        appointment_id = appointment.get("appointment_id") or appointment.get("sp_appointment_id")
                        employee = self.fetch_employee_for_appointment(appointment_id)

                        if employee:
                            self.store_to_mongo(appointment, employee)
                            # Fetch device token using service provider's mobile number
                            sp_mobile = appointment["sp_mobilenumber"]
                            device_token = self.fetch_device_token(sp_mobile)
                            if device_token:
                                send_push_notification(
                                    title="ICare",
                                    body="Your service is about to start",
                                    target_device_token=device_token,
                                    data={"appointment_id": str(appointment_id)}
                                )
                                logger.info(f"Notification sent to {sp_mobile}")
                            else:
                                logger.warning(f"No device token found for mobile: {sp_mobile}")
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")

            time.sleep(60)  # Wait for 1 minute before checking again

