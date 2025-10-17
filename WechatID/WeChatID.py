
import time
import requests
import pymysql 
import logging
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class User:
    Name: str
    Email: str
    WechatID: Optional[str]


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

UserList: List[User] = []


class WeChatID:

    def __init__(
        self,
        DBConfig: dict,
        NameList: Optional[List[str]] = None,
        EmailList: Optional[List[str]] = None,
        WechatConfig: Optional[dict] = None,
    ):
        self.DBConn = None
        self.WechatConfig = WechatConfig if WechatConfig else {}
        self.DBConfig = DBConfig if DBConfig else {}
        self.NameList = NameList if NameList else []
        self.EmailList = EmailList if EmailList else []
        self.UserList = (
            [
                User(name=name, email=email, WechatID=None)
                for name, email in zip(self.NameList, self.EmailList)
            ]
            if self.NameList and self.EmailList
            else []
        )
        self.ExistingEmail = None
        self.AccessToken = self.__get_access_token() if self.WechatConfig else None

    def __get_access_token(self):
        url = self.WechatConfig.get("get_access_token_url").format(
            self.WechatConfig.get("corpid"), self.WechatConfig.get("secret")
        )
        try:
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            return res.json().get("access_token")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get access token: {e}")
            return None

    def __get_wechat_id(self, user: User):
        if not self.AccessToken or not self.WechatConfig.get("url"):
            logging.error("Cannot get WechatID due to missing access token or url.")
            return None

        url = self.WechatConfig.get("url").format(self.AccessToken)
        try:
            res = requests.post(
                url, json={"email": user.Email, "email_type": 1}, timeout=5
            )
            res.raise_for_status()
            data = res.json()
            return data.get("userid")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get wechat_id for {user.Email}: {e}")
            return None
        except Exception as e:
            logging.error(f"API response error for {user.Email}: {e}")
            return None

    def get_wechat_id(self):
        if not self.ExistingEmail:
            self.ExistingEmail = self.__get_existing_email()
        if not self.AccessToken:
            logging.error("Cannot get Wechat IDs due to missing access token.")
            return False

        for user in self.UserList:
            if user.Email in self.ExistingEmail:
                logging.info(
                    f"Skipping {user.Name, user.Email} because it already exists in the database."
                )
                continue
            WechatID = self.__get_wechat_id(user)
            if WechatID:
                user.WechatID = WechatID
            print(user.Name, user.Email, user.WechatID)
            print("-" * 100)
            time.sleep(1)
        return self.UserList

    def __get_existing_email(self):
        conn = self.__connect_db()
        if not conn:
            logging.error("Cannot connect to database, skipping ExistingEmail.")
            return set()

        sql = "SELECT email FROM users WHERE wxid IS NOT NULL"
        ExistingEmail = set()

        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()

                for row in results:
                    ExistingEmail.add(row[0])

            logging.info(f"Successfully queried {len(ExistingEmail)} ExistingEmail.")
            return ExistingEmail

        except pymysql.MySQLError as e:
            logging.error(f"Failed to query existing emails: {e}")
            return set()
        finally:
            if conn:
                conn.close()
                self.db_conn = None

    def __connect_db(self):
        if self.DBConn is None:
            try:
                self.DBConn = pymysql.connect(**self.DBConfig)
                logging.info("Database connection successful.")
            except pymysql.MySQLError as e:
                logging.error(f"Database connection failed: {e}")
                self.DBConn = None
        return self.DBConn

    def SaveToDB(self):
        if not self.DBConn:
            logging.error("Cannot connect to database, skipping save to db.")
            return False

        sql = """
            INSERT INTO users (name, email, wxid) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name), 
                wxid = VALUES(wxid)
        """
        data_to_insert = []
        for user in self.UserList:
            if user.WechatID:
                data_to_insert.append((user.Name, user.Email, user.WechatID))

        if not data_to_insert:
            logging.warning("No valid user data with WechatID to insert.")
            return True

        try:
            with self.DBConn.cursor() as cursor:
                cursor.executemany(sql, data_to_insert)
            self.DBConn.commit()
            logging.info(
                f"Successfully saved {cursor.rowcount} records to the database."
            )
            return True
        except pymysql.MySQLError as e:
            self.DBConn.rollback()
            logging.error(f"Database write failed: {e}")
            return False
        finally:
            if self.DBConn:
                self.DBConn.close()

    def QueryFromDB(
        self,
        ChineseName: Optional[str] = None,
        Email: Optional[str] = None,
    ) -> Optional[List[User]]:
        if not self.DBConn:
            self.DBConn = self.__connect_db()
        if not self.DBConn:
            logging.error("Cannot connect to database, skipping query from db.")
            return None

        if not ChineseName and not Email:
            logging.error("No ChineseName or Email provided, skipping query from db.")
            return None

        cursor = self.DBConn.cursor()
        try:
            sql = "SELECT name, email, wxid FROM users"
            if ChineseName and Email:
                sql += " WHERE name = %s AND email = %s"
                cursor.execute(sql, (ChineseName, Email))
            elif ChineseName:
                sql += " WHERE name = %s"
                cursor.execute(sql, (ChineseName,))
            elif Email:
                sql += " WHERE email = %s"
                cursor.execute(sql, (Email,))
            return [
                User(Name=result[0], Email=result[1], WechatID=result[2])
                for result in cursor.fetchall()
            ]
        except pymysql.MySQLError as e:
            logging.error(f"Database query failed: {e}")
            return None
        finally:
            cursor.close()



