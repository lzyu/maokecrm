# 猫课客户数据库系统 PRD（分阶段版本）

本 PRD 将系统能力拆分为三个阶段：

V1：核心系统功能（不依赖 Agent）
V2：Agent 驱动能力
V3：产品长期规划能力

目标是先快速上线一个稳定 CRM，再逐步加入 AI Agent 能力。



![Gemini_Generated_Image_4jz4fc4jz4fc4jz4](F:\downloads\chrome download\Gemini_Generated_Image_4jz4fc4jz4fc4jz4.png)



---

# 一、V1 版本（必须实现功能）

V1 只包含 **确定性系统功能**，全部由传统系统逻辑实现，不依赖 Agent。

目标：

- 上线可用的 CRM
- 建立客户服务流 Pipeline
- 支持销售与咨询师协作


## 1 用户角色与权限

角色：

- 销售
- 咨询师
- 普通管理员
- 超级管理员

权限规则：

超级管理员

- 管理所有用户
- 新建 / 删除管理员

普通管理员

- 新建销售
- 新建咨询师
- 修改销售与咨询师
- 删除客户
- 查看所有客户

销售

- 创建客户
- 编辑客户
- 添加跟进记录
- 查看咨询记录

咨询师

- 查看客户信息（手机号与微信匿名化）
- 创建服务记录
- 创建服务提醒
- 上传咨询分析


---

# 2 客户管理模块

客户基础信息：

- 客户姓名
- 手机号
- 微信
- 公司名称
- 行业
- 来源渠道
- 客户负责人
- 创建时间


客户状态（固定枚举）：

- 潜在客户
- 意向客户
- 成交客户
- 流失客户

状态修改：

- 销售
- 咨询师


客户标签

标签类型：

- 销售标签
- 咨询师标签


---

# 3 销售管理模块（客户服务流 Pipeline）

Pipeline 包含以下内容：

1 销售跟进记录
2 销售机会
3 课程购买记录
4 上课记录
5 咨询分析记录
6 服务提醒


## 3.1 销售跟进记录

字段：

- 客户
- 跟进时间
- 沟通方式
- 沟通内容
- 跟进备注


## 3.2 销售机会

字段：

- 销售阶段
- 预计成交时间
- 预计成交金额


## 3.3 课程购买记录

V1 实现方式：

- Excel 批量导入

后续：

- 从课程系统每日同步


## 3.4 上课记录

V1 实现方式：

- Excel 批量导入

后续：

- 课程系统定时同步


## 3.5 咨询分析记录

由咨询师上传。

销售可以查看。


## 3.6 服务提醒

由咨询师创建。

销售可以查看。

提醒会保存到客户服务流。


---

# 4 咨询师服务模块

## 4.1 服务记录

字段：

- 服务时间
- 服务内容
- 客户反馈（客户问题）
- 客户满意度


说明：

V1 暂不记录解决方案结构化。


## 4.2 咨询分析上传

咨询师可以上传：

- 咨询总结
- 客户问题
- 咨询结论


---

# 5 数据导入

支持数据导入：

- 课程购买记录
- 上课记录

导入方式：

- Excel
- CSV


---

# 6 系统管理

管理员可使用。

用户管理：

普通管理员：

- 新建销售
- 新建咨询师
- 修改成员

超级管理员：

- 新建管理员
- 删除管理员


客户权限：

销售

- 创建客户
- 编辑客户

客户删除

- 仅管理员


---

# 二、V2 版本（Agent 能力实现）

V2 开始引入 AI Agent（例如 OpenClaw）。

目标：

- 利用 Agent 自动分析数据
- 提供销售与服务辅助


## 1 咨询记录自动总结 Agent

输入：

- 咨询会议记录

输出：

- 服务记录
- 客户问题
- 咨询结论


作用：

减少咨询师录入成本。


---

# 2 客户分析 Agent

输入：

- 客户标签
- 服务记录
- 跟进记录


输出：

- 客户画像
- 客户痛点
- 客户风险


---

# 3 销售建议 Agent

分析：

- 客户状态
- 咨询记录
- 历史跟进


生成：

- 推荐销售策略
- 推荐沟通话术


---

# 4 自动提醒 Agent

系统定期扫描：

- 超过30天未跟进客户
- 课程即将结束客户


自动生成提醒。


---

# 5 客户健康度评分 Agent

根据数据计算：

- 跟进频率
- 服务次数
- 满意度


输出：

客户健康度评分。


---

# 三、V3 版本（产品长期规划）

V3 是完整 AI CRM 能力。


## 1 AI 销售助手

销售打开客户页面时：

系统自动展示：

- 客户画像
- 推荐话术
- 推荐产品


---

# 2 自动销售报告

自动生成：

- 周报
- 月报
- 转化分析


---

# 3 客户分群系统

自动识别客户类型：

- 高价值客户
- 潜在续费客户
- 流失风险客户


