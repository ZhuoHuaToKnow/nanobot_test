/**
 * @file WechatSDK.js
 * @description 精简的微信机器人SDK，基于Wechaty封装
 * @author nanobot
 */

// 禁用 SSL 证书验证（解决自签名证书问题）
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'

import { WechatyBuilder, ScanStatus, log } from 'wechaty'
import qrTerminal from 'qrcode-terminal'
import fs from 'fs'

/**
 * WechatSDK - 微信机器人SDK
 *
 * 使用示例:
 * ```js
 * import { WechatSDK } from '@nanobot/wechat-sdk'
 *
 * const sdk = new WechatSDK({
 *   name: 'MyBot',
 *   onLogin: (user) => console.log('登录:', user),
 *   onMessage: async (msg) => {
 *     const text = msg.text()
 *     if (text === 'ding') await msg.say('dong')
 *   }
 * })
 *
 * await sdk.start()
 * ```
 */
export class WechatSDK {
  /**
   * 构造函数
   * @param {Object} options - 配置选项
   * @param {string} options.name - 机器人名称
   * @param {string} options.puppet - puppet类型，默认 'wechaty-puppet-wechat4u'
   * @param {Function} options.onScan - 扫码回调
   * @param {Function} options.onLogin - 登录回调
   * @param {Function} options.onLogout - 登出回调
   * @param {Function} options.onMessage - 消息回调
   * @param {Function} options.onFriendship - 好友请求回调
   * @param {Function} options.onError - 错误回调
   * @param {Object} options.puppetOptions - puppet配置选项
   */
  constructor(options = {}) {
    printLog("AI自动生成日志: 初始化 WechatSDK")

    this.options = {
      name: options.name || 'WechatSDK',
      puppet: options.puppet || 'wechaty-puppet-wechat4u',
      // wechat4u 可能需要特定配置
      puppetOptions: options.puppetOptions || {},
      onScan: options.onScan || this._defaultOnScan.bind(this),
      onLogin: options.onLogin || this._defaultOnLogin.bind(this),
      onLogout: options.onLogout || this._defaultOnLogout.bind(this),
      onMessage: options.onMessage,
      onFriendship: options.onFriendship || this._defaultOnFriendship.bind(this),
      onError: options.onError || this._defaultOnError.bind(this),
    }

    // 初始化 bot
    this.bot = WechatyBuilder.build({
      name: this.options.name,
      puppet: this.options.puppet,
      puppetOptions: this.options.puppetOptions,
    })

    // 绑定事件
    this._bindEvents()

    printLog("AI自动生成日志: WechatSDK 初始化完成")
  }

  /**
   * 绑定事件处理器
   * @private
   */
  _bindEvents() {
    printLog("AI自动生成日志: 绑定事件处理器")

    this.bot.on('scan', (qrcode, status) => {
      this.options.onScan(qrcode, status, this.bot)
    })

    this.bot.on('login', (user) => {
      this.options.onLogin(user, this.bot)
    })

    this.bot.on('logout', (user) => {
      this.options.onLogout(user, this.bot)
    })

    if (this.options.onMessage) {
      this.bot.on('message', async (msg) => {
        await this.options.onMessage(msg, this.bot)
      })
    }

    this.bot.on('friendship', async (friendship) => {
      await this.options.onFriendship(friendship, this.bot)
    })

    this.bot.on('error', (error) => {
      this.options.onError(error, this.bot)
    })
  }

  /**
   * 默认扫码处理
   * @private
   */
  _defaultOnScan(qrcode, status) {
    if (status === ScanStatus.Waiting || status === ScanStatus.Timeout) {
      qrTerminal.generate(qrcode, { small: true })
      const qrcodeImageUrl = [
        'https://api.qrserver.com/v1/create-qr-code/?data=',
        encodeURIComponent(qrcode)
      ].join('')
      console.log(`\nAI自动生成日志: 请扫描二维码登录微信`)
      console.log(`AI自动生成日志: 二维码链接: ${qrcodeImageUrl}`)
    } else {
      log.info('AI自动生成日志: 扫码状态:', ScanStatus[status], status)
    }
  }

  /**
   * 默认登录处理
   * @private
   */
  _defaultOnLogin(user) {
    const date = new Date()
    console.log(`\nAI自动生成日志: ✅ 登录成功!`)
    console.log(`AI自动生成日志: 用户: ${user}`)
    console.log(`AI自动生成日志: 时间: ${date.toLocaleString('zh-CN')}`)
  }

