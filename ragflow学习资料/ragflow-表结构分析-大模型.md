以下是ragflow的数据库文档，来自于大模型解析，对正确性不做任何保证。需要您自己结合实际情况判断理解，如有错误，感谢修正之后再分享。

------

## 第一章：表清单

| 序号 | 表名                  | 表说明                                                       | 主键                                 | 外键                                                         |
| ---- | --------------------- | ------------------------------------------------------------ | ------------------------------------ | ------------------------------------------------------------ |
| 1    | `api_4_conversation`  | 记录通过 API v4 接口产生的对话交互；按轮次、token、耗时等细节存储。 | `id`                                 | `dialog_id` → `dialog.id``user_id` → `user.id`               |
| 2    | `api_token`           | 管理租户的 API 访问令牌，可绑定到特定对话。                  | `(tenant_id, token)`                 | `tenant_id` → `tenant.id``dialog_id` → `dialog.id`（可选）   |
| 3    | `canvas_template`     | 内置的 Agent 可视化流程编辑器（无代码工作流）模板，存 DSL 脚本布局。 | `id`                                 | —                                                            |
| 4    | `conversation`        | 前端 UI 发起的对话记录。                                     | `id`                                 | `dialog_id` → `dialog.id``user_id` → `user.id`               |
| 5    | `dialog`              | 定义一个对话（Agent）配置：LLM、提示词、检索策略等。         | `id`                                 | `tenant_id` → `tenant.id`                                    |
| 6    | `document`            | 已解析文档元数据（分块、进度、统计等）。                     | `id`                                 | `kb_id` → `knowledgebase.id``created_by` → `user.id`         |
| 7    | `file`                | 知识库文件／文件夹结构。                                     | `id`                                 | `parent_id` → `file.id`（目录树）`tenant_id` → `tenant.id``created_by` → `user.id` |
| 8    | `file2document`       | 文件与文档的多对多关联。                                     | `id`                                 | `file_id` → `file.id``document_id` → `document.id`           |
| 9    | `invitation_code`     | 邀请码及其使用状态。                                         | `id`                                 | `user_id` → `user.id``tenant_id` → `tenant.id`               |
| 10   | `knowledgebase`       | 租户的知识库元数据：语言、嵌入模型、文档统计等。             | `id`                                 | `tenant_id` → `tenant.id``created_by` → `user.id`            |
| 11   | `llm`                 | 平台注册的 LLM 模型：名称、提供方、容量、标签。              | `(fid, llm_name)`                    | —                                                            |
| 12   | `llm_factories`       | LLM 提供方注册表（如 OpenAI、LocalAI）。                     | `name`                               | —                                                            |
| 13   | `task`                | 文档解析／索引任务：页码范围、优先级、进度、日志等。         | `id`                                 | `doc_id` → `document.id`                                     |
| 14   | `tenant`              | 租户配置：多租户名称、密钥、LLM/嵌入/ASR/TTS 等服务 ID。     | `id`                                 | —                                                            |
| 15   | `tenant_langfuse`     | Langfuse 集成：秘钥、Host 等。                               | `tenant_id`                          | `tenant_id` → `tenant.id`                                    |
| 16   | `tenant_llm`          | 租户的 LLM API Key、使用量、配置信息。                       | `(tenant_id, llm_factory, llm_name)` | `tenant_id` → `tenant.id``llm_factory` → `llm_factories.name``llm_name` → `llm.llm_name` |
| 17   | `user`                | 用户账户：昵称、邮箱、密码哈希、首选项、权限标志等。         | `id`                                 | —                                                            |
| 18   | `user_canvas`         | 用户创建的工作流画布（基于 `canvas_template` 或自定义）。    | `id`                                 | `user_id` → `user.id`                                        |
| 19   | `user_canvas_version` | 用户画布的版本历史，用于回滚与版本管理。                     | `id`                                 | `user_canvas_id` → `user_canvas.id`                          |
| 20   | `user_tenant`         | 用户在某租户下的角色关联（owner/admin/normal/invite）。      | `id`                                 | `user_id` → `user.id``tenant_id` → `tenant.id``invited_by` → `user.id` |

------

## 第二章：字段清单

### 2.0 通用审计字段（所有表均含）

