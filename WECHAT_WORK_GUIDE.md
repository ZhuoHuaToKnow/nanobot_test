# 企业微信 (WeChat Work) 集成指南

## 📋 概述

nanobot 现已支持企业微信！这是一个**官方支持、稳定可靠**的微信自动化方案，不会被封号。

### 特点

- ✅ **官方 API** - 使用企业微信官方接口，完全合法
- ✅ **稳定可靠** - 不会被风控或封号
- ✅ **支持 Markdown** - 发送富文本消息
- ✅ **易于配置** - 简单的 JSON 配置

### 当前支持

- ✅ 主动发送消息（推送模式）
- 🔄 接收消息（需要回调服务器，即将支持）

---

## 🚀 快速开始

### 1. 创建企业微信应用

#### 1.1 注册企业（如果没有）

1. 访问 [企业微信官网](https://work.weixin.qq.com/)
2. 下载企业微信 APP 或使用网页版
3. 点击"注册企业"（个人也可以免费注册）

#### 1.2 创建应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)
2. 进入 **应用管理** → **应用** → **自建**
3. 点击 **创建应用**
4. 填写应用信息：
   - **应用名称**：`nanobot` 或你喜欢的名称
   - **应用介绍**：`AI 助手`
   - **应用logo**：上传图片（可选）

#### 1.3 获取配置信息

在创建的应用中，找到并记录以下信息：

1. **AgentId**（例如：`1000002`）
   - 位置：应用详情页顶部

2. **Secret**
   - 位置：应用详情页 → 凭证与基础信息
   - 点击"查看"按钮获取

3. **CorpId**（企业ID）
   - 位置：**我的企业** → **企业信息**
   - 在企业ID旁边点击"复制"

#### 1.4 配置应用权限（可选）

在应用设置中：
- **通讯录权限**：启用"发送消息到企业成员"
- **可见范围**：设置可以使用的成员或部门

### 2. 配置 nanobot

编辑 `~/.nanobot/config.json`，添加以下配置：

```json
{
  "channels": {
    "wecom": {
      "enabled": true,
      "corpId": "你的企业ID",
      "agentId": 1000002,
      "secret": "你的应用Secret",
      "allowFrom": []
    }
  }
}
```

**配置说明：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `enabled` | 是否启用 | `true` |
| `corpId` | 企业ID | `"ww1234567890abcdef"` |
| `agentId` | 应用Agent ID | `1000002` |
| `secret` | 应用Secret | `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"` |
| `allowFrom` | 允许的用户ID白名单 | `[]`（空=允许所有人） |
| `token` | 回调验证Token | 可选，用于接收消息 |
| `encodingAesKey` | 回调加密Key | 可选，用于接收消息 |
| `callbackUrl` | 回调URL | 可选，需要公网服务器 |

### 3. 测试连接

#### 方法一：使用测试脚本

```bash
python wecom_test.py
```

按提示输入配置信息，脚本会发送一条测试消息。

#### 方法二：使用 Python 代码

```python
import asyncio
from nanobot.channels.wechat import WeComChannel
from nanobot.bus.queue import MessageBus

async def send_message():
    # 创建配置
    config = WeComConfig(
        enabled=True,
        corp_id="你的企业ID",
        agent_id=1000002,
        secret="你的应用Secret",
        allow_from=[],
    )

    # 创建渠道
    bus = MessageBus()
    channel = WeComChannel(config, bus)

    # 启动并发送消息
    await channel.start()
    await channel.send_to_user("用户ID", "Hello from nanobot!")
    await channel.stop()

asyncio.run(send_message())
```

### 4. 启动 nanobot 网关

配置完成后，启动网关：

```bash
nanobot gateway
```

现在你可以通过企业微信接收 nanobot 的消息了！

---

## 📖 使用方法

### 发送消息给用户

```python
from nanobot.channels.wechat import WeComChannel

# 假设你已经配置好 channel
await channel.send_to_user("zhangsan", "你好，这是一条测试消息！")
```

### 发送 Markdown 消息

```python
markdown_text = """
# 重要通知

**任务清单**：
- [x] 完成项目文档
- [ ] 代码审查
- [ ] 部署到生产环境

详细信息请查看：[文档链接](https://example.com)
"""

await channel.send_to_user("zhangsan", markdown_text)
```

### 通过消息总线发送

```python
from nanobot.bus.events import OutboundMessage

msg = OutboundMessage(
    channel="wecom",
    chat_id="zhangsan",
    content="Hello via message bus!",
)

# 将消息发送到总线，由 dispatcher 路由
await bus.publish_outbound(msg)
```

---

## 🔧 获取用户 ID

发送消息需要知道用户的 **UserID**（员工账号）。

### 方法一：通过企业通讯录

1. 进入企业微信管理后台
2. **通讯录** → 选择成员
3. 在成员详情中可以看到 **账号**（UserID）

### 方法二：通过 API

```python
import httpx

async def get_user_list(access_token: str):
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/list"
    params = {
        "access_token": access_token,
        "department_id": 1,  # 部门ID
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        return resp.json()

# 返回的用户列表中包含每个用户的 userid
```

---

## ⚠️ 注意事项

### 1. 发送频率限制

企业微信 API 有速率限制：
- 每个应用每分钟可发送消息数有限制
- 建议避免短时间内大量发送

### 2. 消息格式

- **文本消息**：纯文本，最多 2048 字节
- **Markdown 消息**：支持的语法有限，参考 [官方文档](https://developer.work.weixin.qq.com/document/path/90236)

### 3. 可见范围

确保应用在目标用户的可见范围内：
- 应用详情 → 可见范围 → 添加成员/部门

### 4. 权限要求

应用需要以下权限：
- **发送消息到企业成员**

---

## 🔄 与其他渠道对比

| 渠道 | 稳定性 | 配置难度 | 功能完整性 | 推荐度 |
|------|--------|----------|------------|--------|
| **企业微信** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 飞书 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 钉钉 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Telegram | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 个人微信 | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |

---

## 🐛 常见问题

### Q1: 发送消息失败，返回错误码

**错误码 40014**：access_token 无效
- 解决：检查 Secret 是否正确

**错误码 60020**：成员不在应用的可见范围
- 解决：在应用设置中添加目标用户到可见范围

**错误码 601121**：userid 不存在
- 解决：检查 UserID 是否正确，区分大小写

### Q2: 如何批量发送消息？

```python
user_ids = ["user1", "user2", "user3"]
message = "这是一条广播消息"

for user_id in user_ids:
    await channel.send_to_user(user_id, message)
```

### Q3: 支持发送文件吗？

当前版本主要支持文本和 Markdown。文件支持即将推出。

---

## 📚 参考文档

- [企业微信 API 文档](https://developer.work.weixin.qq.com/document/path/90672)
- [应用管理 API](https://developer.work.weixin.qq.com/document/path/90228)
- [消息发送 API](https://developer.work.weixin.qq.com/document/path/90236)

---

## 🎉 完成！

现在你可以在 nanobot 中使用企业微信了！

如果遇到问题，欢迎提 Issue 或贡献代码。
