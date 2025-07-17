import datetime as dt
import cx_Oracle
import psycopg
from psycopg.rows import dict_row
from psycopg import sql

class DemandForecastService:
    def __init__(self, conString:str, host:str, port:str, dbName:str, user:str, password:str):
        self.connectionString= conString
        self.host= host
        self.port= port
        self.dbName= dbName
        self.user= user
        self.password= password
        self.connection = None
        self.postgresqlConnection =None

    def connect(self):
        """Establish a mis database connection."""
        if self.connection:
            self.disconnect()
        try:
            self.connection = cx_Oracle.connect(self.connectionString)
            # loggerr.info("Connected to Oracle MIS DB")
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            self.connection = None

    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            # loggerr.info("Closing Oracle (MIS) DB connection")
            self.connection.close()
            self.connection = None
    
    def connectPostgresqlDb(self):
        """Establish a postgresql database connection."""
        if self.postgresqlConnection:
            self.disconnectPostgresqlDb()
        try:
            self.postgresqlConnection = psycopg.connect(dbname=self.dbName,
                            user=self.user,
                            password=self.password,
                            host=self.host,
                            port=self.port, row_factory=dict_row)
            # loggerr.info("Connected to PostgreSql RA DB")
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            self.postgresqlConnection = None
    
    def disconnectPostgresqlDb(self):
        """Close the PostgreSQL database connection."""
        if self.postgresqlConnection:
            # loggerr.info("Closing Postgres (RA) DB connection")
            try:
                self.postgresqlConnection.commit()
            except Exception as e:
                # loggerr.warning(f"Postgres commit failed before closing: {str(e)}")
                self.postgresqlConnection.rollback()
            finally:
                self.postgresqlConnection.close()
                self.postgresqlConnection = None
            
    def fetchForecastData(self, start_timestamp: dt.datetime, end_timestamp: dt.datetime, entity_tag: str, revision_no: str):
        """
        Fetch data from the FORECAST_REVISION_STORE table based on timestamps, entity_tag, and revision_no.
        """
        if not self.connection:
            print("No active database connection.")
            return []

        query = """
            SELECT TIME_STAMP,ENTITY_TAG, REVISION_NO, FORECASTED_DEMAND_VALUE 
            FROM FORECAST_REVISION_STORE 
            WHERE TIME_STAMP BETWEEN :start_ts AND :end_ts 
              AND ENTITY_TAG = :entity_tag 
              AND REVISION_NO = :revision_no
              order by ENTITY_TAG,TIME_STAMP
        """

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, {
                "start_ts": start_timestamp,
                "end_ts": end_timestamp,
                "entity_tag": entity_tag,
                "revision_no": revision_no
            })

            rows = cursor.fetchall()

            # Process the result
            demandForecastData = [
                {
                    "timestamp": row[0],
                    "entity_tag": row[1],
                    "revision_no": row[2],
                    "forecasted_demand_value": row[3]
                }
                for row in rows
            ]

            return demandForecastData

        except Exception as e:
            print(f"Error during data fetch: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()

    def fetchLoadSheddingData(self, start_timestamp: dt.datetime, end_timestamp: dt.datetime, stateTag:str):
        """
        Fetch particular state Load shedding data  between starttime and endtime
        """
        if not self.postgresqlConnection:
            print("No active postgres database connection.")
            return []

        # Compose SQL with safe identifiers for table names
        query = sql.SQL("""SELECT *
            FROM state_load_shedding sls
            WHERE 
                sls.timestamp BETWEEN %(start_time)s AND %(end_time)s
                AND sls.state_code = %(state_tag)s
                ORDER BY sls.timestamp;
        """)

        cursor = self.postgresqlConnection.cursor()

        try:
            cursor.execute(query, {"start_time": start_timestamp,"end_time": end_timestamp,"state_tag": stateTag})
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching mapping data: {str(e)}")
            return []
        finally:
            cursor.close()