| 序号 | 字段名        | 类型     | 描述                      |
| ---- | ------------- | -------- | ------------------------- |
| 1    | `create_time` | bigint   | 创建时间（Unix 毫秒）     |
| 2    | `create_date` | datetime | 创建时间（可读格式）      |
| 3    | `update_time` | bigint   | 最近更新时间（Unix 毫秒） |
| 4    | `update_date` | datetime | 最近更新时间（可读格式）  |

------

下面仅列出各表在审计字段之外的业务字段，并标注主/外键。

### 2.1 `api_4_conversation`（v4 api对话记录）

| 序号 | 字段名      | 类型         | 描述                  | PK   | FK            |
| ---- | ----------- | ------------ | --------------------- | ---- | ------------- |
| 1    | `id`        | varchar(32)  | 对话记录唯一标识      | 是   | —             |
| 2    | `dialog_id` | varchar(32)  | 所属 `dialog.id`      | 否   | → `dialog.id` |
| 3    | `user_id`   | varchar(255) | 发起者 `user.id`      | 否   | → `user.id`   |
| 4    | `message`   | longtext     | 本轮消息内容          | 否   | —             |
| 5    | `reference` | longtext     | 外部引用 JSON 数组    | 否   | —             |
| 6    | `tokens`    | int          | 消耗 token 数量       | 否   | —             |
| 7    | `source`    | varchar(16)  | 来源 (“api”/“ui”)     | 否   | —             |
| 8    | `dsl`       | longtext     | 内嵌 DSL 脚本（可选） | 否   | —             |
| 9    | `duration`  | float        | 处理耗时（秒）        | 否   | —             |
| 10   | `round`     | int          | 会话轮次              | 否   | —             |
| 11   | `thumb_up`  | int          | 赞数                  | 否   | —             |

### 2.2 `api_token`

| 序号 | 字段名      | 类型         | 描述                  | PK   | FK            |
| ---- | ----------- | ------------ | --------------------- | ---- | ------------- |
| 1    | `tenant_id` | varchar(32)  | 所属租户 `tenant.id`  | 是   | → `tenant.id` |
| 2    | `token`     | varchar(255) | API 访问令牌          | 是   | —             |
| 3    | `dialog_id` | varchar(32)  | 绑定对话（可选）      | 否   | → `dialog.id` |
| 4    | `source`    | varchar(16)  | 来源 (“cli”/“web” 等) | 否   | —             |
| 5    | `beta`      | varchar(255) | 测试标识（可选）      | 否   | —             |

### 2.3 `canvas_template`（agent流程图模板）

| 序号 | 字段名                | 类型         | 描述                                  | PK   | FK   |
| ---- | --------------------- | ------------ | ------------------------------------- | ---- | ---- |
| 1    | `id`                  | varchar(32)  | 模板唯一标识                          | 是   | —    |
| 2    | `avatar`              | text         | 模板缩略图（Base64 或 URL）           | 否   | —    |
| 3    | `title`               | varchar(255) | 模板名称                              | 否   | —    |
| 4    | `description`         | text         | 模板描述                              | 否   | —    |
| 5    | `canvas_type`         | varchar(32)  | 画布类型（如 “agent_flow”）           | 否   | —    |
| 6    | `dsl`                 | longtext     | 基于前端可视化编辑器的布局脚本（DSL） | 否   | —    |
| 7    | `create_*`/`update_*` | …            | 通用审计字段                          | —    | —    |

### 2.4 `conversation`（对话记录）

| 序号 | 字段名      | 类型         | 描述                  | PK   | FK            |
| ---- | ----------- | ------------ | --------------------- | ---- | ------------- |
| 1    | `id`        | varchar(32)  | 对话记录唯一标识      | 是   | —             |
| 2    | `dialog_id` | varchar(32)  | 所属 `dialog.id`      | 否   | → `dialog.id` |
| 3    | `name`      | varchar(255) | 会话名称（可编辑）    | 否   | —             |
| 4    | `message`   | longtext     | 本条消息内容          | 否   | —             |
| 5    | `reference` | longtext     | 引用信息（JSON 数组） | 否   | —             |
| 6    | `user_id`   | varchar(255) | 发起用户 `user.id`    | 否   | → `user.id`   |

### 2.5 `dialog`（智能助理配置/对话配置）

