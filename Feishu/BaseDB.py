import requests
from typing import List, Literal, Dict
from dataclasses import dataclass, field
from enum import Enum
import urllib.parse


class StringOperator(str, Enum):
    IS = "is"
    IS_EMPTY = "isEmpty"
    IS_NOT_EMPTY = "isNotEmpty"
    IS_GREATER = "isGreater"
    IS_LESS = "isLess"
    """-------------------------------- 不支持日期字段 ------------------------------"""
    IS_NOT = "isNot"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "doesNotContain"
    IS_GREATER_EQUAL = "isGreaterEqual"
    IS_LESS_EQUAL = "isLessEqual"


@dataclass
class Condition:
    field_name: str
    operator: StringOperator = field(
        metadata={
            "description": "表示条件运算符，必须是 StringOperator 中的一个值",
            "可选值": [op.value for op in StringOperator],
        }
    )
    value: str | None = field(
        default=None,
        metadata={
            "description": "用于比较的值。当运算符为 'isEmpty'/'isNotEmpty' 时，此值通常为 None。"
        },
    )


@dataclass
class Filter:
    conditions: List[Condition] = field(
        metadata={"description": "筛选条件集合"},
    )
    conjunction: Literal["and", "or"] = field(
        default="and",
        metadata={"description": "表示条件之间的逻辑连接词, 只能是 'and' 或 'or'"},
    )


class DBOperation:
    def __init__(self, AccessToken, APPToken):
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {AccessToken}",
        }
        self.apptoken = APPToken
        pass

    def __query(
        self,
        TableID: str,
        FieldNames: List[str],
        Filter: Filter = None,
        PageToken: str = None,
    ) -> (str, List[Dict]):
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records/search?".format(
            self.apptoken, TableID
        )
        if PageToken:
            url += urllib.parse.urlencode(
                {"page_token": PageToken}, quote_via=urllib.parse.quote
            )
        payload = {"field_names": FieldNames, "filter": Filter}
        res = requests.post(url=url, headers=self.headers, json=payload)
        res.raise_for_status()

        resJson = res.json()
        if resJson.get("code") != 0:
            return res.text

        pageToken = None
        if resJson.get("data").get("has_more"):
            pageToken = res.json().get("data").get("page_token")

        return (pageToken, resJson.get("data").get("items"))

    def Query(self, TableID: str, FieldNames: List[str], Filter: Filter = None):
        ResData = []
        pageToken, data = self.__query(
            TableID=TableID, FieldNames=FieldNames, Filter=Filter
        )
        ResData.extend(data)

        while pageToken:
            pageToken, data = self.__query(
                TableID=TableID,
                FieldNames=FieldNames,
                Filter=Filter,
                PageToken=pageToken,
            )
            ResData.extend(data)
        return {"data": ResData, "total": len(ResData)}

    def __write(self, TableID: str, Records: List[Dict]):
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records/batch_create?".format(
            self.apptoken, TableID
        )
        payload = {"records": Records}
        res = requests.post(url=url, headers=self.headers, json=payload)
        res.raise_for_status()

        resJson = res.json()
        if resJson.get("code") != 0:
            return res.text

        return "success"

    def Write(self, TableID: str, Records: List[Dict]):
        batch_size = 500
        batches = [
            Records[i : i + batch_size] for i in range(0, len(Records), batch_size)
        ]
        for batch in batches:
            msg = self.__write(TableID=TableID, Records=batch)
            if msg != "success":
                return msg
        return "success"

    def Reset(self, TableID: str, Fields: List[str] = None):
        query_result = self.Query(TableID=TableID, FieldNames=[])
        IDs = [i["record_id"] for i in query_result["data"]]

        if not IDs:
            return "success"

        batch_size = 500
        batches = [IDs[i : i + batch_size] for i in range(0, len(IDs), batch_size)]

        for batch in batches:
            url = "https://open.feishu.cn/open-apis/bitable/v1/apps/{}/tables/{}/records/batch_delete".format(
                self.apptoken, TableID
            )
            res = requests.post(url=url, headers=self.headers, json={"records": batch})
            res.raise_for_status()

            resJson = res.json()
            if resJson.get("code") != 0:
                return res.text

        return "success"