---

# 4 自动数据分析

通过大模型生成：

- 销售分析
- 客户价值分析
- 服务效果分析


---

# 5 数据自动同步

与以下系统集成：

- 课程系统
- 支付系统
- 客户管理系统


---

# 四、版本路线总结

V1

目标：上线可用 CRM

核心能力：

- 客户管理
- 销售跟进
- 咨询服务记录
- 服务流 Pipeline
- 数据导入


V2

目标：引入 Agent

能力：

- 咨询记录自动总结
- 客户分析
- 销售建议
- 自动提醒
- 客户健康度评分


V3

目标：完整 AI CRM

能力：

- AI 销售助手
- 自动报告
- 客户分群
- 数据自动分析
- 多系统数据集成


---

# 五、AI CRM + Agent 系统架构设计（升级版）

本系统在 V1 CRM 的基础上，通过 Agent 层逐步演进为 AI CRM。

整体架构分为四层：

1. 应用层（CRM UI）
2. 业务系统层（CRM Core）
3. Agent 层
4. 数据层


## 5.1 系统整体架构

```
Frontend (CRM UI)
       │
       │
CRM Core Backend
       │
       │
Agent Runtime Layer
(OpenClaw / Agent Framework)
       │
       │
Data Layer
(Database + Analytics)
```


## 5.2 CRM Core（核心业务系统）

CRM Core 负责所有确定性业务逻辑：

- 客户管理
- 用户权限
- 客户服务流 Pipeline
- 销售跟进
- 服务记录
- 数据导入

特点：

- 数据真实来源
- 系统核心业务逻辑
- Agent 不直接修改核心数据


## 5.3 Agent Runtime 层

Agent Runtime 负责运行 AI Agent。

建议使用：

- OpenClaw Agent Runtime

Agent 通过以下方式工作：

- 读取 CRM 数据
- 调用工具（Tools）
- 生成分析结果


## 5.4 Agent Tool 设计

Agent 通过 Tools 与系统交互。

建议提供以下工具：

Customer Tools

- get_customer_profile
- get_customer_history

Sales Tools

- get_followups
- get_sales_pipeline

Service Tools

- get_service_records
- get_consultation_analysis

Reminder Tools

- create_reminder
- list_reminders

Analytics Tools

- query_sales_metrics


## 5.5 Agent 列表设计

系统建议设计以下 Agent：


### Customer Analysis Agent

职责：

分析客户情况。

输入：

- 客户标签
- 跟进记录
- 服务记录

输出：

- 客户画像
- 客户痛点
- 客户风险


---

### Sales Suggestion Agent

职责：

为销售生成跟进建议。

输入：

- 客户状态
- 咨询分析
- 跟进历史

输出：

- 推荐销售动作
- 推荐话术


---

### Reminder Agent

职责：

自动检测客户风险并创建提醒。

扫描规则示例：

- 超过30天未跟进
- 课程即将结束

输出：

- 自动提醒


---

### Reporting Agent

职责：

自动生成销售报告。

输入：

- 销售数据
- 客户数据

输出：

- 周报
- 月报


---

## 5.6 Agent Workflow

Agent 通过定时任务或事件触发。

示例 Workflow：

客户数据变化

```
Customer Updated
      │
      │
Customer Analysis Agent
      │
      │
更新客户画像
```


定时扫描 Workflow

```
Daily Cron Job
      │
      │
Reminder Agent
      │
      │
生成提醒
```


## 5.7 Agent Memory

Agent 需要保存上下文记忆。

建议使用两类 Memory：

短期记忆：

- 当前客户上下文

长期记忆：

- 客户分析结果
- 客户画像


存储方式：

- 数据库存储
- 向量数据库（可选）


## 5.8 AI CRM 最终形态

系统最终将演进为 AI CRM：

功能包括：

- 自动客户分析
- 自动销售建议
- 自动提醒
- 自动报告
- AI 销售助手


销售打开客户页面时：

系统自动展示：

- 客户画像
- 推荐销售策略
- 风险提示


---

# 六、技术实现建议

推荐技术架构：

Backend

- Python (FastAPI)

Database

- PostgreSQL

Cache

- Redis

Agent Runtime

- OpenClaw

Queue

- Celery / Redis Queue


Agent 任务调度：

- 定时任务
- 事件触发


---

# 七、实施路线

第一阶段（1-2个月）

实现：

- CRM Core
- 客户管理
- 服务流 Pipeline


第二阶段（2-3个月）

接入 Agent：

- 客户分析
- 销售建议
- 自动提醒


第三阶段（长期）

AI CRM：

- 自动报告
- 客户分群
- AI 销售助手


---

# 八、AI CRM 数据模型设计（核心数据结构）

为了保证系统稳定性与数据安全，CRM 数据模型需要区分三类数据：

