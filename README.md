# 企业微信ID获取与消息推送系统

一个基于 FastAPI 的企业微信集成系统，提供微信用户ID获取、消息推送和数据库管理功能。

## 功能特性

### 🔍 微信用户ID获取
- 通过邮箱地址自动获取企业微信用户ID
- 支持批量处理用户列表
- 自动去重，避免重复查询已存在的用户
- 数据持久化存储到MySQL数据库

### 📱 消息推送服务
- **群聊机器人推送**：支持文本、Markdown、图片消息
- **单聊推送**：支持文本、Markdown消息
- 支持@提及功能（用户ID或手机号）
- 支持@all全员提及

### 🗄️ 数据管理
- MySQL数据库集成
- 用户信息查询API
- 支持按姓名或邮箱查询用户

### 🚀 飞书集成
- 飞书OAuth授权流程
- 自动令牌管理和刷新
- Access Token获取接口

### 🌐 RESTful API
- 基于FastAPI构建的高性能API
- 自动API文档生成
- 完整的错误处理机制
- CORS跨域支持

## 项目结构

```
wechat_id_pull/
├── API.py                 # FastAPI应用主文件
├── config.ini             # 配置文件
├── WechatID/
│   └── WeChatID.py       # 微信ID获取核心逻辑
├── Bot/
│   ├── RoomBot.py        # 群聊机器人
│   └── SingleBot.py      # 单聊机器人
├── AuthToken/
│   └── FeishuToken.py    # 飞书令牌管理
├── pyproject.toml        # 项目依赖配置
└── README.md            # 项目说明文档
```

## 快速开始

### 环境要求
- Python >= 3.12
- MySQL数据库

### 安装依赖

```bash
# 使用uv安装依赖（推荐）
uv sync

# 或使用pip安装
pip install -r requirements.txt
```

### 配置设置

1. 编辑 `config.ini` 配置文件：

```ini
[weixin_config]
secret = your_corp_secret
corpid = your_corp_id
agentid = your_agent_id
url = https://qyapi.weixin.qq.com/cgi-bin/user/get_userid_by_email?access_token={}
get_access_token_url = https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}

[database]
host = your_db_host
port = 3306
user = your_db_user
password = your_db_password
database = your_db_name
charset = utf8mb4

[feishu_config]
appid = your_feishu_app_id
scope = your_feishu_scope
secret = your_feishu_app_secret
redirecturl = your_redirect_url
```

2. 确保MySQL数据库中存在 `users` 表：

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    wxid VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 启动服务

```bash
python API.py
```

服务将在 `http://localhost:8000` 启动，访问 `http://localhost:8000/docs` 查看API文档。

## API接口

### 消息推送接口

#### 1. 群聊推送文本消息
```http
POST /api/chatroomPushText
Content-Type: application/json

{
    "Webhook": "your_webhook_url",
    "Content": "消息内容",
    "All": false,
    "IDList": ["user_id1", "user_id2"],
    "MobileList": ["13800138000"]
}
```

#### 2. 群聊推送Markdown消息
```http
POST /api/chatroomPushMD
Content-Type: application/json

{
    "Webhook": "your_webhook_url",
    "Content": "**Markdown内容**",
    "IDList": ["user_id1", "user_id2"]
}
```

#### 3. 群聊推送图片消息
```http
POST /api/chatroomPushImage
Content-Type: application/json

{
    "Webhook": "your_webhook_url",
    "ImageBase64": "base64_encoded_image_data"
}
```

#### 4. 单聊推送文本消息
```http
POST /api/PushText
Content-Type: application/json

{
    "Content": "消息内容",
    "Touser": ["user_id1", "user_id2"],
    "CorpID": "your_corp_id",
    "Corpsecret": "your_corp_secret",
    "AgentID": "your_agent_id"
}
```

#### 5. 单聊推送Markdown消息
```http
POST /api/PushMD
Content-Type: application/json

{
    "Content": "**Markdown内容**",
    "Touser": ["user_id1", "user_id2"],
    "CorpID": "your_corp_id",
    "Corpsecret": "your_corp_secret",
    "AgentID": "your_agent_id"
}
```

