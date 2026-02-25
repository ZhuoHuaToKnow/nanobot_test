/**
 * @file test-send.js
 * @description 发送消息测试脚本
 * @usage node examples/test-send.js <联系人名称> <消息内容>
 * @example node examples/test-send.js 张三 "你好"
 */

import { WechatSDK } from '../src/WechatSDK.js'

// 获取命令行参数
const args = process.argv.slice(2)
const targetName = args[0]
const messageContent = args[1] || '这是一条测试消息'

// 验证参数
if (!targetName) {
  console.log('AI自动生成日志: ❌ 缺少参数')
  console.log('')
  console.log('用法: node examples/test-send.js <联系人名称> [消息内容]')
  console.log('')
  console.log('示例:')
  console.log('  node examples/test-send.js 张三 "你好"')
  console.log('  node examples/test-send.js "测试群" "群消息"')
  console.log('')
  process.exit(1)
}

console.log('AI自动生成日志: ===========================================')
console.log('AI自动生成日志: 📤 WechatSDK 发送消息测试')
console.log('AI自动生成日志: ===========================================')
console.log(`AI自动生成日志: 目标: ${targetName}`)
console.log(`AI自动生成日志: 消息: ${messageContent}`)
console.log('AI自动生成日志: ===========================================\n')

let loginCompleted = false

// 创建SDK实例
const sdk = new WechatSDK({
  name: 'SendTestBot',

  onLogin: async (user) => {
    console.log('\nAI自动生成日志: ✅ 登录成功!')
    console.log(`AI自动生成日志: 用户: ${await user.name()}`)
    loginCompleted = true

    // 等待1秒后发送消息
    await sleep(1000)
    await sendMessage()
  },

  onMessage: async (msg) => {
    // 收到消息时的处理（可选）
    const contact = msg.talker()
    const text = msg.text()
    const contactName = await contact.name()

    if (!await msg.self()) {
      console.log(`\nAI自动生成日志: 📨 收到消息 ${contactName}: ${text}`)
    }
  },

  onError: (error) => {
    console.error('AI自动生成日志: ❌ 错误:', error.message)
  }
})

/**
 * 发送消息
 */
async function sendMessage() {
  console.log('\nAI自动生成日志: 正在发送消息...')

  // 发送文本消息
  const success = await sdk.sendText(targetName, messageContent)

  if (success) {
    console.log('AI自动生成日志: ✅ 文本消息发送成功')

    // 等待2秒后发送测试文件
    await sleep(2000)

    const fs = await import('fs')
    const testFile = '/tmp/wechat-sdk-send-test.txt'

    fs.writeFileSync(testFile, `
WechatSDK 发送测试文件
目标: ${targetName}
消息: ${messageContent}
时间: ${new Date().toLocaleString('zh-CN')}
    `.trim(), 'utf-8')

    const fileSuccess = await sdk.sendFile(targetName, testFile)

    if (fileSuccess) {
      console.log('AI自动生成日志: ✅ 测试文件发送成功')
    }

    // 再等待2秒后发送测试图片
    await sleep(2000)

    const imageSuccess = await sdk.sendImage(
      targetName,
      'https://wechaty.github.io/wechaty/images/bot-logo.png'
    )

    if (imageSuccess) {
      console.log('AI自动生成日志: ✅ 测试图片发送成功')
    }

    console.log('\nAI自动生成日志: ===========================================')
    console.log('AI自动生成日志: ✅ 测试完成!')
    console.log('AI自动生成日志: ===========================================')

    // 等待5秒后退出
    await sleep(5000)
    await sdk.stop()
    process.exit(0)
  } else {
    console.log('AI自动生成日志: ❌ 发送失败，未找到目标联系人')
    console.log('\nAI自动生成日志: 正在获取联系人列表...')

    const contacts = await sdk.getContacts()
    console.log('\nAI自动生成日志: 可用联系人:')
    for (const contact of contacts) {
      const name = await contact.name()
      const alias = await contact.alias()
      if (name && !name.startsWith('weixin') && name !== '微信团队') {
        console.log(`  • ${name}${alias ? ` (${alias})` : ''}`)
      }
    }

    await sdk.stop()
    process.exit(1)
  }
}

/**
 * 延迟函数
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 启动机器人
sdk.start().catch((error) => {
  console.error('AI自动生成日志: ❌ 启动失败:', error)
  process.exit(1)
})

// 设置120秒超时
setTimeout(() => {
  if (!loginCompleted) {
    console.log('\nAI自动生成日志: ❌ 登录超时（120秒）')
    console.log('AI自动生成日志: 请确保：')
    console.log('  1. 已用微信扫描二维码')
    console.log('  2. 在手机上确认登录')
    sdk.stop()
    process.exit(1)
  }
}, 120000)

// 优雅退出
process.on('SIGINT', async () => {
  console.log('\nAI自动生成日志: 正在停止机器人...')
  await sdk.stop()
  process.exit(0)
})
