#!/usr/bin/env python3
"""
企业微信配置验证器

验证你的配置是否正确
"""

import json
import sys


def validate_config(config_path: str = None):
    """验证配置文件"""
    print("=" * 60)
    print("企业微信配置验证器")
    print("=" * 60)

    if config_path:
        print(f"\n📋 读取配置文件: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            return False
    else:
        print("\n📋 请输入配置信息:")
        config = {
            "channels": {
                "wecom": {
                    "enabled": True,
                    "corpId": input("企业ID (corpId): ").strip(),
                    "agentId": int(input("应用Agent ID (agentId): ").strip()),
                    "secret": input("应用Secret (secret): ").strip(),
                    "allowFrom": [],
                }
            }
        }

    # 验证配置
    wecom_config = config.get("channels", {}).get("wecom", {})

    print("\n" + "-" * 60)
    print("配置验证:")
    print("-" * 60)

    checks = [
        ("启用状态", wecom_config.get("enabled", False), lambda x: x is True),
        ("企业ID", wecom_config.get("corpId", ""), lambda x: len(x) > 0),
        ("Agent ID", wecom_config.get("agentId", 0), lambda x: x > 0),
        ("Secret", wecom_config.get("secret", ""), lambda x: len(x) > 0),
    ]

    all_valid = True
    for name, value, check_func in checks:
        is_valid = check_func(value)
        status = "✅" if is_valid else "❌"
        print(f"{status} {name}: {value}")
        if not is_valid:
            all_valid = False

    print("-" * 60)

    if all_valid:
        print("\n✅ 配置验证通过！")
        print("\n下一步:")
        print("1. 将配置添加到 ~/.nanobot/config.json")
        print("2. 运行: nanobot gateway")
        print("3. 或者运行测试脚本: python wecom_test.py")
        return True
    else:
        print("\n❌ 配置验证失败，请检查上述项目")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="验证企业微信配置")
    parser.add_argument(
        "--config",
        "-c",
        help="配置文件路径",
        default=None,
    )
    args = parser.parse_args()

    try:
        success = validate_config(args.config)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
