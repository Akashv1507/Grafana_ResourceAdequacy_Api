import datetime as dt
import psycopg
from psycopg.rows import dict_row

class OutageSummaryService:
    def __init__(self, host:str, port:str, dbName:str, user:str, password:str):
        
        self.host= host
        self.port= port
        self.dbName= dbName
        self.user= user
        self.password= password
        self.postgresqlConnection =None

   
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
            
    
    def fetchOutageSummaryData(self, startTimestamp: dt.datetime, endTimestamp: dt.datetime, stateName=None, classification=None, stationType=None, shutdownType=None, shutdownTag=None ):
        """
        Fetch outage summary data including(state_name, classification, station_type, shutdown_type, shutdown_tag, outage_val)  between starttime and endtime
        """
        if not self.postgresqlConnection:
            print("No active postgres database connection.")
            return []
        # Base query
        query = """
            SELECT time_stamp, state_name, classification, station_type, shutdown_type, shutdown_tag, outage_val
            FROM public.gen_all_outage_type_summary
            WHERE time_stamp BETWEEN %(start_time)s AND %(end_time)s
        """
        # Parameters list (start_time & end_time are mandatory)
        params = {"start_time":startTimestamp, "end_time":endTimestamp}

        # Add optional filters dynamically
        if stateName is not None:
            query += " AND state_name = %(state_name)s"
            params.update({"state_name": stateName})

        if classification is not None:
            query += " AND classification = %(classification)s"
            params.update({"classification": classification})

        if stationType is not None:
            query += " AND station_type = %(station_type)s"
            params.update({"station_type": stationType})

        if shutdownType is not None:
            query += " AND shutdown_type = %(shutdown_type)s"
            params.update({"shutdown_type": shutdownType})

        if shutdownTag is not None:
            query += " AND shutdown_tag = %(shutdown_tag)s"
            params.append({"shutdown_tag": shutdownTag})

        #  add ORDER BY if needed
        query += " ORDER BY time_stamp, state_name, classification, station_type, shutdown_type, shutdown_tag"
        cursor = self.postgresqlConnection.cursor()

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching mapping data: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()

