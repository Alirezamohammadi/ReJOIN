import psycopg2
import database_env as creds


class Database:

    def __init__(self):
        self.conn = self.connect()

    def connect(self):
        try:
            conn_string = "host=" + creds.PGHOST + " port=" + "5432" + " dbname=" + creds.PGDATABASE + " user=" + creds.PGUSER \
                          + " password=" + creds.PGPASSWORD
            conn = psycopg2.connect(conn_string)
            return conn
        except (Exception, psycopg2.Error) as error:
            print("Error connecting")

    def get_tables_attributes(self):
        cursor = self.conn.cursor()
        q = "SELECT c.table_name, c.column_name FROM information_schema.columns c " \
            "INNER JOIN information_schema.tables t ON c.table_name = t.table_name " \
            "AND c.table_schema = t.table_schema " \
            "AND t.table_type = 'BASE TABLE' " \
            "AND t.table_schema = 'public'"
        cursor.execute(q)
        rows = cursor.fetchall()
        cursor.close()

        tables_attributes = {}
        for table, attribute in rows:
            if table in tables_attributes:
                tables_attributes[table].append(attribute)
            else:
                tables_attributes[table] = [attribute]

        tables = list(tables_attributes.keys())
        attributes = []
        for k in tables_attributes:
            attributes = attributes + [k + "." + v for v in tables_attributes[k]]
        return tables, attributes

    def close(self):
        if self.conn:
            self.conn.close()

    def optimizer_cost(self, query):
        query = "EXPLAIN (FORMAT JSON) " + query
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows[0][0][0]['Plan']['Total Cost']

    def get_query_time(self, query):
        query = "EXPLAIN ANALYZE " + query
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        planning = [float(s) for s in rows[-2][0].split() if self.is_number(s)]
        execution = [float(s) for s in rows[-1][0].split() if self.is_number(s)]
        cursor.close()
        return planning[0], execution[0]

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def get_reward(self, query, episodes, phase):  # get reward from specific episode(tuples of joins)
        query = query  # todo reorder query from tree
        if phase == 1:
            return self.optimizer_cost(query)
        return self.get_query_time(query)[1]