| 序号 | 字段名                     | 类型         | 描述                                                   | PK   | FK                        |
| ---- | -------------------------- | ------------ | ------------------------------------------------------ | ---- | ------------------------- |
| 1    | `id`                       | varchar(32)  | 对话配置唯一标识                                       | 是   | —                         |
| 2    | `tenant_id`                | varchar(32)  | 所属租户 `tenant.id`                                   | 否   | → `tenant.id`             |
| 3    | `name`                     | varchar(255) | 对话名称                                               | 否   | —                         |
| 4    | `description`              | text         | 描述                                                   | 否   | —                         |
| 5    | `icon`                     | text         | 可视化图标（Base64 或 URL）                            | 否   | —                         |
| 6    | `language`                 | varchar(32)  | 语言                                                   | 否   | —                         |
| 7    | `llm_id`                   | varchar(128) | 使用的 LLM 引用（如 “qwq-plus-latest@Tongyi-Qianwen”） | 否   | → `tenant_llm` 或 `llm`   |
| 8    | `llm_setting`              | longtext     | LLM 参数 JSON                                          | 否   | —                         |
| 9    | `prompt_type`              | varchar(16)  | 提示词类型（如 “simple”/“chain”）                      | 否   | —                         |
| 10   | `prompt_config`            | longtext     | 提示词详细配置 JSON                                    | 否   | —                         |
| 11   | `similarity_threshold`     | float        | 检索相似度阈值                                         | 否   | —                         |
| 12   | `vector_similarity_weight` | float        | 向量相似度权重                                         | 否   | —                         |
| 13   | `top_n`                    | int          | 检索返回文档数                                         | 否   | —                         |
| 14   | `top_k`                    | int          | 文档内部检索 Top-K                                     | 否   | —                         |
| 15   | `do_refer`                 | varchar(1)   | 是否引用上下文                                         | 否   | —                         |
| 16   | `rerank_id`                | varchar(128) | 重排序算法引用                                         | 否   | → `tenant_llm` / `llm`    |
| 17   | `kb_ids`                   | longtext     | 关联知识库 ID 列表                                     | 否   | → `knowledgebase.id` 列表 |
| 18   | `status`                   | varchar(1)   | 启用状态 （0/1）                                       | 否   | —                         |

### 2.6 `document`（文档）

| 序号 | 字段名             | 类型         | 描述                        | PK   | FK                   |
| ---- | ------------------ | ------------ | --------------------------- | ---- | -------------------- |
| 1    | `id`               | varchar(32)  | 文档唯一标识                | 是   | —                    |
| 2    | `thumbnail`        | text         | 缩略图（可选）              | 否   | —                    |
| 3    | `kb_id`            | varchar(256) | 所属 `knowledgebase.id`     | 否   | → `knowledgebase.id` |
| 4    | `parser_id`        | varchar(32)  | 解析器 ID                   | 否   | —                    |
| 5    | `parser_config`    | longtext     | 解析参数 JSON               | 否   | —                    |
| 6    | `source_type`      | varchar(128) | 来源类型（如 “local”/“s3”） | 否   | —                    |
| 7    | `type`             | varchar(32)  | 文档类型（如 “doc”/“pdf”）  | 否   | —                    |
| 8    | `created_by`       | varchar(32)  | 上传用户 `user.id`          | 否   | → `user.id`          |
| 9    | `name`             | varchar(255) | 原始文件名                  | 否   | —                    |
| 10   | `location`         | varchar(255) | 存储路径                    | 否   | —                    |
| 11   | `size`             | int          | 文件大小（字节）            | 否   | —                    |
| 12   | `token_num`        | int          | 分词后 token 数             | 否   | —                    |
| 13   | `chunk_num`        | int          | 分块数                      | 否   | —                    |
| 14   | `progress`         | float        | 解析进度（0–1）             | 否   | —                    |
| 15   | `progress_msg`     | text         | 进度日志                    | 否   | —                    |
| 16   | `process_begin_at` | datetime     | 解析开始时间                | 否   | —                    |
| 17   | `process_duation`  | float        | 解析耗时（秒）              | 否   | —                    |
| 18   | `meta_fields`      | longtext     | 自定义元字段 JSON           | 否   | —                    |
| 19   | `run`              | varchar(1)   | 是否自动运行                | 否   | —                    |
| 20   | `status`           | varchar(1)   | 完成状态（0/1）             | 否   | —                    |

### 2.7 `file`（原始文件）

