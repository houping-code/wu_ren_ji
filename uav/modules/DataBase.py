import json
import sqlite3


class DataBase:
    def __init__(self):
        with open("config.json", "r") as fp:
            config = json.loads(fp.read())

        databasePath = config.get("service").get("database").get("path")
        self._conn = sqlite3.connect(databasePath, check_same_thread=False)

        self._cursor = self._conn.cursor()

        self.createTable()

    def createTable(self):
        self.executeSql(
            """CREATE TABLE IF NOT EXISTS `startValueTable` (`clientName` char(5) PRIMARY KEY, `startValue` char(64) 
            UNIQUE NOT NULL)""",
            ())

        self.executeSql(
            """CREATE TABLE IF NOT EXISTS `identityAuthTable` (`clientName` char(7) PRIMARY KEY, `agreeKey` char(32) 
            UNIQUE NOT NULL, `authTime` char(18) NOT NULL)""",
            ())

        self._conn.commit()

    def executeSql(self, sqlCommand, arg):
        self._cursor.execute(sqlCommand, arg)

    def queryStartValue(self, clientName):
        self.executeSql("SELECT startValue FROM startValueTable WHERE clientName = ?", (clientName,))
        result = self._cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def queryAuthTime(self, clientName):
        self.executeSql("SELECT authTime FROM identityAuthTable WHERE clientName = ?", (clientName,))
        result = self._cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def queryIdentityKey(self, clientName):
        self.executeSql("SELECT agreeKey FROM identityAuthTable WHERE clientName = ?", (clientName,))
        result = self._cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def queryAgreeKeyAndAuthTime(self, clientName):
        self.executeSql("SELECT agreeKey, authTime FROM identityAuthTable WHERE clientName = ?", (clientName,))
        result = self._cursor.fetchone()
        if result:
            return result
        else:
            return None

    def insertStartValueTable(self, clientName, startValue):
        self.executeSql("""
               INSERT INTO startValueTable (clientName, startValue)
               VALUES (?, ?)
               """, (clientName, startValue,))
        self._conn.commit()

    def insertIdentityAuthTable(self, clientName, agreeKey, authTime):
        self.executeSql("""
        INSERT INTO identityAuthTable (clientName, agreeKey, authTime)
        VALUES (?, ?, ?)
        """, (clientName, agreeKey, authTime,))
        self._conn.commit()

    def updateAgreeKeyAndAuthTime(self, clientName, agreeKey, authTime):
        self.executeSql("""
                    UPDATE identityAuthTable
                    SET agreeKey = ?, authTime = ?
                    WHERE clientName = ?
                    """, (agreeKey, authTime, clientName,))
        self._conn.commit()

    def updateStartValue(self, clientName, startValue):
        self.executeSql("""
                            UPDATE startValueTable
                            SET startValue = ?
                            WHERE clientName = ?
                            """, (startValue, clientName,))
        self._conn.commit()

    def close(self):
        self._conn.close()
