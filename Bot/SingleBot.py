import requests
import json
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class TextData:
    content: str


@dataclass
class TextInfo:
    text: TextData
    agentid: int
    touser: str
    msgtype: Optional[str] = "text"
    enable_duplicate_check: Optional[int] = 1
    duplicate_check_interval: Optional[int] = 600


@dataclass
class MarkdownData:
    content: str


@dataclass
class MDInfo:
    markdown: MarkdownData
    agentid: int
    touser: str
    msgtype: Optional[str] = "markdown"
    enable_duplicate_check: Optional[int] = 1
    duplicate_check_interval: Optional[int] = 600


class SingleBot:
    def __init__(
        self,
        CorpID: str = "ww833f9e9fa0a48ec5",
        Corpsecret: str = "ZZwebvmiAs51CUHJaOFhs31-fsd7YhXKKlTOndLih4I",
        AgentID: str = "1000158",
    ):
        self.access_token = self.__get_access_token(
            Corpid=CorpID,
            Corpsecret=Corpsecret,
        )
        self.AgentID = AgentID

    def __get_access_token(
        self,
        Corpid: str,
        Corpsecret: str,
    ):
        res = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}".format(
                Corpid, Corpsecret
            )
        )
        return res.json()["access_token"]

    def __push(
        self,
        data: dict,
    ) -> str:
        try:
            res = requests.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(
                    self.access_token
                ),
                json=data,
            )
            res.raise_for_status()
            try:
                responseJson = res.json()
                if responseJson.get("errcode") == 0:
                    return "Push success"
                else:
                    return f"Push failed: {responseJson.get('errmsg', 'Unknown Access Token Error')}"
            except (json.JSONDecodeError, AttributeError):
                return f"Push success, but response body is unexpected: {res.text}"
        except requests.exceptions.RequestException as e:
            return f"Push failed: HTTP Request Error or Timeout ({e})"

    def PushMarkdown(
        self,
        Content: str,
        Touser: Optional[List[str]],
    ):
        markdownData = MarkdownData(content=Content)
        markdownInfo = MDInfo(
            markdown=markdownData,
            agentid=self.AgentID,
            touser=("|".join(Touser) if Touser else "all"),
        )
        data = asdict(markdownInfo)
        result = self.__push(data)
        return result