| 序号 | 字段名        | 类型         | 描述                       | PK   | FK            |
| ---- | ------------- | ------------ | -------------------------- | ---- | ------------- |
| 1    | `id`          | varchar(32)  | 文件或文件夹唯一标识       | 是   | —             |
| 2    | `parent_id`   | varchar(32)  | 上级文件夹 `file.id`       | 否   | → `file.id`   |
| 3    | `tenant_id`   | varchar(32)  | 所属租户 `tenant.id`       | 否   | → `tenant.id` |
| 4    | `created_by`  | varchar(32)  | 上传用户 `user.id`         | 否   | → `user.id`   |
| 5    | `name`        | varchar(255) | 文件/目录名称              | 否   | —             |
| 6    | `location`    | varchar(255) | 存储路径                   | 否   | —             |
| 7    | `size`        | int          | 文件大小（字节）；目录为 0 | 否   | —             |
| 8    | `type`        | varchar(32)  | 类型 (“doc”/“folder”)      | 否   | —             |
| 9    | `source_type` | varchar(128) | 来源 (“knowledgebase”/…)   | 否   | —             |

### 2.8 `file2document`（原始文件与文档对应关系）

| 序号 | 字段名        | 类型        | 描述               | PK   | FK              |
| ---- | ------------- | ----------- | ------------------ | ---- | --------------- |
| 1    | `id`          | varchar(32) | 关联记录唯一标识   | 是   | —               |
| 2    | `file_id`     | varchar(32) | 文件 `file.id`     | 否   | → `file.id`     |
| 3    | `document_id` | varchar(32) | 文档 `document.id` | 否   | → `document.id` |

### 2.9 `invitation_code`（邀请团队成员）

| 序号 | 字段名       | 类型        | 描述                     | PK   | FK            |
| ---- | ------------ | ----------- | ------------------------ | ---- | ------------- |
| 1    | `id`         | varchar(32) | 邀请码条目唯一标识       | 是   | —             |
| 2    | `code`       | varchar(32) | 邀请码                   | 否   | —             |
| 3    | `visit_time` | datetime    | 最后使用时间             | 否   | —             |
| 4    | `user_id`    | varchar(32) | 使用者 `user.id`（可空） | 否   | → `user.id`   |
| 5    | `tenant_id`  | varchar(32) | 目标租户 `tenant.id`     | 否   | → `tenant.id` |
| 6    | `status`     | varchar(1)  | 状态（0/1）              | 否   | —             |

### 2.10 `knowledgebase`（知识库）

| 序号 | 字段名                     | 类型         | 描述                     | PK   | FK                     |
| ---- | -------------------------- | ------------ | ------------------------ | ---- | ---------------------- |
| 1    | `id`                       | varchar(32)  | 知识库唯一标识           | 是   | —                      |
| 2    | `avatar`                   | text         | 知识库图标（Base64/URL） | 否   | —                      |
| 3    | `tenant_id`                | varchar(32)  | 所属租户 `tenant.id`     | 否   | → `tenant.id`          |
| 4    | `name`                     | varchar(128) | 知识库名称               | 否   | —                      |
| 5    | `language`                 | varchar(32)  | 语言                     | 否   | —                      |
| 6    | `description`              | text         | 描述                     | 否   | —                      |
| 7    | `embd_id`                  | varchar(128) | 嵌入模型引用             | 否   | → `tenant_llm` / `llm` |
| 8    | `permission`               | varchar(16)  | 权限（public/private）   | 否   | —                      |
| 9    | `created_by`               | varchar(32)  | 创建者 `user.id`         | 否   | → `user.id`            |
| 10   | `doc_num`                  | int          | 文档总数                 | 否   | —                      |
| 11   | `token_num`                | int          | 总 token 数              | 否   | —                      |
| 12   | `chunk_num`                | int          | 总分块数                 | 否   | —                      |
| 13   | `similarity_threshold`     | float        | 检索阈值                 | 否   | —                      |
| 14   | `vector_similarity_weight` | float        | 向量相似度权重           | 否   | —                      |
| 15   | `parser_id`                | varchar(32)  | 默认解析器               | 否   | —                      |
| 16   | `parser_config`            | longtext     | 解析配置 JSON            | 否   | —                      |
| 17   | `pagerank`                 | int          | 内部排序权重             | 否   | —                      |
| 18   | `status`                   | varchar(1)   | 启用状态                 | 否   | —                      |

### 2.11 `llm`(大模型)

