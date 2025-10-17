import requests
import json
from dataclasses import dataclass
from typing import Optional, List
from dataclasses import asdict
import base64
import hashlib


@dataclass
class ContentData:
    content: str
    mentioned_list: List[str]
    mentioned_mobile_list: List[str]


@dataclass
class TextInfo:
    text: ContentData
    msgtype: str = "text"


@dataclass
class MarkdownData:
    content: str


@dataclass
class MDTextInfo:
    markdown: MarkdownData
    msgtype: str = "markdown"


@dataclass
class MDInfo:
    markdown_v2: MarkdownData
    msgtype: str = "markdown_v2"


@dataclass
class ImageData:
    base64: str
    md5: str


@dataclass
class ImageInfo:
    image: ImageData
    msgtype: str = "image"


class ChatRoomBot:
    def __init__(
        self,
        webhook: str,
    ):
        self.webhook = webhook

    def __push(
        self,
        data: dict,
    ) -> str:
        try:
            res = requests.post(
                self.webhook,
                headers={
                    "Content-Type": "application/json",
                },
                json=data,
            )
            res.raise_for_status()
            try:
                responseJson = res.json()
                if responseJson.get("errcode") == 0:
                    return "Push success"
                else:
                    return f"Push failed: {responseJson.get('errmsg', 'Unknown API Error')}"
            except (json.JSONDecodeError, AttributeError):
                return f"Push success, but response body is unexpected: {res.text}"
        except requests.exceptions.RequestException as e:
            return f"Push failed: HTTP Request Error or Timeout ({e})"

    def PushText(
        self,
        Content: str,
        All: Optional[bool] = False,
        IDList: Optional[List[str]] = None,
        MobileList: Optional[List[str]] = None,
    ) -> str:
        mentionedList = IDList if IDList else []
        mentionedMobileList = MobileList if MobileList else []
        if All:
            mentionedMobileList.append(
                "@all"
            ) if mentionedMobileList else mentionedMobileList.append("@all")
        contextData = ContentData(
            mentioned_list=mentionedList,
            mentioned_mobile_list=mentionedMobileList,
            content=Content,
        )
        textInfo = TextInfo(text=contextData)
        data = asdict(textInfo)
        result = self.__push(data=data)
        return result

    def PushMarkdown(
        self,
        Content: str,
        IDList: Optional[List[str]] = None,
    ) -> str:
        mentionedStr = "<@" + "><@".join(IDList) + ">" if IDList else ""
        if mentionedStr:
            markdown = MarkdownData(content=mentionedStr + "\n" + Content)
            mdTextInfo = MDTextInfo(markdown=markdown)
            data = asdict(mdTextInfo)
        else:
            markdown = MarkdownData(content=Content)
            mdInfo = MDInfo(markdown_v2=markdown)
            data = asdict(mdInfo)
        result = self.__push(data=data)
        return result

    def PushImage(
        self,
        ImageBytes: bytes,
    ) -> str:
        base64Data = base64.b64encode(ImageBytes).decode("utf-8")
        md5Hash = hashlib.md5(ImageBytes).hexdigest()
        imageData = ImageData(
            base64=base64Data,
            md5=md5Hash,
        )
        imageInfo = ImageInfo(image=imageData)
        Data = asdict(imageInfo)
        result = self.__push(data=Data)
        return result



