import datetime as dt
import psycopg
from psycopg.rows import dict_row
from psycopg import sql

class StateDcDataService:
    def __init__(self, host, port, dbName, user, password):
        self.host= host
        self.port= port
        self.dbName= dbName
        self.user= user
        self.password= password
        self.connection = None

    def connect(self):
        """Establish a postgresql database connection."""
        try:
            self.connection = psycopg.connect(dbname=self.dbName,
                            user=self.user,
                            password=self.password,
                            host=self.host,
                            port=self.port, row_factory=dict_row)
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            self.connection = None
    
    def disconnect(self):
        """Close the PostgreSQL database connection."""
        if self.connection:
            self.connection.close()
    
    def fetchMappingTblData(self):
        """Fetch  data from the mapping_table."""
        if not self.connection:
            print("No active database connection.")
            return []

        query = "SELECT id, plant_name, unit_name, state, fuel_type, installed_capacity, aux_consumption, outage_unit_name FROM public.mapping_table"
        cursor = self.connection.cursor()

        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching mapping data: {str(e)}")
            return []
        finally:
            cursor.close()
    
    def fetchStateDcData(self, revisionTypeTableName, plantIdList:list, startTime:dt.datetime, endTime:dt.datetime):
        """Fetch  state dc and normatice dc data from plantId list and between starttime and endtime"""
        if not self.connection:
            print("No active database connection.")
            return []

        # Compose SQL with safe identifiers for table names
        query = sql.SQL("""SELECT dadd.date_time, SUM(dadd.dc_data) AS sum_dc, SUM(dadd.dc_data * (1 - COALESCE(mt.aux_consumption, 0) / 100)) AS sum_normative_dc
            FROM {dc_table} dadd JOIN mapping_table mt ON dadd.plant_id = mt.id
            WHERE 
                dadd.date_time BETWEEN %(start_time)s AND %(end_time)s
                AND dadd.plant_id = ANY(%(plant_ids)s)
            GROUP BY dadd.date_time ORDER BY dadd.date_time;
        """).format(dc_table=sql.Identifier(revisionTypeTableName))

        cursor = self.connection.cursor()

        try:
            cursor.execute(query, {"start_time": startTime,"end_time": endTime,"plant_ids": plantIdList})
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching mapping data: {str(e)}")
            return []
        finally:
            cursor.close()