  /**
   * 默认登出处理
   * @private
   */
  _defaultOnLogout(user) {
    console.log(`\nAI自动生成日志: 用户 ${user} 已登出`)
  }

  /**
   * 默认好友请求处理
   * @private
   */
  async _defaultOnFriendship(friendship) {
    const contact = friendship.contact()
    const name = await contact.name()
    const hello = friendship.hello()
    const type = friendship.type()

    printLog(`AI自动生成日志: 收到好友请求 - ${name}: ${hello}`)

    // 默认自动接受所有好友请求
    if (type === this.bot.Friendship.Type.Receive) {
      await friendship.accept()
      printLog(`AI自动生成日志: 已自动接受好友请求: ${name}`)
    }
  }

  /**
   * 默认错误处理
   * @private
   */
  _defaultOnError(error) {
    // wechat4u 的兼容性错误，可以忽略
    if (error.message && error.message.includes('Cannot read properties of undefined')) {
      return
    }

    // SSL 证书错误，通常是由于网络代理导致的，可以忽略
    if (error.message && error.message.includes('self-signed certificate')) {
      return
    }

    // MemoryCard JSON 错误，可以忽略
    if (error.message && error.message.includes('Unexpected end of JSON input')) {
      return
    }

    // HTML 响应错误（wechat4u 尝试不同连接方式时的正常现象）
    if (error.message && error.message.includes('Unexpected token')) {
      return
    }

    // 其他错误正常输出（但不输出 code 2 的错误，因为通常不是严重问题）
    if (error.code !== 2) {
      console.error('AI自动生成日志: ❌ 发生错误:', error.message)
    }
  }

  /**
   * 启动机器人
   * @returns {Promise<void>}
   */
  async start() {
    printLog("AI自动生成日志: 正在启动微信机器人...")

    try {
      await this.bot.start()
      printLog("AI自动生成日志: 机器人启动成功，等待扫码登录...")
    } catch (error) {
      printLog(`AI自动生成日志: 启动失败: ${error.message}`)
      throw error
    }
  }

  /**
   * 停止机器人
   * @returns {Promise<void>}
   */
  async stop() {
    printLog("AI自动生成日志: 正在停止微信机器人...")

    try {
      await this.bot.stop()
      printLog("AI自动生成日志: 机器人已停止")
    } catch (error) {
      printLog(`AI自动生成日志: 停止失败: ${error.message}`)
      throw error
    }
  }

  /**
   * 获取 bot 实例
   * @returns {Wechaty} bot实例
   */
  getBot() {
    return this.bot
  }

  /**
   * 查找联系人
   * @param {string} name - 联系人名称
   * @returns {Promise<Contact|null>}
   */
  async findContact(name) {
    printLog(`AI自动生成日志: 查找联系人: ${name}`)

    try {
      const contact = await this.bot.Contact.find({ name })
      if (contact) {
        printLog(`AI自动生成日志: 找到联系人: ${name}`)
      } else {
        printLog(`AI自动生成日志: 未找到联系人: ${name}`)
      }
      return contact
    } catch (error) {
      printLog(`AI自动生成日志: 查找联系人失败: ${error.message}`)
      return null
    }
  }

  /**
   * 查找群聊
   * @param {string} topic - 群名称
   * @returns {Promise<Room|null>}
   */
  async findRoom(topic) {
    printLog(`AI自动生成日志: 查找群聊: ${topic}`)

    try {
      const room = await this.bot.Room.find({ topic })
      if (room) {
        printLog(`AI自动生成日志: 找到群聊: ${topic}`)
      } else {
        printLog(`AI自动生成日志: 未找到群聊: ${topic}`)
      }
      return room
    } catch (error) {
      printLog(`AI自动生成日志: 查找群聊失败: ${error.message}`)
      return null
    }
  }