| 序号 | 字段名       | 类型         | 描述                     | PK        | FK   |
| ---- | ------------ | ------------ | ------------------------ | --------- | ---- |
| 1    | `fid`        | varchar(128) | 平台提供方 ID            | 是 (复合) | —    |
| 2    | `llm_name`   | varchar(128) | 模型名称                 | 是 (复合) | —    |
| 3    | `model_type` | varchar(128) | 类别 (“chat”/“embed” 等) | 否        | —    |
| 4    | `max_tokens` | int          | 最大 token 支持          | 否        | —    |
| 5    | `tags`       | varchar(255) | 标签（逗号分隔）         | 否        | —    |
| 6    | `is_tools`   | tinyint(1)   | 是否支持工具调用         | 否        | —    |
| 7    | `status`     | varchar(1)   | 启用状态                 | 否        | —    |

### 2.12 `llm_factories`(大模型供应商)

| 序号 | 字段名   | 类型         | 描述                    | PK   | FK   |
| ---- | -------- | ------------ | ----------------------- | ---- | ---- |
| 1    | `name`   | varchar(128) | 提供方名称              | 是   | —    |
| 2    | `logo`   | text         | Logo（可选 Base64/URL） | 否   | —    |
| 3    | `tags`   | varchar(255) | 支持能力标签            | 否   | —    |
| 4    | `status` | varchar(1)   | 启用状态                | 否   | —    |

### 2.13 `task`(文档解析任务)

| 序号 | 字段名            | 类型        | 描述                                        | PK   | FK              |
| ---- | ----------------- | ----------- | ------------------------------------------- | ---- | --------------- |
| 1    | `id`              | varchar(32) | 任务唯一标识                                | 是   | —               |
| 2    | `doc_id`          | varchar(32) | 所属文档 `document.id`                      | 否   | → `document.id` |
| 3    | `from_page`       | int         | 起始页                                      | 否   | —               |
| 4    | `to_page`         | int         | 结束页                                      | 否   | —               |
| 5    | `task_type`       | varchar(32) | 任务类型（“parse”/“keyword”/“question” 等） | 否   | —               |
| 6    | `priority`        | int         | 优先级                                      | 否   | —               |
| 7    | `begin_at`        | datetime    | 开始时间                                    | 否   | —               |
| 8    | `process_duation` | float       | 处理耗时（秒）                              | 否   | —               |
| 9    | `progress`        | float       | 进度（0–1）                                 | 否   | —               |
| 10   | `progress_msg`    | text        | 日志                                        | 否   | —               |
| 11   | `retry_count`     | int         | 重试次数                                    | 否   | —               |
| 12   | `digest`          | text        | 摘要或摘要 ID 列表                          | 否   | —               |
| 13   | `chunk_ids`       | longtext    | 本任务生成的分块 ID 列表                    | 否   | —               |

### 2.14 `tenant`(租户)

| 序号 | 字段名       | 类型         | 描述                 | PK   | FK                     |
| ---- | ------------ | ------------ | -------------------- | ---- | ---------------------- |
| 1    | `id`         | varchar(32)  | 租户唯一标识         | 是   | —                      |
| 2    | `name`       | varchar(100) | 租户名称             | 否   | —                      |
| 3    | `public_key` | varchar(255) | 公钥（可选）         | 否   | —                      |
| 4    | `llm_id`     | varchar(128) | 默认 LLM 引用        | 否   | → `tenant_llm` / `llm` |
| 5    | `embd_id`    | varchar(128) | 默认嵌入模型         | 否   | → `tenant_llm` / `llm` |
| 6    | `asr_id`     | varchar(128) | 默认语音转文本       | 否   | —                      |
| 7    | `img2txt_id` | varchar(128) | 默认图像转文本       | 否   | —                      |
| 8    | `rerank_id`  | varchar(128) | 默认重排序           | 否   | —                      |
| 9    | `tts_id`     | varchar(256) | 默认 TTS             | 否   | —                      |
| 10   | `parser_ids` | varchar(256) | 允许的解析器 ID 列表 | 否   | —                      |
| 11   | `credit`     | int          | 租户初始额度         | 否   | —                      |
| 12   | `status`     | varchar(1)   | 启用状态             | 否   | —                      |



### 2.15 `user_tenant`(用户与租户关联)

