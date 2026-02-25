/**
 * @file index.js
 * @description WechatSDK 入口文件
 */

export { WechatSDK } from './WechatSDK.js'

// 导出便捷创建函数
export async function createWechatSDK(options) {
  const { WechatSDK } = await import('./WechatSDK.js')
  return new WechatSDK(options)
}

export default WechatSDK