  /**
   * 发送文本消息
   * @param {string|Contact|Room} target - 目标（名称、Contact实例或Room实例）
   * @param {string} text - 消息内容
   * @returns {Promise<boolean>}
   */
  async sendText(target, text) {
    printLog(`AI自动生成日志: 发送文本消息 -> ${target}`)

    try {
      let targetObj = target

      // 如果是字符串，先查找
      if (typeof target === 'string') {
        targetObj = await this.findContact(target)
        if (!targetObj) {
          targetObj = await this.findRoom(target)
        }
        if (!targetObj) {
          printLog(`AI自动生成日志: 未找到目标: ${target}`)
          return false
        }
      }

      await targetObj.say(text)
      printLog(`AI自动生成日志: 文本消息发送成功`)
      return true
    } catch (error) {
      printLog(`AI自动生成日志: 发送文本消息失败: ${error.message}`)
      return false
    }
  }

  /**
   * 发送文件
   * @param {string|Contact|Room} target - 目标
   * @param {string} filePath - 文件路径
   * @returns {Promise<boolean>}
   */
  async sendFile(target, filePath) {
    printLog(`AI自动生成日志: 发送文件 -> ${target}: ${filePath}`)

    try {
      // 检查文件是否存在
      if (!fs.existsSync(filePath)) {
        printLog(`AI自动生成日志: 文件不存在: ${filePath}`)
        return false
      }

      let targetObj = target

      // 如果是字符串，先查找
      if (typeof target === 'string') {
        targetObj = await this.findContact(target)
        if (!targetObj) {
          targetObj = await this.findRoom(target)
        }
        if (!targetObj) {
          printLog(`AI自动生成日志: 未找到目标: ${target}`)
          return false
        }
      }

      const { FileBox } = await import('wechaty')
      const fileBox = FileBox.fromFile(filePath)
      await targetObj.say(fileBox)

      printLog(`AI自动生成日志: 文件发送成功`)
      return true
    } catch (error) {
      printLog(`AI自动生成日志: 发送文件失败: ${error.message}`)
      return false
    }
  }

  /**
   * 发送网络图片
   * @param {string|Contact|Room} target - 目标
   * @param {string} url - 图片URL
   * @returns {Promise<boolean>}
   */
  async sendImage(target, url) {
    printLog(`AI自动生成日志: 发送图片 -> ${target}: ${url}`)

    try {
      let targetObj = target

      // 如果是字符串，先查找
      if (typeof target === 'string') {
        targetObj = await this.findContact(target)
        if (!targetObj) {
          targetObj = await this.findRoom(target)
        }
        if (!targetObj) {
          printLog(`AI自动生成日志: 未找到目标: ${target}`)
          return false
        }
      }

      const { FileBox } = await import('wechaty')
      const fileBox = FileBox.fromUrl(url)
      await targetObj.say(fileBox)

      printLog(`AI自动生成日志: 图片发送成功`)
      return true
    } catch (error) {
      printLog(`AI自动生成日志: 发送图片失败: ${error.message}`)
      return false
    }
  }

  /**
   * 获取所有联系人
   * @returns {Promise<Contact[]>}
   */
  async getContacts() {
    printLog("AI自动生成日志: 获取所有联系人")

    try {
      const contacts = await this.bot.Contact.findAll()
      printLog(`AI自动生成日志: 共找到 ${contacts.length} 个联系人`)
      return contacts
    } catch (error) {
      printLog(`AI自动生成日志: 获取联系人失败: ${error.message}`)
      return []
    }
  }

  /**
   * 获取所有群聊
   * @returns {Promise<Room[]>}
   */
  async getRooms() {
    printLog("AI自动生成日志: 获取所有群聊")

    try {
      const rooms = await this.bot.Room.findAll()
      printLog(`AI自动生成日志: 共找到 ${rooms.length} 个群聊`)
      return rooms
    } catch (error) {
      printLog(`AI自动生成日志: 获取群聊失败: ${error.message}`)
      return []
    }
  }

  /**
   * 检查是否已登录
   * @returns {boolean}
   */
  isLoggedIn() {
    return this.bot.isLoggedIn
  }

  /**
   * 获取登录用户
   * @returns {Promise<Contact|null>}
   */
  async getSelf() {
    try {
      const self = this.bot.userSelf()
      if (self) {
        const name = await self.name()
        printLog(`AI自动生成日志: 当前登录用户: ${name}`)
      }
      return self
    } catch (error) {
      printLog(`AI自动生成日志: 获取登录用户失败: ${error.message}`)
      return null
    }
  }
}

/**
 * 辅助函数：打印日志
 */
function printLog(message) {
  const timestamp = new Date().toLocaleTimeString('zh-CN')
  console.log(`[${timestamp}] ${message}`)
}

export default WechatSDK
