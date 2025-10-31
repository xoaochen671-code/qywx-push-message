from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Literal
import Bot.RoomBot as RoomBot
import Bot.SingleBot as SingleBot
import WechatID.WeChatID as WeChatID
import AuthToken.FeishuToken as FeishuToken
import Feishu.BaseDB as FeishuDB
import uvicorn
import base64
import configparser
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum

origins = ["*"]


class TextInfo(BaseModel):
    Webhook: str = Field(..., description="目标 Webhook URL")
    Content: str = Field(..., description="消息文本内容")
    AllMention: Optional[bool] = Field(
        False, alias="All", description="是否提及所有人 (@all)"
    )
    IDList: Optional[List[str]] = Field(
        None, alias="IDList", description="提及的用户 ID 列表"
    )
    MobileList: Optional[List[str]] = Field(
        None, alias="MobileList", description="提及的手机号列表"
    )

    model_config = ConfigDict(populate_by_name=True)


class MDInfo(BaseModel):
    Webhook: str = Field(..., description="目标 Webhook URL")
    Content: str = Field(..., description="消息文本内容")
    IDList: Optional[List[str]] = Field(
        None, alias="IDList", description="提及的用户 ID 列表"
    )

    model_config = ConfigDict(populate_by_name=True)


class ImageInfo(BaseModel):
    Webhook: str = Field(..., description="目标 Webhook URL")
    ImageBase64: str = Field(..., description="图片的 Base64 编码字符串")

    @field_validator("ImageBase64")
    @classmethod
    def must_be_valid_base64(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("ImageBase64 字段必须是有效的 Base64 编码字符串")
        return v

    model_config = ConfigDict(populate_by_name=True)


class Text(BaseModel):
    Content: str = Field(..., description="消息文本内容")
    Touser: Optional[List[str]] = Field(
        None, alias="Touser", description="发送的用户 ID 列表"
    )
    CorpID: str = Field("ww833f9e9fa0a48ec5", alias="CorpID")
    Corpsecret: str = Field(
        "ZZwebvmiAs51CUHJaOFhs31-fsd7YhXKKlTOndLih4I", alias="Corpsecret"
    )
    AgentID: str = Field("1000158", alias="AgentID")

    model_config = ConfigDict(populate_by_name=True)


class MD(BaseModel):
    Content: str = Field(..., description="Markdown消息文本内容")
    Touser: Optional[List[str]] = Field(
        None, alias="Touser", description="发送的用户 ID 列表"
    )
    CorpID: str = Field("ww833f9e9fa0a48ec5", alias="CorpID")
    Corpsecret: str = Field(
        "ZZwebvmiAs51CUHJaOFhs31-fsd7YhXKKlTOndLih4I", alias="Corpsecret"
    )
    AgentID: str = Field("1000158", alias="AgentID")

    model_config = ConfigDict(populate_by_name=True)


class StringOperatorEnum(str, Enum):
    IS = "is"
    IS_EMPTY = "isEmpty"
    IS_NOT_EMPTY = "isNotEmpty"
    IS_GREATER = "isGreater"
    IS_LESS = "isLess"
    IS_NOT = "isNot"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "doesNotContain"
    IS_GREATER_EQUAL = "isGreaterEqual"
    IS_LESS_EQUAL = "isLessEqual"


class ConditionModel(BaseModel):
    field_name: str = Field(..., description="字段名称")
    operator: StringOperatorEnum = Field(..., description="条件运算符")
    value: Optional[str] = Field(
        None, description="用于比较的值（isEmpty/isNotEmpty时可为空）"
    )


class FilterModel(BaseModel):
    conjunction: Literal["and", "or"] = Field("and", description="条件之间的逻辑连接词")
    conditions: List[ConditionModel] = Field(..., description="筛选条件集合")


class QueryRequest(BaseModel):
    APPToken: str = Field(..., description="飞书应用Token")
    TableID: str = Field(..., description="多维表格的table_id")
    FieldNames: List[str] = Field(..., description="需要查询的字段名称列表")
    Filter: Optional[FilterModel] = Field(None, description="筛选条件")


class WriteRequest(BaseModel):
    APPToken: str = Field(..., description="飞书应用Token")
    TableID: str = Field(..., description="多维表格的table_id")
    Records: List[dict] = Field(
        ...,
        description="要写入的记录列表，每条记录是一个字典，包含 fields 字段",
        example=[{"fields": {"字段1": "值1", "字段2": "值2"}}],
    )


class ResetRequest(BaseModel):
    APPToken: str = Field(..., description="飞书应用Token")
    TableID: str = Field(..., description="多维表格的table_id")


app = FastAPI(title="Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_config():
    config_parser = configparser.ConfigParser()
    config_parser.read("config.ini")

    db_config = {
        "host": config_parser.get("database", "host"),
        "port": int(config_parser.get("database", "port")),
        "user": config_parser.get("database", "user"),
        "password": config_parser.get("database", "password"),
        "database": config_parser.get("database", "database"),
        "charset": config_parser.get("database", "charset"),
    }
    return db_config


def get_feishu_config():
    config_parser = configparser.ConfigParser()
    config_parser.read("config.ini")

    feishu_config = {
        "appid": config_parser.get("feishu_config", "appid"),
        "scope": config_parser.get("feishu_config", "scope"),
        "secret": config_parser.get("feishu_config", "secret"),
        "redirecturl": config_parser.get("feishu_config", "redirecturl"),
    }
    return feishu_config


@app.post("/api/chatroomPushText", summary="发送Text消息")
async def pushTextInfo(RequestData: TextInfo):
    bot_client = RoomBot.ChatRoomBot(webhook=RequestData.Webhook)

    result = bot_client.PushText(
        Content=RequestData.Content,
        All=RequestData.AllMention,
        IDList=RequestData.IDList,
        MobileList=RequestData.MobileList,
    )

    if "success" in result.lower():
        return {"status": "ok", "message": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@app.post("/api/chatroomPushMD", summary="发送Markdown消息")
async def pushMDInfo(RequestData: MDInfo):
    bot_client = RoomBot.ChatRoomBot(webhook=RequestData.Webhook)

    result = bot_client.PushMarkdown(
        Content=RequestData.Content,
        IDList=RequestData.IDList,
    )

    if "success" in result.lower():
        return {"status": "ok", "message": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@app.post("/api/chatroomPushImage", summary="发送图片消息")
async def pushImageInfo(RequestData: ImageInfo):
    bot_client = RoomBot.ChatRoomBot(webhook=RequestData.Webhook)
    base64BytesForm = RequestData.ImageBase64.encode("utf-8")
    originalImageBytes = base64.b64decode(base64BytesForm)
    result = bot_client.PushImage(originalImageBytes)
    if "success" in result.lower():
        return {"status": "ok", "message": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@app.post("/api/PushText", summary="发送Text消息")
async def PushText(RequestData: Text):
    bot_client = SingleBot.SingleBot(
        CorpID=RequestData.CorpID,
        Corpsecret=RequestData.Corpsecret,
        AgentID=RequestData.AgentID,
    )
    result = bot_client.PushText(
        Content=RequestData.Content,
        Touser=RequestData.Touser,
    )
    if "success" in result.lower():
        return {"status": "ok", "message": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@app.post("/api/PushMD", summary="发送Markdown消息")
async def PushMarkdown(RequestData: MD):
    bot_client = SingleBot.SingleBot(
        CorpID=RequestData.CorpID,
        Corpsecret=RequestData.Corpsecret,
        AgentID=RequestData.AgentID,
    )
    result = bot_client.PushMarkdown(
        Content=RequestData.Content,
        Touser=RequestData.Touser,
    )
    if "success" in result.lower():
        return {"status": "ok", "message": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@app.get("/api/queryUser", summary="查询用户信息", response_model=List[WeChatID.User])
async def queryUser(ChineseName: Optional[str] = None, Email: Optional[str] = None):
    if not ChineseName and not Email:
        raise HTTPException(
            status_code=400, detail="至少需要提供 ChineseName 或 Email 中的一个参数"
        )

    try:
        db_config = get_db_config()

        wechat_client = WeChatID.WeChatID(
            DBConfig=db_config,
        )

        results = wechat_client.QueryFromDB(ChineseName=ChineseName, Email=Email)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")


@app.get("/api/getFeishuAuthUrl", summary="获取飞书授权URL")
async def getFeishuAuthUrl():
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )

        auth_url = feishu_client.get_url()
        return {"status": "ok", "auth_url": auth_url, "message": "成功生成飞书授权URL"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成授权URL失败: {str(e)}")


@app.get("/api/CreateFeishuToken", summary="获取飞书授权令牌")
async def CreateFeishuToken(code: str):
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )

        token = feishu_client.create_token(code=code)

        return {
            "status": "ok",
            "message": "成功获取飞书授权令牌",
            "data": {
                "access_token": token.access_token,
                "access_token_expires_at": token.access_token_expires_at,
                "refresh_token": token.refresh_token,
                "refresh_token_expires_at": token.refresh_token_expires_at,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取授权令牌失败: {str(e)}")


@app.get("/api/getFeiShuAccessToken", summary="获取有效的飞书Access Token")
async def getFeiShuAccessToken():
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )

        access_token = feishu_client.get_token()

        return {
            "status": "ok",
            "message": "成功获取Access Token",
            "data": {"access_token": access_token},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Access Token失败: {str(e)}")


@app.post("/api/queryFeishuDB", summary="查询飞书多维表格")
async def queryFeishuDB(RequestData: QueryRequest):
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )
        access_token = feishu_client.get_token()

        db_operation = FeishuDB.DBOperation(
            AccessToken=access_token, APPToken=RequestData.APPToken
        )

        filter_obj = None
        if RequestData.Filter:
            conditions = []
            for cond in RequestData.Filter.conditions:
                condition = FeishuDB.Condition(
                    field_name=cond.field_name,
                    operator=FeishuDB.StringOperator(cond.operator.value),
                    value=cond.value,
                )
                conditions.append(condition)

            filter_obj = FeishuDB.Filter(
                conditions=conditions, conjunction=RequestData.Filter.conjunction
            )

        results = db_operation.Query(
            TableID=RequestData.TableID,
            FieldNames=RequestData.FieldNames,
            Filter=filter_obj,
        )

        return {
            "status": "ok",
            "message": "查询成功",
            "data": results["data"],
            "total": results["total"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询飞书数据库失败: {str(e)}")


@app.post("/api/writeFeishuDB", summary="写入飞书多维表格")
async def writeFeishuDB(RequestData: WriteRequest):
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )
        access_token = feishu_client.get_token()

        db_operation = FeishuDB.DBOperation(
            AccessToken=access_token, APPToken=RequestData.APPToken
        )

        result = db_operation.Write(
            TableID=RequestData.TableID,
            Records=RequestData.Records,
        )

        if result == "success":
            return {
                "status": "ok",
                "message": f"成功写入 {len(RequestData.Records)} 条记录",
                "total_records": len(RequestData.Records),
            }
        else:
            raise HTTPException(status_code=500, detail=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入飞书数据库失败: {str(e)}")


@app.post("/api/resetFeishuDB", summary="清空飞书多维表格")
async def resetFeishuDB(RequestData: ResetRequest):
    try:
        db_config = get_db_config()
        feishu_config = get_feishu_config()
        feishu_client = FeishuToken.FSToken(
            DBConfig=db_config,
            FSConfig=feishu_config,
        )
        access_token = feishu_client.get_token()

        db_operation = FeishuDB.DBOperation(
            AccessToken=access_token, APPToken=RequestData.APPToken
        )

        result = db_operation.Reset(TableID=RequestData.TableID)

        if result == "success":
            return {
                "status": "ok",
                "message": "成功清空表格数据",
            }
        else:
            raise HTTPException(status_code=500, detail=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空飞书数据库失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
