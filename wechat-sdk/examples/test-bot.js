/**
 * @file test-bot.js
 * @description 交互式测试机器人
 * @usage node examples/test-bot.js
 */

import { WechatSDK } from '../src/WechatSDK.js'

// 创建SDK实例
const sdk = new WechatSDK({
  name: 'TestBot',
  onLogin: async (user, bot) => {
    console.log('\nAI自动生成日志: ========================')
    console.log('AI自动生成日志: ✅ 登录成功!')
    console.log(`AI自动生成日志: 用户: ${await user.name()}`)
    console.log('AI自动生成日志: ========================')
    console.log('\nAI自动生成日志: 现在可以测试以下功能:')
    console.log('  1. 发送 "ding" -> 自动回复 "dong"')
    console.log('  2. 发送 "文件" -> 发送测试文件')
    console.log('  3. 发送 "图片" -> 发送测试图片')
    console.log('  4. 发送 "联系人" -> 显示联系人列表')
    console.log('  5. 发送 "群聊" -> 显示群聊列表')
    console.log('')
  },

  onMessage: async (msg, bot) => {
    try {
      const contact = msg.talker()
      const room = msg.room()
      const text = msg.text()
      const contactName = await contact.name()
      const roomName = room ? await room.topic() : '私聊'

      console.log(`\nAI自动生成日志: 📨 收到消息 [${roomName}] ${contactName}: ${text}`)

      // 忽略自己的消息
      if (await msg.self()) {
        return
      }

      // 只处理文本消息
      if (msg.type() !== bot.Message.Type.Text) {
        return
      }

      // 处理命令
      switch (text.trim()) {
        case 'ding':
          await msg.say('dong')
          console.log('AI自动生成日志: ✅ 已回复: dong')
          break

        case '文件':
          await sendTestFile(msg)
          break

        case '图片':
          await sendTestImage(msg)
          break

        case '联系人':
          await showContacts(msg)
          break

        case '群聊':
          await showRooms(msg)
          break

        case '帮助':
        case 'help':
          await showHelp(msg)
          break

        default:
          // 回复收到的消息
          await msg.say(`收到: ${text}`)
          console.log(`AI自动生成日志: ✅ 已确认收到消息`)
      }
    } catch (error) {
      console.error('AI自动生成日志: ❌ 处理消息出错:', error.message)
    }
  },

  onError: (error) => {
    console.error('AI自动生成日志: ❌ 机器人错误:', error)
  }
})

/**
 * 发送测试文件
 */
async function sendTestFile(msg) {
  printLog("AI自动生成日志: 创建测试文件...")

  const fs = await import('fs')
  const testFile = '/tmp/wechat-sdk-test.txt'

  const content = `WechatSDK 测试文件
生成时间: ${new Date().toLocaleString('zh-CN')}
SDK版本: 1.0.0
协议: wechat4u (免费)`

  fs.writeFileSync(testFile, content, 'utf-8')

  const { FileBox } = await import('wechaty')
  const fileBox = FileBox.fromFile(testFile)

  await msg.say(fileBox)
  printLog("AI自动生成日志: ✅ 测试文件已发送")
}

/**
 * 发送测试图片
 */
async function sendTestImage(msg) {
  printLog("AI自动生成日志: 发送测试图片...")

  const { FileBox } = await import('wechaty')
  // 使用一个公开的测试图片
  const fileBox = FileBox.fromUrl('https://wechaty.github.io/wechaty/images/bot-logo.png')

  await msg.say(fileBox)
  printLog("AI自动生成日志: ✅ 测试图片已发送")
}

/**
 * 显示联系人列表
 */
async function showContacts(msg) {
  printLog("AI自动生成日志: 获取联系人列表...")

  const bot = msg.wechaty
  const contacts = await bot.Contact.findAll()

  let response = `📋 联系人列表 (共 ${contacts.length} 个):\n\n`

  for (const contact of contacts) {
    const name = await contact.name()
    const alias = await contact.alias()

    if (name && !name.startsWith('weixin') && name !== '微信团队') {
      response += `• ${name}${alias ? ` (${alias})` : ''}\n`
    }
  }

  await msg.say(response)
  printLog("AI自动生成日志: ✅ 联系人列表已发送")
}

/**
 * 显示群聊列表
 */
async function showRooms(msg) {
  printLog("AI自动生成日志: 获取群聊列表...")

  const bot = msg.wechaty
  const rooms = await bot.Room.findAll()

  let response = `🏠 群聊列表 (共 ${rooms.length} 个):\n\n`

  for (const room of rooms) {
    const topic = await room.topic()
    if (topic) {
      response += `• ${topic}\n`
    }
  }

  await msg.say(response)
  printLog("AI自动生成日志: ✅ 群聊列表已发送")
}

/**
 * 显示帮助信息
 */
async function showHelp(msg) {
  const helpText = `
📖 WechatSDK 测试命令:

• ding    - 测试自动回复
• 文件    - 发送测试文件
• 图片    - 发送测试图片
• 联系人  - 显示联系人列表
• 群聊    - 显示群聊列表
• 帮助    - 显示此帮助信息

其他消息将自动回复确认。
  `.trim()

  await msg.say(helpText)
}

function printLog(msg) {
  console.log(msg)
}

// 启动机器人
console.log('AI自动生成日志: ===========================================')
console.log('AI自动生成日志: 🤖 WechatSDK 测试机器人')
console.log('AI自动生成日志: ===========================================')
console.log('AI自动生成日志: 协议: wechat4u (免费，无需Token)')
console.log('AI自动生成日志: 功能: 发送文本、文件、图片')
console.log('AI自动生成日志: ===========================================\n')

sdk.start().catch((error) => {
  console.error('AI自动生成日志: ❌ 启动失败:', error)
  process.exit(1)
})

// 优雅退出
process.on('SIGINT', async () => {
  console.log('\nAI自动生成日志: 正在停止机器人...')
  await sdk.stop()
  process.exit(0)
})