| 序号 | 字段名       | 类型        | 描述                                               | PK   | FK            |
| ---- | ------------ | ----------- | -------------------------------------------------- | ---- | ------------- |
| 1    | `id`         | varchar(32) | 关联关系唯一标识                                   | 是   | —             |
| 2    | `user_id`    | varchar(32) | 用户 ID，参照 `user.id`                            | 否   | → `user.id`   |
| 3    | `tenant_id`  | varchar(32) | 租户 ID，参照 `tenant.id`                          | 否   | → `tenant.id` |
| 4    | `role`       | varchar(32) | 用户在租户中的角色（如 owner/admin/normal/invite） | 否   | —             |
| 5    | `invited_by` | varchar(32) | 邀请人用户 ID，参照 `user.id`                      | 否   | → `user.id`   |
| 6    | `status`     | varchar(1)  | 状态标志（0=禁用，1=启用）                         | 否   | —             |

这样即可完整覆盖 `user_tenant` 的全部字段。



### 2.16 `tenant_langfuse`(租户凭证)

| 序号 | 字段名       | 类型          | 描述              | PK   | FK            |
| ---- | ------------ | ------------- | ----------------- | ---- | ------------- |
| 1    | `tenant_id`  | varchar(32)   | 租户 ID（唯一）   | 是   | → `tenant.id` |
| 2    | `secret_key` | varchar(2048) | Langfuse 私钥     | 否   | —             |
| 3    | `public_key` | varchar(2048) | Langfuse 公钥     | 否   | —             |
| 4    | `host`       | varchar(128)  | Langfuse 服务地址 | 否   | —             |

### 2.17 `tenant_llm`(租户与llm关联)

| 序号 | 字段名        | 类型          | 描述            | PK        | FK                     |
| ---- | ------------- | ------------- | --------------- | --------- | ---------------------- |
| 1    | `tenant_id`   | varchar(32)   | 租户 ID         | 是 (复合) | → `tenant.id`          |
| 2    | `llm_factory` | varchar(128)  | 提供方名称      | 是 (复合) | → `llm_factories.name` |
| 3    | `model_type`  | varchar(128)  | 模型类型        | 是 (复合) | —                      |
| 4    | `llm_name`    | varchar(128)  | 模型名称        | 是 (复合) | → `llm.llm_name`       |
| 5    | `api_key`     | varchar(2048) | API 密钥        | 否        | —                      |
| 6    | `api_base`    | varchar(255)  | API 基址        | 否        | —                      |
| 7    | `max_tokens`  | int           | 最大 token 限制 | 否        | —                      |
| 8    | `used_tokens` | int           | 已用 token 数   | 否        | —                      |

### 2.18 `user`(用户)

| 序号 | 字段名             | 类型         | 描述               | PK   | FK   |
| ---- | ------------------ | ------------ | ------------------ | ---- | ---- |
| 1    | `id`               | varchar(32)  | 用户唯一标识       | 是   | —    |
| 2    | `access_token`     | varchar(255) | 会话令牌（可选）   | 否   | —    |
| 3    | `nickname`         | varchar(100) | 昵称               | 否   | —    |
| 4    | `password`         | varchar(255) | 密码哈希           | 否   | —    |
| 5    | `email`            | varchar(255) | 邮箱               | 否   | —    |
| 6    | `avatar`           | text         | 头像（Base64/URL） | 否   | —    |
| 7    | `language`         | varchar(32)  | 首选语言           | 否   | —    |
| 8    | `color_schema`     | varchar(32)  | 主题配色           | 否   | —    |
| 9    | `timezone`         | varchar(64)  | 时区               | 否   | —    |
| 10   | `last_login_time`  | datetime     | 最后登录时间       | 否   | —    |
| 11   | `is_authenticated` | varchar(1)   | 是否已认证         | 否   | —    |
| 12   | `is_active`        | varchar(1)   | 是否激活           | 否   | —    |
| 13   | `is_anonymous`     | varchar(1)   | 是否匿名           | 否   | —    |
| 14   | `login_channel`    | varchar(255) | 登录渠道           | 否   | —    |
| 15   | `status`           | varchar(1)   | 启用状态           | 否   | —    |
| 16   | `is_superuser`     | tinyint(1)   | 超级用户标志       | 否   | —    |

### 2.19 `user_canvas`(用户-画布流程)

