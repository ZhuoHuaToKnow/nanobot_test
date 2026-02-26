# 企业微信集成到 nanobot - 快速开始

## ✅ 已完成的工作

我已经成功将企业微信（WeChat Work）集成到 nanobot 中：

### 1. **配置模型** ✅
在 `nanobot/config/schema.py` 中添加了 `WeComConfig` 类：
- `corp_id` - 企业ID
- `agent_id` - 应用Agent ID
- `secret` - 应用Secret
- `allow_from` - 用户白名单

### 2. **渠道实现** ✅
创建了 `nanobot/channels/wechat.py`：
- `WeComChannel` 类实现了企业微信 API
- 支持发送文本和 Markdown 消息
- 自动管理 access_token

### 3. **管理器注册** ✅
在 `nanobot/channels/manager.py` 中注册了企业微信渠道

### 4. **辅助工具** ✅
- `wecom_test.py` - 测试脚本
- `wecom_config_validator.py` - 配置验证器
- `config_example.json` - 配置示例
- `WECHAT_WORK_GUIDE.md` - 完整使用指南

---

## 🚀 快速开始（3步）

### 第 1 步：创建企业微信应用

1. 访问 [企业微信管理后台](https://work.weixin.qq.com/)
2. **应用管理** → **应用** → **自建** → **创建应用**
3. 获取以下信息：
   - **AgentId**: 你的是 `1000002` ✅
   - **Secret**: 在应用详情页点击"查看"
   - **CorpId**: 在 **我的企业** → **企业信息** 中

### 第 2 步：配置 nanobot

编辑 `~/.nanobot/config.json`，添加以下内容：

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

### 第 3 步：测试连接

```bash
# 方法一：使用测试脚本（推荐）
python wecom_test.py

# 方法二：启动网关
nanobot gateway
```

---

## 📖 使用示例

### 发送消息

```python
from nanobot.channels.wechat import WeComChannel
from nanobot.bus.queue import MessageBus

# 创建配置
config = WeComConfig(
    enabled=True,
    corp_id="你的企业ID",
    agent_id=1000002,
    secret="你的应用Secret",
)

# 创建渠道并发送消息
bus = MessageBus()
channel = WeComChannel(config, bus)

# 启动
await channel.start()

# 发送消息
await channel.send_to_user("用户ID", "Hello from nanobot!")

# 停止
await channel.stop()
```

---

## 🔧 验证配置

运行配置验证器：

```bash
python wecom_config_validator.py
```

或者验证现有的配置文件：

```bash
python wecom_config_validator.py --config ~/.nanobot/config.json
```

---

## 📚 文档

完整文档请查看：
- **[WECHAT_WORK_GUIDE.md](./WECHAT_WORK_GUIDE.md)** - 详细使用指南
- **[config_example.json](./config_example.json)** - 配置示例

---

## ⚠️ 重要提示

### 关于用户ID

发送消息需要知道目标用户的 **UserID**（员工账号），你可以：

1. **查看企业通讯录**
   - 企业微信管理后台 → 通讯录 → 成员详情 → 账号

2. **通过 API 获取**
   - 使用企业微信 API 的 `user/list` 接口

### 关于发送模式

当前实现是 **推送模式**（主动发送消息）：
- ✅ nanobot 主动发送消息给用户
- ✅ 适合通知、提醒等场景
- ✅ 不需要公网服务器

**接收消息模式**（用户给 nanobot 发消息）需要：
- ❌ 公网服务器（用于接收企业微信回调）
- 🔄 即将支持

---

## 🎉 下一步

1. ✅ 配置已添加到 nanobot
2. ✅ 渠道已实现
3. ✅ 文档已完成

**现在你需要做的：**

1. 获取你的 `Secret` 和 `CorpId`
2. 更新 `~/.nanobot/config.json`
3. 运行测试：`python wecom_test.py`
4. 启动网关：`nanobot gateway`

---

## 🐛 遇到问题？

### 常见错误

**错误码 40014**：access_token 无效
- 检查 Secret 是否正确

**错误码 60020**：成员不在应用的可见范围
- 在应用设置中添加目标用户

**错误码 601121**：userid 不存在
- 检查 UserID 是否正确（区分大小写）

---

祝使用愉快！🎊
