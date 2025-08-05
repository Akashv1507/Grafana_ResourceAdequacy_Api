import datetime as dt
import psycopg
from psycopg.rows import dict_row
from psycopg import sql

class StateDeficitDataService:
    def __init__(self, host, port, dbName, user, password):
        self.host= host
        self.port= port
        self.dbName= dbName
        self.user= user
        self.password= password
        self.connection = None

    def connect(self):
        """Establish a postgresql database connection."""
        if self.connection:
            self.disconnect()  
        try:
            self.connection = psycopg.connect(dbname=self.dbName,
                            user=self.user,
                            password=self.password,
                            host=self.host,
                            port=self.port, row_factory=dict_row)
            # loggerr.info("Connected to PostgreSql RA DB")
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            self.connection = None
    
    def disconnect(self):
        """Close the PostgreSQL database connection."""
        if self.connection:
            # loggerr.info("Closing Postgres (RA) DB connection")
            try:
                self.connection.commit()
            except Exception as e:
                # loggerr.warning(f"Postgres commit failed before closing: {str(e)}")
                self.connection.rollback()
            finally:
                self.connection.close()
                self.connection = None

    
    def fetchDeficitRevisionNo(self, targteDate: dt.date, defType:str ):
        """Fetch state Deficit revision no deficit_revision_metadata tbl for target date"""
        
        if not self.connection:
            print("No active database connection.")
            return []
        # Compose SQL with safe identifiers for table names
        query = sql.SQL("""select drm.def_rev_no, drm.time from deficit_revision_metadata drm where drm.date =%(target_date)s and drm.def_type = %(def_type)s order  by drm.def_rev_no;""")

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, {"target_date": targteDate,"def_type": defType})
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching outage and dc summary data data: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()

    def fetchStateDeficitData(self, startTime:dt.datetime, endTime:dt.datetime, stateName:str, revisionNo:str ):
        """Fetch state Deficit data from state_deficit_data tbl between starttime and endtime"""
        
        if not self.connection:
            print("No active database connection.")
            return []
        # Compose SQL with safe identifiers for table names
        query = sql.SQL("""select * from state_deficit_data sdd
                            where sdd.timestamp between %(start_time)s and %(end_time)s and sdd.state_key = %(state_name)s 
                            and  sdd.def_revision_no = %(revision_no)s""")

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, {"start_time": startTime,"end_time": endTime, 'state_name': stateName, 'revision_no':revisionNo })
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching deficit data: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()

    def fetchAllParamsRevisionNo(self, targteDate: dt.date, defRevNo:str ):
        """Fetch all other parameters like(Demand Fore, Re forecast, SDl, etc ) revision no for particular deficit revision NO from deficit_revision_metadata tbl for target date"""
        
        if not self.connection:
            print("No active database connection.")
            return {}
        # Compose SQL with safe identifiers for table names
        query = sql.SQL("""select * from deficit_revision_metadata drm where drm.date =%(target_date)s and drm.def_rev_no = %(def_rev_no)s order by drm.def_rev_no;""")

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, {"target_date": targteDate, "def_rev_no": defRevNo})
            row = cursor.fetchone()
            return row
        except Exception as e:
            print(f"Error fetching outage and dc summary data data: {str(e)}")
            return {}
        finally:
            if cursor:
                cursor.close()