1. 业务核心数据（Core Business Data）
2. Agent 分析数据（AI Analysis Data）
3. 系统事件与日志数据（System Events）

原则：

- 核心业务数据只允许系统或人工修改
- Agent 默认 **只读核心业务数据**
- Agent 的输出写入 **AI 分析表**


## 8.1 用户与权限相关表

users

字段：

- id
- name
- role_id
- phone
- email
- status
- created_at


roles

字段：

- id
- role_name

角色枚举：

- sales
- consultant
- admin
- super_admin


---

# 九、客户核心数据模型

## 9.1 客户表

customers

字段：

- id
- name
- phone
- wechat
- company_name
- industry
- source_channel
- owner_user_id
- customer_status
- created_at
- updated_at


customer_status 枚举：

- potential
- interested
- converted
- lost



## 9.2 标签系统


Tags

字段：

- id
- tag_name
- tag_type


Tag 类型：

- sales
- consultant



customer_tags

字段：

- id
- customer_id
- tag_id
- created_by


---

# 十、客户服务流 Pipeline 数据模型

Pipeline 是 CRM 的核心。


## 10.1 销售跟进记录

sales_followups

字段：

- id
- customer_id
- sales_id
- followup_time
- contact_method
- content
- created_at



## 10.2 销售机会

sales_opportunities

字段：

- id
- customer_id
- stage
- expected_close_date
- expected_amount



## 10.3 课程购买记录

course_purchase_records

字段：

- id
- customer_id
- course_name
- purchase_date
- amount
- import_source



## 10.4 上课记录

course_attendance_records

字段：

- id
- customer_id
- course_name
- class_date
- status



## 10.5 咨询服务记录

service_records

字段：

- id
- customer_id
- consultant_id
- service_time
- service_content
- customer_feedback
- satisfaction_score



## 10.6 咨询分析记录

consultation_analysis

字段：

- id
- customer_id
- consultant_id
- analysis_summary
- uploaded_file
- created_at



## 10.7 服务提醒

service_reminders

字段：

- id
- customer_id
- created_by
- reminder_type
- reminder_time
- status


提醒类型：

- followup
- renewal
- progress_check


---

# 十一、AI Agent 数据模型

Agent 的输出必须写入 **独立 AI 表**。


## 11.1 客户画像

ai_customer_profiles

字段：

- id
- customer_id
- profile_summary
- pain_points
- risk_level
- generated_at



## 11.2 销售建议

ai_sales_suggestions

字段：

- id
- customer_id
- suggestion_text
- recommended_action
- generated_at



## 11.3 客户健康度

ai_customer_health_scores

字段：

- id
- customer_id
- health_score
- score_reason
- generated_at



## 11.4 自动提醒

ai_generated_reminders

字段：

- id
- customer_id
- reminder_reason
- suggested_action
- created_at



---

# 十二、Agent 数据访问边界设计

为了防止 AI 误操作数据，需要明确访问边界。


## 12.1 Agent 只读数据

Agent 可以读取：

- customers
- customer_tags
- sales_followups
- service_records
- consultation_analysis
- purchase_records


这些是分析输入。



## 12.2 Agent 可以写入的数据

Agent 只允许写入：

- ai_customer_profiles
- ai_sales_suggestions
- ai_customer_health_scores
- ai_generated_reminders



## 12.3 Agent 不允许直接修改

Agent 不允许修改：

- customers
- sales_followups
- service_records
- purchase_records



任何修改必须通过：

- 人工确认
- 或系统逻辑


---

# 十三、客户 Pipeline 统一时间线

为了方便 UI 展示，可以构建一个统一 Timeline。


pipeline_events

字段：

- id
- customer_id
- event_type
- reference_id
- created_at


事件类型：

- followup
- service_record
- consultation
- purchase
- reminder



UI 可以按时间展示客户历史。


---

# 十四、AI CRM 数据流

系统数据流：


CRM Core Data

```
Customers
Followups
Service Records
Course Data
```


Agent Analysis

```
Customer Analysis Agent
        │
        │
AI Tables
```


UI 展示

```
Customer Profile
Sales Suggestions
Health Score
```


---

# 十五、未来扩展（可选）

如果未来数据量变大，可以增加：


Vector Database

用于存储：

- 咨询记录 embedding
- 客户对话 embedding


Event Bus

用于触发 Agent：

- Kafka
- Redis Streams


Data Warehouse

用于 BI：

- ClickHouse
- BigQuery



---

# 十六、最终系统结构

完整系统：


```
CRM Application

├── Customer Management
├── Sales Pipeline
├── Service Records

AI Layer

├── Customer Analysis Agent
├── Sales Suggestion Agent
├── Reminder Agent
├── Reporting Agent

Data Layer

├── Core CRM Tables
├── AI Analysis Tables
└── Event Tables
```


该架构可以稳定支持：

- CRM 基础业务
- AI 分析能力
- Agent 自动化能力

