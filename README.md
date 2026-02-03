# Cookie Chat Group Bot

一个功能丰富的Telegram群组机器人，具有成就系统、徽章系统、卡片系统和完整的管理界面。

## 功能特性

### 核心功能
- **成就系统**：用户可以通过在群组中活动解锁各种成就
- **徽章系统**：用户可以获得和展示不同的徽章
- **卡片系统**：用户可以使用经验值购买卡片，卡片具有不同的功能和价值
- **经验值系统**：用户通过在群组中发送消息获得经验值

### 管理工具
- **命令行界面 (CLI)**：通过命令行管理机器人和查看数据
- **图形用户界面 (GUI)**：使用PySide6实现的桌面应用，提供直观的数据管理和可视化

### 数据管理
- **数据库统计**：查看群组消息总数、用户总数、群组数量和数据库占用空间
- **数据导出**：将数据导出为CSV格式
- **批量操作**：支持对多个用户进行批量经验值操作

## 技术栈

- **Python 3.12++**
- **python-telegram-bot**：用于实现Telegram机器人
- **SQLite**：用于本地数据库存储
- **PySide6**：用于实现图形用户界面
- **click** 和 **rich**：用于实现命令行界面
- **toml**：用于配置文件管理
- **uv**：用于依赖管理

## 安装与配置

### 前置要求
- Python 3.12 或更高版本
- uv 依赖管理工具
- Telegram Bot API Token

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/AImixAE/cookie-v2bot.git
   cd cookie-v2bot
   ```

2. **安装依赖**
   ```bash
   uv sync
   ```

3. **配置环境变量**
   - 复制 `.env.example` 文件为 `.env`
   - 在 `.env` 文件中填入你的 Telegram Bot Token
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ```

4. **配置成就、徽章和卡片**
   - 编辑 `config/achievements.toml` 配置成就
   - 编辑 `config/badges.toml` 配置徽章
   - 编辑 `config/cards.toml` 配置卡片

## 使用方法

### 启动机器人
```bash
uv run run.py bot
```

### 使用命令行工具
```bash
# 列出所有群组
uv run run.py cli list-groups

# 列出所有用户
uv run run.py cli list-users

# 查看用户详细信息
uv run run.py cli user-detail <user_id>

# 查看排行榜
uv run run.py cli leaderboard <chat_id>

# 对用户执行操作
uv run run.py cli user-operation <user_id>

# 清空数据库（危险操作）
uv run run.py cli clear-database
```

### 使用图形界面
```bash
uv run run.py gui
```

## 项目结构

```
cookie-chat-group-bot-v2/
├── config/                # 配置文件目录
│   ├── achievements.toml  # 成就配置
│   ├── badges.toml        # 徽章配置
│   ├── cards.toml         # 卡片配置
│   └── config.toml        # 基本配置
├── data/                  # 数据目录
│   └── bot.db             # SQLite 数据库文件
├── src/                   # 源代码目录
│   ├── bot.py             # 机器人主要逻辑
│   ├── cli.py             # 命令行工具
│   ├── config_loader.py   # 配置加载器
│   ├── core.py            # 核心功能
│   ├── database.py        # 数据库操作
│   └── gui.py             # 图形用户界面
├── .env                   # 环境变量
├── .env.example           # 环境变量示例
├── pyproject.toml         # 项目配置
├── run.py                 # 项目入口点
└── README.md              # 项目说明
```

## 配置文件说明

### achievements.toml
定义用户可以解锁的成就，包括成就名称、描述、解锁条件等。

### badges.toml
定义用户可以获得的徽章，包括徽章名称、描述、获取条件等。

### cards.toml
定义用户可以购买的卡片，包括卡片名称、描述、价格（经验值）等。

### config.toml
定义机器人的基本配置，如消息处理设置等。

## 数据库结构

数据库包含以下主要表：

- **users**：存储用户信息
- **chats**：存储群组信息
- **messages**：存储消息记录
- **achievements**：存储用户成就
- **badges**：存储用户徽章
- **cards**：存储用户卡片

## 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request 并描述您的更改