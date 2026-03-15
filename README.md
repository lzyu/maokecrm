# 猫课 CRM 系统 (Maoke CRM)

[![Version](https://img.shields.io/badge/version-V1.0-blue.svg)](https://github.com/your-repo/maokecrm)
[![Status](https://img.shields.io/badge/status-开发中-orange.svg)]()

猫课客户关系管理系统 - 一个专为教育培训机构设计的现代化 CRM 系统，支持销售与咨询师高效协作。

## 📋 项目概述

本系统分为三个阶段开发：
- **V1**: 核心 CRM 功能（当前版本）- 传统系统逻辑实现
- **V2**: Agent 驱动能力 - 引入 AI 助手
- **V3**: 长期规划能力 - 高级分析与自动化

V1 版本目标：在 1-2 个月内上线稳定可用的 CRM 系统，建立完整的客户服务流程。

## ✨ 核心功能

### 👥 用户与权限管理
- 多角色支持：销售、咨询师、管理员、超级管理员
- 细粒度权限控制
- 操作审计日志

### 👨‍💼 客户管理
- 客户档案管理（基本信息、标签、状态）
- 负责人分配机制
- 客户状态跟踪

### 📈 销售管理
- 销售机会管理
- 跟进记录追踪
- 销售漏斗分析

### 🎓 咨询服务
- 服务记录管理
- 咨询分析上传
- 客户反馈收集

### ⏰ 服务提醒
- 智能提醒系统
- 优先级管理
- 完成状态跟踪

### 📊 数据导入
- Excel/CSV 批量导入
- 课程购买记录
- 上课出勤记录
- 导入结果统计

### 📅 客户时间线
- 客户全生命周期事件聚合
- 时间线可视化展示
- 关键节点追踪

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL
- **API 文档**: Swagger/OpenAPI 3.0
- **认证**: JWT Token

### 前端
- **框架**: React + TypeScript
- **UI 库**: Ant Design
- **状态管理**: Redux Toolkit / Zustand
- **构建工具**: Vite

### 部署与工具
- **容器化**: Docker
- **版本控制**: Git
- **文档**: Markdown
- **图表**: Mermaid (ER 图)

## 📁 项目结构

```
maokecrm/
├── README.md                 # 项目说明
├── crm_prd.md               # 产品需求文档
├── restapi.md               # REST API 设计
├── docs/                    # 项目文档
│   ├── crm_v1_api_list.md   # API 接口列表
│   ├── crm_v1_ddl_draft.sql # 数据库 DDL
│   ├── crm_v1_prd_latest.md # V1 最新 PRD
│   ├── crm_v1_swagger.yaml  # Swagger API 规范
│   └── crm_er_diagram.md    # 实体关系图
└── src/                     # 源代码 (待创建)
    ├── backend/            # 后端代码
    ├── frontend/           # 前端代码
    └── database/           # 数据库脚本
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Docker (可选)

### 后端设置
```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install fastapi uvicorn sqlalchemy psycopg2-binary

# 3. 启动数据库
# 使用 Docker 启动 PostgreSQL
docker run -d --name postgres-crm \
  -e POSTGRES_DB=crm_db \
  -e POSTGRES_USER=crm_user \
  -e POSTGRES_PASSWORD=crm_pass \
  -p 5432:5432 postgres:13

# 4. 运行后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置
```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
```

### 数据库初始化
```bash
# 执行 DDL 创建表结构
psql -U crm_user -d crm_db -f docs/crm_v1_ddl_draft.sql
```

## 📚 API 文档

### Swagger UI
启动后端服务后，访问：http://localhost:8000/docs

### API 规范文件
- [完整 API 列表](docs/crm_v1_api_list.md)
- [Swagger YAML](docs/crm_v1_swagger.yaml)
- [REST API 设计](restapi.md)

### 核心 API 端点

#### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `POST /api/v1/users` - 创建用户
- `PUT /api/v1/users/{user_id}` - 更新用户

#### 客户管理
- `GET /api/v1/customers` - 获取客户列表
- `POST /api/v1/customers` - 创建客户
- `GET /api/v1/customers/{customer_id}` - 获取客户详情

#### 销售管理
- `GET /api/v1/sales/opportunities` - 获取销售机会
- `POST /api/v1/sales/followups` - 添加跟进记录

#### 数据导入
- `POST /api/v1/import/course-purchases` - 导入课程购买记录
- `POST /api/v1/import/attendances` - 导入上课记录

## 🗂️ 数据库设计

### 核心表结构
- `users` - 用户表
- `customers` - 客户表
- `sales_opportunities` - 销售机会
- `sales_followups` - 销售跟进
- `service_records` - 服务记录
- `service_reminders` - 服务提醒
- `course_purchase_records` - 课程购买记录
- `course_attendance_records` - 上课记录

### ER 图
查看 [实体关系图](docs/crm_er_diagram.md) 了解数据库结构。

## 🔐 权限说明

| 角色 | 客户管理 | 销售操作 | 服务操作 | 系统管理 |
|------|----------|----------|----------|----------|
| 超级管理员 | 全部 | 全部 | 全部 | 用户管理、审计查看 |
| 普通管理员 | 全部 | 全部 | 全部 | 创建销售/咨询师 |
| 销售 | 负责客户 | 跟进管理 | 查看 | 无 |
| 咨询师 | 查看脱敏 | 查看 | 服务记录、提醒 | 无 |

## 📊 开发进度

### V1.0 版本 (当前)
- ✅ 需求分析与设计
- ✅ API 设计与文档
- ✅ 数据库设计
- 🔄 后端开发
- ⏳ 前端开发
- ⏳ 测试与部署

### 后续规划
- **V2.0**: AI Agent 集成
- **V3.0**: 高级分析功能

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

项目维护者：猫课团队

---

*最后更新：2026-03-15*

