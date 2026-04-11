# 猫课 CRM 项目总结

本文档基于 PRD（`docs/crm_v1_prd_latest.md`）、后端路由（`backend/app/api/v1`）与前端路由（`frontend/src/App.tsx`）整理。**权限以当前代码为准**；与 PRD 不一致处见文末「PRD 与实现的差异」。

---

## 一、现有功能概览（V1）

| 领域 | 能力 |
|------|------|
| **认证** | JWT 登录 / 刷新 / 登出，当前用户信息 |
| **用户与角色** | 角色列表；用户分页列表、创建、查看、更新、删除（删除仅超管） |
| **客户** | 分页列表（关键词/状态/负责人/标签筛选）、创建、详情、更新、软删除、更新状态 |
| **标签** | 列表、创建、更新、删除（删除需管理员及以上） |
| **销售跟进** | 跟进列表、新增、删除（软删除） |
| **销售机会** | 列表、看板、详情、创建、更新、阶段更新、删除 |
| **服务记录** | 列表、创建（咨询师 / 管理员 / 超管） |
| **服务提醒** | 列表、创建、标记完成、删除 |
| **数据导入** | 导入批次与失败行查询；课程购买 / 上课记录文件导入 |
| **客户时间线** | 按客户聚合跟进、服务、机会、提醒、购课、上课、咨询分析、创建与状态变更等事件 |
| **审计** | 日志分页与筛选、统计、动作类型与资源类型字典 |
| **前端页面** | 登录、工作台、客户列表/详情、跟进、机会、服务记录、提醒；**导入 / 用户 / 审计 / 设置** 仅 `admin` / `super_admin` 可进路由 |

---

## 二、API 清单（前缀均为 `/api/v1`）

### 认证 `prefix=/auth`

| 方法 | 路径 |
|------|------|
| POST | `/auth/login` |
| POST | `/auth/refresh` |
| POST | `/auth/logout` |
| GET | `/auth/me` |

### 角色 `prefix=/roles`

| 方法 | 路径 |
|------|------|
| GET | `/roles` |

### 用户 `prefix=/users`

| 方法 | 路径 |
|------|------|
| GET | `/users` |
| POST | `/users` |
| GET | `/users/{user_id}` |
| PUT | `/users/{user_id}` |
| DELETE | `/users/{user_id}` |

### 客户 `prefix=/customers`

| 方法 | 路径 |
|------|------|
| GET | `/customers` |
| POST | `/customers` |
| GET | `/customers/{customer_id}` |
| PUT | `/customers/{customer_id}` |
| DELETE | `/customers/{customer_id}` |
| PUT | `/customers/{customer_id}/status` |

### 标签 `prefix=/tags`

| 方法 | 路径 |
|------|------|
| GET | `/tags` |
| POST | `/tags` |
| PUT | `/tags/{tag_id}` |
| DELETE | `/tags/{tag_id}` |

### 跟进 `prefix=/followups`

| 方法 | 路径 |
|------|------|
| GET | `/followups` |
| POST | `/followups` |
| DELETE | `/followups/{followup_id}` |

### 销售机会 `prefix=/opportunities`

| 方法 | 路径 |
|------|------|
| GET | `/opportunities` |
| GET | `/opportunities/kanban` |
| POST | `/opportunities` |
| GET | `/opportunities/{opportunity_id}` |
| PUT | `/opportunities/{opportunity_id}` |
| PUT | `/opportunities/{opportunity_id}/stage` |
| DELETE | `/opportunities/{opportunity_id}` |

### 服务记录 `prefix=/services`

| 方法 | 路径 |
|------|------|
| GET | `/services/records` |
| POST | `/services/records` |

### 提醒 `prefix=/reminders`

| 方法 | 路径 |
|------|------|
| GET | `/reminders` |
| POST | `/reminders` |
| PUT | `/reminders/{reminder_id}/done` |
| DELETE | `/reminders/{reminder_id}` |

### 导入 `prefix=/imports`

