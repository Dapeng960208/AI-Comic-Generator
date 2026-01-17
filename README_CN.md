# AI Comic Generator

[English](./README.md) | [中文](./README_CN.md)

一个基于 AI 的全流程漫画创作辅助工具，集成了故事生成、分镜拆解、角色设定、一致性控制和批量绘图功能。

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![Vue](https://img.shields.io/badge/Frontend-Vue3-green)

## ✨ 核心理念
*   **JSON 驱动的工作流**: 本项目的核心思想是通过结构化的 JSON 数据来管理整个漫画创作流程。从故事大纲到角色设定，再到分镜细节，所有内容都以 JSON 格式存储和处理。这确保了数据的一致性、版本控制能力，以及与 AI 模型的高效集成。
*   **全局配置 (Global Config JSON)**: 一个集中式的配置系统，用于掌控整个项目的艺术方向。
    *   **风格一致性**: 定义全局画风（如“赛博朋克”、“水墨风”）、画幅比例和色调，确保生成的所有分镜都遵循统一的视觉语言。
    *   **角色与布局控制**: 管理全局角色特征和分镜布局偏好（如分镜间距、边框样式）。
    *   **动态同步**: 对全局配置的修改会自动同步应用到所有分镜中，无需手动逐格调整，即可快速迭代整体风格。

## ✨ 核心功能

*   **项目管理**: 支持多项目管理，每个项目独立保存故事、角色和分镜数据。
*   **智能编剧**: 输入简单的故事点子，AI 自动扩充情节并拆分为专业的漫画分镜脚本 (JSON 格式)。
*   **角色工坊**:
    *   自动从故事中提取角色并生成详细的人物设定（三视图）。
    *   **角色一致性**: 绘图时自动引用角色设定图作为参考（Image-to-Image）。
    *   **合并与去重**: 支持手动合并重复生成的角色（如“马管家”和“马老”）。
*   **分镜编辑器**:
    *   可视化编辑每一格分镜的提示词、角色和动作。
    *   支持单格重绘、批量生成。
    *   **上下文感知**: 生成分镜时自动读取前序分镜和角色图，保持画风和剧情连贯性。
*   **风格控制**:
    *   全局风格配置（如“赛博朋克”、“水墨风”），强制 AI 遵循设定。
    *   支持自定义对话框、边框样式。
*   **后台任务**: 耗时的批量生图任务在后台运行，支持进度实时查看。

## 🛠️ 技术栈

### Backend (后端)
*   **Framework**: FastAPI
*   **Database**: SQLite + SQLModel
*   **AI Service**: Google Gemini (目前仅支持 Google 最新模型)
    *   **文本模型**: `gemini-3-flash-preview`
    *   **图像模型**: `gemini-3-pro-image-preview`
*   **Task Queue**: FastAPI BackgroundTasks

### Frontend (前端)
*   **Framework**: Vue 3 + Vite
*   **UI Library**: Element Plus
*   **State Management**: Pinia
*   **HTTP Client**: Axios
*   **Package Manager**: pnpm

## 🚀 快速开始

### 前置要求
*   Python 3.9+
*   Node.js 16+
*   pnpm
*   Google Cloud API Key (需开通 Gemini API 权限)

### 1. 后端配置

进入 `backend` 目录：

```bash
cd backend
```

创建虚拟环境并安装依赖：

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

使用 Alembic 初始化数据库：

```bash
# 初始化 alembic (如果尚未初始化)
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 应用迁移到数据库
alembic upgrade head
```

启动后端服务：

```bash
# Windows (使用提供的脚本)
..\start_backend.bat

# 或者手动运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端配置

进入 `frontend` 目录：

```bash
cd frontend
```

安装依赖：

```bash
pnpm install
```

启动前端服务：

```bash
# Windows (使用提供的脚本)
..\start_frontend.bat

# 或者手动运行
pnpm dev
```

访问浏览器：`http://localhost:5173`

## 📖 使用指南

1.  **配置模型**:
    *   在顶部导航栏点击 "Models"。
    *   添加新的配置并填入你的 Google API Key。
    *   确保模型类型设置正确（Text/Image）并已启用。

2.  **创建项目**: 在首页点击“新建项目”，输入漫画标题和简介。
3.  **故事与配置**:
    *   输入你的故事大纲。
    *   设置全局风格（如“日系少年漫”）、画幅比例等。
    *   点击“生成分镜配置”，AI 将生成角色表和分镜脚本。
    
    ![故事与配置](assets/story_config.png)

4.  **角色工坊**:
    *   查看 AI 生成的角色设定。
    *   点击“绘制”生成角色立绘。
    *   如有重复角色，使用“合并角色”功能进行清理。

    ![角色工坊](assets/character_studio.png)

5.  **分镜编辑**:
    *   在分镜列表中检查每一格的描述。
    *   点击“生成图片”或“一键生成所有”开始绘制漫画。
    *   点击图片可查看大图，支持下载。

    ![分镜编辑](assets/storyboard.png)

## 🖼️ 示例展示

您可以在 [example/](./example/) 目录中找到一个完整的示例项目，包含故事脚本、角色设定图和生成的分镜画面。

### 角色设定

<div align="center">
  <img src="example/characters/Shen%20Tianhu.png" width="200" alt="沈天虎" />
  <img src="example/characters/Butler%20Ma.png" width="200" alt="马管家" />
  <img src="example/characters/苏媚瑶.png" width="200" alt="苏媚瑶" />
</div>

### 漫画分镜

<div align="center">
  <img src="example/panels/panel_1_1.png" width="45%" />
  <img src="example/panels/panel_1_2.png" width="45%" />
</div>
<div align="center">
  <img src="example/panels/panel_1_3.png" width="45%" />
  <img src="example/panels/panel_1_4.png" width="45%" />
</div>

## 📁 目录结构

```
aImanhua/
├── backend/            # FastAPI 后端
│   ├── app/            # 应用代码
│   ├── static/         # 生成的图片和临时文件存储
│   └── ...
├── frontend/           # Vue3 Frontend
│   ├── src/            # 页面与组件
│   └── ...
└── ...
```

## � 联系方式

邮箱: gjp960208@gmail.com

## �📝 License

MIT License

Copyright (c) 2025 FunASR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
