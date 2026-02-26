# 产品需求文档 (PRD)

## 1. Nanobot数据备份恢复功能

### 1.1 需求概述
为nanobot添加数据目录的一键备份和恢复功能，支持将整个 `~/.nanobot` 目录打包为压缩包进行备份和迁移。

### 1.2 需求背景
用户需要在以下场景中使用该功能：
- 备份agent的配置、记忆和会话记录
- 在不同设备间迁移nanobot数据
- 分享特定的nanobot配置

### 1.3 备份恢复范围
备份/恢复的目录为 `~/.nanobot`，包含以下内容：

```
~/.nanobot/
├── config.json         # nanobot配置文件
├── workspace/          # Agent工作区
│   ├── AGENTS.md       # Agent配置指令
│   ├── HEARTBEAT.md    # 心跳服务配置
│   ├── SOUL.md         # Agent灵魂配置
│   ├── TOOLS.md        # 工具配置
│   ├── USER.md         # 用户配置
│   ├── memory/         # 记忆目录
│   │   ├── MEMORY.md   # 长期记忆
│   │   └── HISTORY.md  # 历史记录
│   ├── sessions/       # 会话目录
│   │   └── *.jsonl     # 会话记录文件
│   └── skills/         # 自定义技能目录
├── sessions/           # 全局会话目录（旧版）
├── history/            # CLI命令历史
└── cron/               # 定时任务配置
```

---

## 2. 功能设计

### 2.1 后端接口设计

#### 2.1.1 备份命令
```bash
nanobot backup [OPTIONS]
```

**功能描述：**
- 将 `~/.nanobot` 目录打包为zip文件
- 输出到当前目录，文件名格式：`nanobot-backup-YYYYMMDD-HHMMSS.zip`
- 支持指定输出路径的参数 `--output/-o`
- 显示备份进度和结果

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `--output`, `-o` | string | 指定输出文件路径 (可选) |

**返回值：**
- 成功：显示备份文件路径和大小
- 失败：显示错误信息

#### 2.1.2 恢复命令
```bash
nanobot restore <backup_file> [OPTIONS]
```

**功能描述：**
- 从zip文件解压并恢复 `~/.nanobot` 目录内容
- 支持合并模式或覆盖模式
- 恢复前自动备份现有数据
- 验证压缩包格式和内容完整性

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `backup_file` | string | 要恢复的备份文件路径 |
| `--merge`, `-m` | boolean | 合并模式，保留现有文件 (可选) |
| `--force`, `-f` | boolean | 强制恢复，不提示确认 (可选) |

**返回值：**
- 成功：显示恢复文件数量和状态
- 失败：显示错误信息并回滚

### 2.2 前端交互设计

#### 2.2.1 备份命令交互流程
```
用户执行: nanobot backup
    ↓
显示: [nanobot] 正在备份nanobot数据...
    ↓
显示: ✓ 压缩完成: nanobot-backup-20250226-163000.zip (25.5 KB)
    ↓
退出
```

#### 2.2.2 恢复命令交互流程
```
用户执行: nanobot restore backup.zip
    ↓
显示: [nanobot] 恢复nanobot数据
显示:   备份文件: backup.zip
显示:   目标目录: ~/.nanobot
    ↓
显示:   现有数据将被完全覆盖并自动备份
    ↓
提示: 是否继续? [Y/n]
    ↓ (用户确认)
显示: ✓ 恢复完成
显示:   恢复文件: 15
    ↓
退出
```

---

## 3. 技术实现

### 3.1 文件结构
```
nanobot/
├── cli/
│   ├── commands.py       # backup/restore命令
│   └── backup.py         # 备份恢复功能模块
```

### 3.2 核心模块设计

#### 3.2.1 备份模块 (nanobot/cli/backup.py)
```python
def backup_nano_data(
    data_dir: Path,
    output_path: Path | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> Path:
    """备份nanobot数据目录为zip压缩包

    Args:
        data_dir: ~/.nanobot目录路径
        output_path: 输出文件路径，None则自动生成

    Returns:
        导出的zip文件路径
    """
```

#### 3.2.2 恢复模块 (nanobot/cli/backup.py)
```python
def restore_nano_data(
    archive_path: Path,
    data_dir: Path,
    merge: bool = False,
    backup: bool = True,
    on_progress: Callable[[str], None] | None = None,
) -> dict:
    """从备份压缩包恢复nanobot数据目录

    Args:
        archive_path: 压缩包文件路径
        data_dir: 目标~/.nanobot目录
        merge: 是否合并模式（保留现有文件）
        backup: 是否自动备份现有数据

    Returns:
        恢复结果统计信息
    """
```

---

## 4. 测试计划

### 4.1 后端接口测试
- 测试正常备份流程
- 测试指定输出路径
- 测试空目录备份
- 测试大型目录备份
- 测试恢复正常备份文件
- 测试恢复损坏的压缩包（应失败）
- 测试合并模式恢复
- 测试覆盖模式恢复
- 测试自动备份功能
- 测试恢复失败回滚

### 4.2 前端交互测试
使用命令行测试脚本：
- 测试备份命令输出格式
- 测试恢复命令交互流程
- 测试错误提示信息

---

## 5. 实施步骤
1. 创建backup模块（nanobot/cli/backup.py）
2. 在CLI commands.py中添加backup/restore命令
3. 编写单元测试
4. 进行集成测试