### 用户查询接口

#### 查询用户信息
```http
GET /api/queryUser?ChineseName=张三
GET /api/queryUser?Email=zhangsan@example.com
GET /api/queryUser?ChineseName=张三&Email=zhangsan@example.com
```

**响应示例：**
```json
[
    {
        "name": "张三",
        "email": "zhangsan@example.com",
        "wxid": "ZhangSan"
    }
]
```

### 飞书授权接口

#### 1. 获取飞书授权URL
```http
GET /api/getFeishuAuthUrl
```

**响应示例：**
```json
{
    "status": "ok",
    "auth_url": "https://open.feishu.cn/open-apis/authen/v1/authorize?...",
    "message": "成功生成飞书授权URL"
}
```

#### 2. 获取飞书授权令牌(用于接受飞书Code)
```http
GET /api/CreateFeishuToken?code=your_auth_code
```

**参数说明：**
- `code` (必填): 飞书授权码

**响应示例：**
```json
{
    "status": "ok",
    "message": "成功获取飞书授权令牌",
    "data": {
        "access_token": "access_token_string",
        "access_token_expires_at": 1234567890,
        "refresh_token": "refresh_token_string",
        "refresh_token_expires_at": 1234567890
    }
}
```

#### 3. 获取有效的飞书Access Token
```http
GET /api/getFeiShuAccessToken
```

**响应示例：**
```json
{
    "status": "ok",
    "message": "成功获取Access Token",
    "data": {
        "access_token": "access_token_string"
    }
}
```

## 核心类说明

### WeChatID类
- `__init__()`: 初始化数据库配置和微信配置
- `get_wechat_id()`: 批量获取微信用户ID
- `SaveToDB()`: 保存用户信息到数据库
- `QueryFromDB()`: 从数据库查询用户信息

### RoomBot类
- `PushText()`: 推送文本消息到群聊
- `PushMarkdown()`: 推送Markdown消息到群聊
- `PushImage()`: 推送图片消息到群聊

### SingleBot类
- `PushText()`: 推送文本消息给指定用户
- `PushMarkdown()`: 推送Markdown消息给指定用户

### FeishuToken类
- `__init__()`: 初始化数据库配置和飞书配置
- `get_url()`: 生成飞书OAuth授权URL
- `create_token()`: 使用授权码创建飞书令牌
- `get_token()`: 获取有效的Access Token（自动刷新）

## 使用示例

### Python代码示例

```python
from WechatID.WeChatID import WeChatID

# 配置数据库连接
db_config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "password",
    "database": "wechat_db",
    "charset": "utf8mb4"
}

# 配置微信API
wechat_config = {
    "corpid": "your_corp_id",
    "secret": "your_corp_secret",
    "url": "https://qyapi.weixin.qq.com/cgi-bin/user/get_userid_by_email?access_token={}",
    "get_access_token_url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}"
}

# 用户列表
names = ["张三", "李四", "王五"]
emails = ["zhangsan@example.com", "lisi@example.com", "wangwu@example.com"]

# 创建微信ID获取实例
wechat_client = WeChatID(
    DBConfig=db_config,
    NameList=names,
    EmailList=emails,
    WechatConfig=wechat_config
)

# 获取微信ID并保存到数据库
users = wechat_client.get_wechat_id()
wechat_client.SaveToDB()

# 查询用户信息
user_info = wechat_client.QueryFromDB(ChineseName="张三")
print(user_info)
```

## 注意事项

1. **企业微信配置**：需要先在企业微信管理后台创建应用并获取相关配置信息
2. **数据库权限**：确保数据库用户具有读写权限
3. **网络访问**：需要能够访问企业微信API接口
4. **安全性**：生产环境中请妥善保管配置文件中的敏感信息

## 依赖项

- `fastapi`: Web框架
- `pymysql`: MySQL数据库连接
- `requests`: HTTP请求库
- `pydantic`: 数据验证
- `uvicorn`: ASGI服务器

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 更新日志

- v0.1.0: 初始版本，支持基本的微信ID获取和消息推送功能
