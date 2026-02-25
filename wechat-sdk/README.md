# @nanobot/wechat-sdk

基于 [Wechaty](https://github.com/wechaty/wechaty) 封装的精简微信机器人 SDK。

## 特点

- ✅ **完全免费** - 使用 Wechat4U 协议（iPad协议），无需购买 Token
- ✅ **开箱即用** - 简洁的 API 设计，快速上手
- ✅ **功能完整** - 支持收发文本、文件、图片
- ✅ **TypeScript 友好** - 完整的类型定义
- ✅ **事件驱动** - 灵活的事件回调机制

---

## 安装

```bash
cd wechat-sdk
npm install
```

使用国内镜像（推荐）：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

---

## 快速开始

### 方式一：交互式测试机器人

```bash
npm run dev
```

**流程：**
1. 终端会显示二维码
2. 用微信扫描登录
3. 登录成功后，给自己或好友发送消息测试：
   - 发送 `ding` → 自动回复 `dong`
   - 发送 `文件` → 自动发送测试文件
   - 发送 `图片` → 自动发送测试图片
   - 发送 `联系人` → 显示联系人列表
   - 发送 `群聊` → 显示群聊列表

### 方式二：发送消息测试

```bash
# 向指定联系人发送消息
npm test -- <联系人名称> <消息内容>

# 示例：向"张三"发送"你好"
npm test -- 张三 "你好"
```

---

## 使用示例

### 基础用法

```javascript
import { WechatSDK } from './src/WechatSDK.js'

const sdk = new WechatSDK({
  name: 'MyBot',

  // 登录成功回调
  onLogin: async (user) => {
    console.log('登录成功:', await user.name())
  },

  // 消息处理回调
  onMessage: async (msg, bot) => {
    const contact = msg.talker()
    const text = msg.text()
    const room = msg.room()

    // 获取发送者信息
    const contactName = await contact.name()
    const roomName = room ? await room.topic() : '私聊'

    console.log(`收到消息 [${roomName}] ${contactName}: ${text}`)

    // 忽略自己的消息
    if (await msg.self()) return

    // 处理消息
    if (text === 'ding') {
      await msg.say('dong')
    }
  }
})

await sdk.start()
```

### 发送消息

```javascript
// 发送文本消息
await sdk.sendText('张三', '你好！')

// 发送文件
await sdk.sendFile('张三', '/path/to/file.pdf')

// 发送网络图片
await sdk.sendImage('张三', 'https://example.com/image.png')

// 发送到群聊
await sdk.sendText('某个群名称', '群消息')
```

### 查找联系人和群聊

```javascript
// 查找联系人
const contact = await sdk.findContact('张三')
if (contact) {
  await contact.say('找到你了！')
}

// 查找群聊
const room = await sdk.findRoom('测试群')
if (room) {
  await room.say('群消息')
}

// 获取所有联系人
const contacts = await sdk.getContacts()

// 获取所有群聊
const rooms = await sdk.getRooms()
```

### 自定义扫码处理

```javascript
const sdk = new WechatSDK({
  name: 'MyBot',

  onScan: (qrcode, status) => {
    // 自定义扫码处理
    const url = `https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrcode)}`
    console.log('扫码链接:', url)
    // 可以在这里将二维码发送到手机或其他设备
  },

  onLogin: async (user) => {
    console.log('登录成功')
  }
})
```

---

## API 文档

### WechatSDK

#### 构造函数选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | string | `'WechatSDK'` | 机器人名称 |
| `puppet` | string | `'wechaty-puppet-wechat4u'` | Puppet 类型 |
| `puppetOptions` | object | `{ uos: true }` | Puppet 配置选项 |
| `onScan` | function | 默认处理 | 扫码回调 |
| `onLogin` | function | 默认处理 | 登录回调 |
| `onLogout` | function | 默认处理 | 登出回调 |
| `onMessage` | function | - | 消息回调 |
| `onFriendship` | function | 默认处理 | 好友请求回调 |
| `onError` | function | 默认处理 | 错误回调 |

