from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
import Bot.RoomBot as RoomBot
import Bot.SingleBot as SingleBot
import WechatID.WeChatID as WeChatID
import AuthToken.FeishuToken as FeishuToken
import uvicorn
import base64
import configparser
from fastapi.middleware.cors import CORSMiddleware

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
        "redirecturl": config_parser.get("feishu_config","redirecturl")
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
        return {
            "status": "ok", 
            "auth_url": auth_url,
            "message": "成功生成飞书授权URL"
        }
        
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
                "refresh_token_expires_at": token.refresh_token_expires_at
            }
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
            "data": {
                "access_token": access_token
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Access Token失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