| 序号 | 字段名        | 类型         | 描述                          | PK   | FK          |
| ---- | ------------- | ------------ | ----------------------------- | ---- | ----------- |
| 1    | `id`          | varchar(32)  | 画布唯一标识                  | 是   | —           |
| 2    | `avatar`      | text         | 缩略图                        | 否   | —           |
| 3    | `user_id`     | varchar(255) | 所属用户 `user.id`            | 否   | → `user.id` |
| 4    | `title`       | varchar(255) | 画布标题                      | 否   | —           |
| 5    | `permission`  | varchar(16)  | 权限（如 “private”/“public”） | 否   | —           |
| 6    | `description` | text         | 描述                          | 否   | —           |
| 7    | `canvas_type` | varchar(32)  | 画布类型（同模版）            | 否   | —           |
| 8    | `dsl`         | longtext     | 用户自定义布局脚本            | 否   | —           |

### 2.20 `user_canvas_version`(用户-画布流程版本)

| 序号 | 字段名           | 类型         | 描述                  | PK   | FK                 |
| ---- | ---------------- | ------------ | --------------------- | ---- | ------------------ |
| 1    | `id`             | varchar(32)  | 版本唯一标识          | 是   | —                  |
| 2    | `user_canvas_id` | varchar(255) | 所属 `user_canvas.id` | 否   | → `user_canvas.id` |
| 3    | `title`          | varchar(255) | 版本标题（可选）      | 否   | —                  |
| 4    | `description`    | text         | 版本描述              | 否   | —                  |
| 5    | `dsl`            | longtext     | 该版本的布局脚本      | 否   | —                  |

------

## 第三章：概念实体与关系分析

```text
Tenant ──< user_tenant 用户-租户关联>── User
   │
   ├─< dialog -对话配置>──< conversation d对话记录> / < api_4_conversation 接口v4的对话记录>
   │
   ├─< knowledgebase 知识库>──< document 文档>──< task 文件解析任务>
   │                       └─< file2document 原始文件与文档对应关系>──< file 原始文件>
   │
   ├─< api_token >
   │
   └─< tenant_llm >── LLM_factories / LLM
```

1. **多租户隔离**：所有业务数据（对话、知识库、文件、LLM 调用）均与 `tenant_id` 关联。
2. **用户角色**：`user_tenant` 定义用户在租户中的角色，用于权限控制。
3. **知识库编排**：`knowledgebase` → `document` → `task` → 外部向量引擎。
4. **可视化 Agent**：基于 `canvas_template`（内置）与 `user_canvas`（自定义），在前端拖拽生成 DSL 流程。
5. **对话服务**：UI 层 `conversation` 与 API 层 `api_4_conversation` 并行记录，`dialog` 配置服务端交互策略。

------

## 第五章：主要业务场景与数据变动

1. **用户注册／租户创建**
   - **操作**：插入 `user`、`tenant`；
   - **权限**：自动在 `user_tenant` 创建 owner 关联；
   - **可选**：如果使用邀请码，写入 `invitation_code`。
2. **Agent（对话）初始化**
   - **操作**：在 `dialog` 插入配置；
   - **授权**：为租户分配 LLM（`tenant_llm`）及检索模型；
   - **后续**：前端可基于 `canvas_template` 快速创建流程。
3. **知识库与文件**
   - **上传**：`file`（目录／文件）；
   - **关联**：`file2document` 至 `document`；
   - **解析任务**：向 `task` 中写入解析／关键词／问题生成任务。
4. **文档解析**
   - **执行器**：轮询 `task.status=0`；
   - **更新**：写入 `document.progress`、`document.status`；
   - **完成**：分块存入向量引擎。
5. **对话交互**
   - **用户发起**：UI 写入 `conversation`；API 写入 `api_4_conversation`；
   - **LLM 调用**：根据 `dialog` 配置，选用 `tenant_llm` 及策略；
   - **统计**：累计 token、耗时，支持多轮和打分（`thumb_up`）。
6. **画布管理**
   - **模板**：`canvas_template` 存储官方预置流程；
   - **自定义**：`user_canvas`／`user_canvas_version` 管理用户版及历史回滚；
   - **渲染**：前端拖拽 DSL → 执行时转为实际 API 调用。

------

以上即 RAGFlow 后端数据库的全量设计文档，涵盖表说明、字段清单、实体关系与主要业务场景。若需更深入的字段注释或补充其他场景，请继续沟通！