#### 方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `start()` | `Promise<void>` | 启动机器人 |
| `stop()` | `Promise<void>` | 停止机器人 |
| `getBot()` | `Wechaty` | 获取 bot 实例 |
| `findContact(name)` | `Promise<Contact|null>` | 查找联系人 |
| `findRoom(topic)` | `Promise<Room|null>` | 查找群聊 |
| `sendText(target, text)` | `Promise<boolean>` | 发送文本消息 |
| `sendFile(target, filePath)` | `Promise<boolean>` | 发送文件 |
| `sendImage(target, url)` | `Promise<boolean>` | 发送图片 |
| `getContacts()` | `Promise<Contact[]>` | 获取所有联系人 |
| `getRooms()` | `Promise<Room[]>` | 获取所有群聊 |
| `isLoggedIn()` | `boolean` | 是否已登录 |
| `getSelf()` | `Promise<Contact|null>` | 获取登录用户 |

---

## 事件回调

### onScan(qrcode, status, bot)

扫码时触发，可用于自定义二维码显示方式。

```javascript
onScan: (qrcode, status, bot) => {
  console.log('扫码状态:', status)
  console.log('二维码:', qrcode)
}
```

### onLogin(user, bot)

登录成功后触发。

```javascript
onLogin: async (user, bot) => {
  const name = await user.name()
  console.log('登录成功:', name)
}
```

### onMessage(msg, bot)

收到消息时触发。

```javascript
onMessage: async (msg, bot) => {
  const contact = msg.talker()      // 发送者
  const text = msg.text()            // 消息内容
  const room = msg.room()            // 群聊（如果是群消息）

  // 判断是否是自己发的消息
  const isSelf = await msg.self()

  // 消息类型
  const type = msg.type()
  // bot.Message.Type.Text     - 文本
  // bot.Message.Type.Image     - 图片
  // bot.Message.Type.Video     - 视频
  // bot.Message.Type.Audio     - 音频
  // bot.Message.Type.Attachment - 文件
}
```

---

## 项目结构

```
wechat-sdk/
├── package.json           # 项目配置
├── README.md              # 说明文档
├── src/
│   ├── index.js          # 入口文件
│   └── WechatSDK.js      # SDK 核心类
└── examples/
    ├── test-bot.js       # 交互式测试机器人
    └── test-send.js      # 发送消息测试脚本
```

---

## 注意事项

1. **使用小号测试** - 建议使用微信小号进行测试
2. **网络环境** - 确保网络能访问微信服务器
3. **Node.js 版本** - 需要 Node.js >= 18.0.0
4. **Web 微信限制** - Wechat4U 基于 Web 协议，某些功能可能受限
5. **账号安全** - 频繁操作可能触发微信风控，请适度使用

---

## 常见问题

### 安装依赖失败

```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 找不到联系人

- 确保联系人名称正确
- 使用微信昵称或备注名都可以
- 可以运行测试机器人查看完整的联系人列表

### 发送文件失败

- Wechat4U 协议对文件上传有限制
- 某些文件类型可能不支持
- 建议使用小文件测试

---

## 与 nanobot 集成

此 SDK 可以轻松集成到 nanobot 的渠道架构中：

```python
# nanobot/channels/wechat.py
from WechatSDK import WechatSDK

class WechatChannel(BaseChannel):
    def __init__(self):
        # 初始化 SDK
        pass

    async def start(self):
        # 启动机器人
        pass

    async def send(self, msg: OutboundMessage):
        # 发送消息
        pass
```

---

## 参考资料

- [Wechaty 官网](https://wechaty.js.org)
- [Wechat4U GitHub](https://github.com/wechaty/puppet-wechat4u)
- [Wechaty GitHub](https://github.com/wechaty/wechaty)

---

## License

MIT
