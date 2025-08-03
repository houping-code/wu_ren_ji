import pymysql
from pymysql.err import MySQLError
import json
from . import logger

with open("config.json", "r") as fp:
    config = json.loads(fp.read())
    host = config.get("database").get("host")
    port = config.get("database").get("port")
    user = config.get("database").get("user")
    password = config.get("database").get("password")
    keyDatabase = config.get("database").get("keyDatabase")


def connect(database):
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )

    return connection


def executeSqlCommand(database, command, arg):
    """
    使用提供的数据库凭证连接到MySQL服务器并执行传入的MySQL命令。

    参数:
        command (str): 要执行的MySQL命令。
        params (tuple, list or dict, optional): 命令参数。默认为None。

    返回:
        tuple: 查询结果和受影响的行数。
    """
    connection = connect(database)

    try:
        with connection.cursor() as cursor:
            cursor.execute(command, arg)
            result = cursor.fetchall()

        # 提交更改
        connection.commit()

        return result
    except MySQLError as e:
        logger.error(f"执行mysql命令时出错: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        connection.close()


def queryIdentityKey(clientName):
    result = executeSqlCommand(keyDatabase, "SELECT agreeKey FROM identityAuthTable WHERE clientName = %s",
                               (clientName,))
    if result:
        return result[0][0]
    else:
        return None
