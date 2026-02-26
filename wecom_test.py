#!/usr/bin/env python3
"""
WeChat Work (企业微信) 测试脚本

使用方法:
1. 配置 ~/.nanobot/config.json 添加企业微信配置
2. 运行: python wecom_test.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from nanobot.channels.wechat import WeComChannel, test_wecom_connection


async def main():
    """主测试函数"""
    print("=" * 50)
    print("企业微信 (WeChat Work) 测试")
    print("=" * 50)

    # 请替换为你的实际配置
    CORP_ID = input("请输入企业ID (Corp ID): ").strip()
    AGENT_ID = int(input("请输入应用Agent ID: ").strip())
    SECRET = input("请输入应用Secret: ").strip()
    USER_ID = input("请输入要发送消息的用户ID (员工账号): ").strip()

    print("\n正在测试连接...")
    print(f"- 企业ID: {CORP_ID}")
    print(f"- 应用Agent ID: {AGENT_ID}")
    print(f"- 目标用户: {USER_ID}")
    print("-" * 50)

    success = await test_wecom_connection(CORP_ID, AGENT_ID, SECRET, USER_ID)

    if success:
        print("\n✅ 测试成功！请检查企业微信是否收到消息。")
    else:
        print("\n❌ 测试失败，请检查配置和日志。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
