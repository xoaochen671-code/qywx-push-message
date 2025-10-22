from turtle import update
import requests
import urllib.parse
import pymysql
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Token:
    access_token: str
    refresh_token: str
    access_token_expires_at: str = None
    refresh_token_expires_at: str = None
    access_token_expires_at_dt :datetime = None
    refresh_token_expires_at_dt :datetime = None

class FSToken:
    def __init__(
        self,
        DBConfig: dict,
        FSConfig: dict,
    ):
        self.app_id = FSConfig["appid"]
        self.app_secret = FSConfig["secret"]
        self.redirect_url = FSConfig["redirecturl"]
        self.scope = FSConfig["scope"]
        self.DBConfig = DBConfig
        self.DBConn = None
        self.update = "update token set access_token = %s, access_token_expires_at = %s, refresh_token = %s, refresh_token_expires_at = %s where platform = 'feishu' and user = 'yangxiaochen'"

    def __connect_db(self):
        if self.DBConn is None:
            try:
                self.DBConn = pymysql.connect(**self.DBConfig)
            except pymysql.MySQLError as e:
                raise f"Database connection failed: {e}"

    def __jsonTotoken(self, res: dict) -> Token:
        access_token = res.get("access_token")
        expires_in = res.get("expires_in")
        refresh_token = res.get("refresh_token")
        refresh_token_expires_in = res.get("refresh_token_expires_in")

        expires_at = datetime.now() + timedelta(seconds=expires_in)
        expires_at_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
        refresh_token_expires_at = datetime.now() + timedelta(
            seconds=refresh_token_expires_in
        )
        refresh_token_expires_at_str = refresh_token_expires_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return Token(
            access_token=access_token,
            access_token_expires_at=expires_at_str,
            refresh_token=refresh_token,
            refresh_token_expires_at=refresh_token_expires_at_str,
        )

    def get_url(self):
        url = (
            "https://accounts.feishu.cn/open-apis/authen/v1/authorize?"
            + urllib.parse.urlencode(
                {
                    "client_id": self.app_id,
                    "redirect_uri": self.redirect_url,
                    "scope": self.scope,
                },
                quote_via=urllib.parse.quote,
            )
        )
        return url

    def __executeToken(self, token: Token):
        try:
            with self.DBConn.cursor() as cursor:
                cursor.execute(
                    self.update,
                    (
                        token.access_token,
                        token.access_token_expires_at,
                        token.refresh_token,
                        token.refresh_token_expires_at,
                    ),
                )
            self.DBConn.commit()
        except Exception as e:
            self.DBConn.rollback()
            raise f"Database update failed: {e}"
        finally:
            if self.DBConn:
                self.DBConn.close()

    def create_token(
        self,
        code: str,
    ):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        user_token_url = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"

        if not self.DBConn:
            self.__connect_db()

        res = requests.post(
            url=user_token_url,
            headers=headers,
            json={
                "grant_type": "authorization_code",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
                "redirect_uri": self.redirect_url,
                "scope": self.scope,
            },
        ).json()
        token = self.__jsonTotoken(res)
        self.__executeToken(token=token)
        return token

    def get_token(self) -> str:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        user_token_url = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"

        if not self.DBConn:
            self.__connect_db()

        query = "select access_token,access_token_expires_at,refresh_token,refresh_token_expires_at from token where platform = 'feishu' and user = 'yangxiaochen' order by id desc limit 1"
        try:
            with self.DBConn.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchone()
            token = Token(
                access_token=data[0],
                access_token_expires_at_dt=data[1],
                refresh_token=data[2],
                refresh_token_expires_at_dt=data[3],
            )
        except Exception as e:
            raise f"Error: unable to fetch data: {e}"
        if (
            token.access_token_expires_at_dt is None
            or datetime.now() + timedelta(hours=1) > token.access_token_expires_at_dt
        ):
            res = requests.post(
                url=user_token_url,
                headers=headers,
                json={
                    "grant_type": "refresh_token",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "refresh_token": token.refresh_token,
                },
            ).json()
            token = self.__jsonTotoken(res)
            self.__executeToken(token=token)
        return token.access_token