| 方法 | 路径 |
|------|------|
| GET | `/imports/batches` |
| GET | `/imports/batches/{batch_id}/errors` |
| POST | `/imports/course-purchases` |
| POST | `/imports/attendance` |

### 时间线 `prefix=/timeline`

| 方法 | 路径 |
|------|------|
| GET | `/timeline/{customer_id}` |

### 审计 `prefix=/audit`

| 方法 | 路径 |
|------|------|
| GET | `/audit/logs` |
| GET | `/audit/stats` |
| GET | `/audit/actions` |
| GET | `/audit/resource-types` |

### 系统（不在 v1 前缀下）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/healthz` | 健康检查 |
| GET | `/readyz` | 就绪检查 |
| GET | `/api/openapi.json` | OpenAPI 规范 |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

---

## 三、各角色在代码中的能力（摘要）

角色层级：`super_admin` > `admin` > `sales` > `consultant`（见 `backend/app/core/permissions.py`）。

### super_admin（超级管理员）

- 与用户 `admin` 同属 **管理员及以上**（`is_admin_or_above`）：用户管理、角色列表、审计、导入、按负责人筛选客户等。
- **唯一**可调用 **`DELETE /users/{id}`** 删除用户（且不能删除自己）。

### admin（管理员）

- 用户：列表 / 创建 / 查看 / 更新（不可删用户）。
- 审计、导入、导入批次与错误查询。
- 客户：**可删客户**；创建客户时可指定 `owner_user_id`；列表可按 `owner_user_id` 筛选。
- 标签：**可删标签**；创建/更新标签与所有登录用户相同。
- 跟进 / 机会 / 提醒：可看全量或按接口规则操作。
- 服务记录：可创建（与咨询师相同）。

### sales（销售）

- 客户：当前 `customers.py` 中 **`can_access_all_customers` / `can_modify_customer` 实现为恒为真**，列表/详情/更新在实现上**未按负责人收紧**（与 PRD「仅负责客户」不一致）。
- 创建客户时 **负责人强制为本人**（不可代指定他人）。
- **不可** 删除客户。
- 跟进：列表仅自己的；仅能给 **负责人为自己的客户** 添加跟进；可删除自己的跟进。
- 机会：列表/看板可看全部；创建/改/删时若非管理员，需 **`owner_user_id` 为自己** 的机会。
- 提醒：完成/删除需为 **执行人本人** 或管理员。
- 时间线：`permissions.can_access_all_customers` 为假 → **仅本人负责客户** 的时间线。
- 前端：**不能** 进入 `/imports`、`/users`、`/audit`、`/settings`（仅 admin/super_admin）。

### consultant（咨询师）

- 与 sales 类似：受 **时间线 / 跟进 / 机会 / 提醒** 等接口中的 `is_admin_or_above` 与客户负责人规则约束。
- **可** `POST /services/records` 创建服务记录。
- PRD 中的 **手机号/微信脱敏**：`masking` 模块已实现，但 `customers.py` 的 `apply_masking` 当前 **直接返回原数据、未脱敏**。
- 前端同样 **无** 管理类菜单路由。

---

## 四、PRD 与实现的差异

1. **客户数据范围**：PRD 要求销售仅看自己负责客户；代码里客户模块使用了 **本地** `can_access_all_customers` / `can_modify_customer`（恒为真），而 **时间线** 使用 **`permissions.can_access_all_customers`**（仅管理员看全部），可能导致 **列表/详情/编辑** 与 **时间线** 权限表现不一致。
2. **咨询师脱敏**：PRD 要求脱敏展示；当前客户接口 **未实际应用掩码逻辑**。
3. **前端**：菜单级限制只区分 **是否 admin/super_admin**；销售与咨询师共用同一套业务页，细粒度以 **接口返回 403** 为准。

---

## 五、参考

- 产品说明：`docs/crm_v1_prd_latest.md`
- 交互式 API 文档：启动后端后访问 `http://localhost:8000/docs`

*文档生成依据仓库当前代码结构整理，若代码变更请同步更新本文档。*
