# My Claude Code

基于 OpenAI API 的 AI 编程助手，支持工具调用、任务规划和 MCP 协议。

## 功能特性

- **ReAct Agent 循环** — 自动推理 + 工具调用，循环执行直到任务完成
- **文件操作** — 读取、写入、编辑、搜索、Glob 查找
- **终端执行** — 安全的 Bash 命令执行，内置危险命令拦截
- **网页抓取** — 获取网页内容并转为 Markdown
- **任务规划** — 多步骤任务拆分、状态跟踪、顺序执行
- **MCP 协议** — 支持 Stdio/SSE 两种传输方式，可扩展外部工具

## 快速开始

### 1. 安装依赖

```bash
pip install openai python-dotenv mcp anyio
```

### 2. 配置环境变量

创建 `.env` 文件：

```
BASE_URL="https://api.deepseek.com"
API_KEY="your-api-key"
MODEL="deepseek-v4-pro"
```

### 3. 配置 MCP 服务器（可选）

编辑 `agent/mcps/mcp.json`：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"]
    }
  }
}
```

也支持 SSE 模式：

```json
{
  "mcpServers": {
    "my-sse-server": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### 4. 运行

```bash
python -m agent.Client
```

输入 `exit`、`quit` 或 `q` 退出。

## 项目结构

```
agent/
├── Agent.py              # ReAct Agent 主循环
├── Client.py             # 入口，工具注册与交互循环
├── data.py               # 数据模型（Message, ChatResponse, ToolCallInfo）
├── llm/
│   └── base.py           # LLM 客户端封装
├── mcps/
│   └── mcp.json          # MCP 服务器配置
└── tools/
    ├── bash/
    │   └── terminal.py   # 终端工具
    ├── file/
    │   ├── edit.py       # 文件编辑
    │   ├── glob.py       # 文件搜索
    │   ├── grep.py       # 内容搜索
    │   ├── read.py       # 文件读取
    │   └── write.py      # 文件写入
    ├── mcp/
    │   ├── adapter.py    # MCP 工具适配器
    │   ├── manager.py    # MCP 客户端管理
    │   └── protocol.py   # MCP 协议定义
    ├── planning/
    │   ├── add_tasks.py  # 添加任务
    │   ├── list_tasks.py # 列出任务
    │   ├── planner.py    # 任务管理器
    │   └── update_task.py# 更新任务
    ├── skills/
    │   ├── data.py       # 技能数据
    │   └── skills.py     # 技能管理
    ├── registry.py       # 工具注册中心
    └── web/
        └── fetch.py      # 网页抓取
```

## License

MIT
