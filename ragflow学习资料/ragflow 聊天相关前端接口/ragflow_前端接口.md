# RAGFlow 聊天 API 文档

> **说明**：本接口文档依据浏览器 F12 抓取的实际请求数据（以此为准），并参考官方 API 文档及社区博客校对字段。此文档记录的是RAGFlow前端内部接口，与官方公开API接口有所区别。

**基础 URL：** `http://127.0.0.1` 

**注意：** 所有请求均需在请求头中携带：

```http
Authorization: Bearer <access_token>
```

---

## 1. 获取应用信息

- **接口路径**：`/v1/getAppInfo`
- **请求方法**：GET
- **功能描述**：获取应用的基本信息，如应用名称。
- **调用场景**：客户端启动时加载应用元数据。

### 请求示例

无需额外参数，仅需带 Authorization

### 响应示例

```json
{
  "code": 0,
  "data": {
    "appName": "KnowledgeBase"
  },
  "message": "success"
}
```

| 字段           | 类型      | 说明         |
| ------------ | ------- | ---------- |
| code         | integer | 返回码，0 表示成功 |
| data.appName | string  | 应用名称       |
| message      | string  | 响应消息       |

---

## 2. 获取用户信息

- **接口路径**：`/v1/user/info`
- **请求方法**：GET
- **功能描述**：获取当前登录用户的认证信息与个人资料。
- **调用场景**：页面加载或设置页面展示用户信息。

### 请求示例

无需额外参数，仅需带 Authorization

### 响应示例

```json
{
  "code": 0,
  "data": {
    "access_token": "b6cbe756559311f0bb99000c29d1a431",
    "avatar": null,
    "color_schema": "Bright",
    "create_date": "Fri, 13 Jun 2025 13:18:46 GMT",
    "create_time": 1749791926098,
    "email": "test@abc.com",
    "id": "de9f5c834e69421083ceb2cb9641d241",
    "is_active": "1",
    "is_anonymous": "0",
    "is_authenticated": "1",
    "is_superuser": true,
    "language": "Chinese",
    "last_login_time": "Fri, 13 Jun 2025 13:18:44 GMT",
    "login_channel": "password",
    "nickname": "abc456",
    "role": "normal",
    "status": "1",
    "timezone": "UTC+8 Asia/Shanghai",
    "update_date": "Mon, 30 Jun 2025 17:22:16 GMT",
    "update_time": 1751275336385
  },
  "message": "success"
}
```

| 字段                     | 类型            | 说明                   |
| ---------------------- | ------------- | -------------------- |
| data.access\_token     | string        | 登录令牌                 |
| data.avatar            | string / null | 用户头像 URL 或 Base64 编码 |
| data.color\_schema     | string        | 主题配色                 |
| data.create\_date      | string        | 账户创建日期 (GMT)         |
| data.create\_time      | integer       | 账户创建时间戳（毫秒 Unix）     |
| data.email             | string        | 用户邮箱                 |
| data.id                | string        | 用户唯一标识               |
| data.is\_active        | string        | 用户是否激活（"1" / "0"）    |
| data.is\_anonymous     | string        | 是否匿名用户（"1" / "0"）    |
| data.is\_authenticated | string        | 是否已验证（"1" / "0"）     |
| data.is\_superuser     | boolean       | 是否超级用户               |
| data.language          | string        | 语言偏好                 |
| data.last\_login\_time | string        | 上次登录时间 (GMT)         |
| data.login\_channel    | string        | 登录方式（如 "password"）   |
| data.nickname          | string        | 用户昵称                 |
| data.role              | string        | 用户角色（如 "normal"）     |
| data.status            | string        | 用户状态（"1" / "0"）      |
| data.timezone          | string        | 时区设置                 |
| data.update\_date      | string        | 最后更新日期 (GMT)         |
| data.update\_time      | integer       | 最后更新时间戳（毫秒 Unix）     |
| message                | string        | 响应消息                 |

---

## 3. 获取租户信息

- **接口路径**：`/v1/user/tenant_info`
- **请求方法**：GET
- **功能描述**：获取当前租户的配置，如模型、解析器、重排器等。
- **调用场景**：初始化租户绑定的资源和功能。

### 请求示例

无需额外参数，仅需带 Authorization

### 响应示例

```json
{
  "code": 0,
  "data": {
    "asr_id": "",
    "embd_id": "text-embedding-v4@Tongyi-Qianwen",
    "img2txt_id": "qwen-vl-plus@Tongyi-Qianwen",
    "llm_id": "qwen-plus@Tongyi-Qianwen",
    "name": "xiyuan27's Kingdom",
    "parser_ids": "naive:General,qa:Q&A,resume:Resume,manual:Manual,table:Table,paper:Paper,book:Book,laws:Laws,presentation:Presentation,picture:Picture,one:One,audio:Audio,email:Email,tag:Tag",
    "rerank_id": "gte-rerank@Tongyi-Qianwen",
    "role": "normal",
    "tenant_id": "e08c2142481511f0b121010101010000",
    "tts_id": null
  },
  "message": "success"
}
```

| 字段               | 类型            | 说明              |
| ---------------- | ------------- | --------------- |
| data.asr\_id     | string        | 语音识别模型 ID，可能为空  |
| data.embd\_id    | string        | Embedding 模型 ID |
| data.img2txt\_id | string        | 图像转文本模型 ID      |
| data.llm\_id     | string        | 默认大模型 ID        |
| data.name        | string        | 租户名称            |
| data.parser\_ids | string        | 支持的解析器列表（逗号分隔）  |
| data.rerank\_id  | string        | 重排模型 ID         |
| data.role        | string        | 用户在该租户中的角色      |
| data.tenant\_id  | string        | 租户唯一标识          |
| data.tts\_id     | string / null | 文本转语音模型 ID，可能为空 |
| message          | string        | 响应消息            |

---

## 4. 列出对话模板

- **接口路径**：`/v1/dialog/list`
- **请求方法**：GET
- **功能描述**：获取当前租户下所有智能助理（对话模板）的列表。
- **调用场景**：左侧面板展示可选助理。

### 请求示例

无需额外参数，仅需带 Authorization

### 响应示例

```json
{
  "code": 0,
  "data": [
    {
      "id": "0d3bb0a6522b11f09ad3000c29d1a431",
      "create_date": "Thu, 26 Jun 2025 09:15:30 GMT",
      "create_time": 1750900530757,
      "description": "A helpful dialog",
      "do_refer": "1",
      "icon": "",
      "kb_ids": ["37e5c164522811f0a6b8000c29d1a431"],
      "kb_names": ["国内机票"],
      "language": "English",
      "llm_id": "qwen-plus@Tongyi-Qianwen",
      "llm_setting": {},
      "name": "国内机票政策助理",
      "prompt_config": {
           "empty_response": "",
           "keyword": true,
           "parameters": [{"key":"knowledge","optional":false}],
           "prologue": "你好！我是你的助理，有什么可以帮到你的吗？",
           "quote": true,
           "reasoning": false,
           "refine_multiturn": false,
           "system": "你是一个国内机票助理。",
           "tts": false,
           "use_kg": false
      },
      "prompt_type": "simple",
      "rerank_id": "",
      "similarity_threshold": 0.2,
      "status": "1",
      "tenant_id": "e08c2142481511f0b121010101010000",
      "top_k": 1024,
      "top_n": 8,
      "update_date": "Thu, 26 Jun 2025 09:15:30 GMT",
      "update_time": 1750900530757,
      "vector_similarity_weight": 0.3
    }
  ],
  "message": "success"
}
```

| 字段                                | 类型      | 说明               |
| --------------------------------- | ------- | ---------------- |
| data[].id                         | string  | 对话模板 ID          |
| data[].create\_date               | string  | 创建日期 (GMT)       |
| data[].create\_time               | integer | 创建时间戳（毫秒 Unix）   |
| data[].description                | string  | 描述               |
| data[].do\_refer                  | string  | 是否引用知识库（"1"/"0"） |
| data[].icon                       | string  | 图标 URL 或 Base64  |
| data[].kb\_ids                    | array   | 关联知识库 ID 列表      |
| data[].kb\_names                  | array   | 关联知识库名称列表        |
| data[].language                   | string  | 语言设置             |
| data[].llm\_id                    | string  | 使用的大模型 ID        |
| data[].llm\_setting               | object  | LLM 运行时参数        |
| data[].name                       | string  | 助理名称             |
| data[].prompt\_config             | object  | 完整提示配置           |
| data[].prompt\_type               | string  | 提示类型（如 "simple"） |
| data[].rerank\_id                 | string  | 重排模型 ID          |
| data[].similarity\_threshold      | number  | 相似度阈值            |
| data[].status                     | string  | 状态（"1"/"0"）      |
| data[].tenant\_id                 | string  | 租户 ID            |
| data[].top\_k                     | integer | 最大检索条数           |
| data[].top\_n                     | integer | 重排前检索条数          |
| data[].update\_date               | string  | 最后更新日期 (GMT)     |
| data[].update\_time               | integer | 最后更新时间戳（毫秒 Unix） |
| data[].vector\_similarity\_weight | number  | 向量相似度权重          |
| message                           | string  | 响应消息             |

---

## 5. 列出租户列表

- **接口路径**：`/v1/tenant/list`
- **请求方法**：GET
- **功能描述**：获取当前用户可访问的所有租户信息列表。
- **调用场景**：在多租户环境下切换租户时使用。

### 请求示例

无需额外参数，仅需带 Authorization

### 响应示例

```json
{
  "code": 0,
  "data": [
    {
      "avatar": "data:image/png;base64,...",
      "delta_seconds": 3566.120275,
      "email": "xiyuan27@abc.com",
      "nickname": "xiyuan27",
      "role": "normal",
      "tenant_id": "e08c2142481511f0b121010101010000",
      "update_date": "Mon, 30 Jun 2025 17:07:57 GMT"
    }
  ],
  "message": "success"
}
```

| 字段                    | 类型     | 说明                  |
| --------------------- | ------ | ------------------- |
| data[].avatar         | string | 租户头像 Base64 编码或 URL |
| data[].delta\_seconds | number | 与服务器时差（秒）           |
| data[].email          | string | 租户所属用户邮箱            |
| data[].nickname       | string | 租户昵称                |
| data[].role           | string | 用户在租户中的角色           |
| data[].tenant\_id     | string | 租户唯一标识              |
| data[].update\_date   | string | 最后更新时间 (GMT)        |
| message               | string | 响应消息                |

---

## 6. 获取对话模板详情

- **接口路径**：`/v1/dialog/get`
- **请求方法**：GET
- **功能描述**：获取指定对话模板的详细配置，包括 prompt\_config。

### 请求参数

| 参数         | 位置    | 类型     | 必填 | 说明      |
| ---------- | ----- | ------ | -- | ------- |
| dialog\_id | query | string | 是  | 对话模板 ID |

### 响应示例

```json
{
  "code": 0,
  "data": {
    "id": "0d3bb0a6522b11f09ad3000c29d1a431",
    "create_date": "Thu, 26 Jun 2025 09:15:30 GMT",
    "create_time": 1750900530757,
    "description": "A helpful dialog",
    "do_refer": "1",
    "icon": "",
    "kb_ids": ["37e5c164522811f0a6b8000c29d1a431"],
    "kb_names": ["国内机票"],
    "language": "English",
    "llm_id": "qwen-plus@Tongyi-Qianwen",
    "llm_setting": {},
    "name": "国内机票政策助理",
    "prompt_config": {
      "empty_response": "",
      "keyword": true,
      "parameters": [{"key":"knowledge","optional":false}],
      "prologue": "你好！我是你的助理，有什么可以帮到你的吗？",
      "quote": true,
      "reasoning": false,
      "refine_multiturn": false,
      "system": "你是一个国内机票助理。",
      "tts": false,
      "use_kg": false
    },
    "prompt_type": "simple",
    "rerank_id": "",
    "similarity_threshold": 0.2,
    "status": "1",
    "tenant_id": "e08c2142481511f0b121010101010000",
    "top_k": 1024,
    "top_n": 8,
    "update_date": "Thu, 26 Jun 2025 09:15:30 GMT",
    "update_time": 1750900530757,
    "vector_similarity_weight": 0.3
  },
  "message": "success"
}
```

| 字段                                    | 类型      | 说明               |
| ------------------------------------- | ------- | ---------------- |
| data.id                               | string  | 对话模板 ID          |
| data.create\_date                     | string  | 创建日期 (GMT)       |
| data.create\_time                     | integer | 创建时间戳（毫秒 Unix）   |
| data.description                      | string  | 描述               |
| data.do\_refer                        | string  | 是否引用知识库（"1"/"0"） |
| data.icon                             | string  | 图标 URL 或 Base64  |
| data.kb\_ids                          | array   | 关联知识库 ID 列表      |
| data.kb\_names                        | array   | 关联知识库名称列表        |
| data.language                         | string  | 语言设置             |
| data.llm\_id                          | string  | 使用的大模型 ID        |
| data.llm\_setting                     | object  | LLM 运行时参数        |
| data.name                             | string  | 助理名称             |
| data.prompt\_config.empty\_response   | string  | 空响应文字            |
| data.prompt\_config.keyword           | boolean | 是否使用关键词触发        |
| data.prompt\_config.parameters        | array   | 参数列表             |
| data.prompt\_config.prologue          | string  | 前言文本             |
| data.prompt\_config.quote             | boolean | 是否引用上下文          |
| data.prompt\_config.reasoning         | boolean | 是否开启推理           |
| data.prompt\_config.refine\_multiturn | boolean | 是否多轮优化           |
| data.prompt\_config.system            | string  | 系统提示             |
| data.prompt\_config.tts               | boolean | 是否开启文本转语音        |
| data.prompt\_config.use\_kg           | boolean | 是否使用知识图谱         |
| data.prompt\_type                     | string  | 提示类型             |
| data.rerank\_id                       | string  | 重排模型 ID          |
| data.similarity\_threshold            | number  | 相似度阈值            |
| data.status                           | string  | 状态（"1"/"0"）      |
| data.tenant\_id                       | string  | 租户 ID            |
| data.top\_k                           | integer | 最大检索条数           |
| data.top\_n                           | integer | 重排前检索条数          |
| data.update\_date                     | string  | 更新日期 (GMT)       |
| data.update\_time                     | integer | 更新时间戳（毫秒 Unix）   |
| data.vector\_similarity\_weight       | number  | 向量相似度权重          |
| message                               | string  | 响应消息             |

---

## 7. 列出会话列表

- **接口路径**：`/v1/conversation/list`
- **请求方法**：GET
- **功能描述**：获取某个对话模板下的所有会话线程。

### 请求参数

| 参数         | 位置    | 类型     | 必填 | 说明      |
| ---------- | ----- | ------ | -- | ------- |
| dialog\_id | query | string | 是  | 对话模板 ID |

### 响应示例

```json
{
  "code": 0,
  "data": [
    {
      "create_date": "Mon, 30 Jun 2025 22:47:24 GMT",
      "create_time": 1751294844221,
      "dialog_id": "0d3bb0a6522b11f09ad3000c29d1a431",
      "id": "d0ec8a67af064b2d8a396cf33bce2377",
      "message": [
        {"content": "你好！我是你的助理，有什么可以帮到你的吗？","role": "assistant"},
        {"content": "阿拉伯通票如何退票","doc_ids": [],"id": "46cea227-60d8-4edc-bdf5-416acbcd52b5","role": "user"},
        {"content": "退票规则如下。","created_at": 1751294855.8851023,"id": "46cea227-60d8-4edc-bdf5-416acbcd52b5","role": "assistant"}
      ],
      "name": "48小时内退票，如何处理",
      "reference": [ /* 与 document/infos 输出相同的引用结构 */ ],
      "update_date": "Mon, 30 Jun 2025 22:52:05 GMT",
      "update_time": 1751295125884,
      "user_id": "de9f5c834e69421083ceb2cb9641d241"
    }
  ],
  "message": "success"
}
```

| 字段                        | 类型      | 说明                                               |
| ------------------------- | ------- | ------------------------------------------------ |
| data[].create\_date       | string  | 会话创建日期 (GMT)                                     |
| data[].create\_time       | integer | 创建时间戳（毫秒 Unix）                                   |
| data[].dialog\_id         | string  | 所属对话模板 ID                                        |
| data[].id                 | string  | 会话 ID                                            |
| data[].message            | array   | 消息数组                                             |
| data[].message[].content  | string  | 消息内容                                             |
| data[].message[].role     | string  | 消息角色（user/assistant）                              |
| data[].message[].id       | string  | 消息唯一标识                                           |
| data[].message[].doc_ids  | array   | 关联文档ID列表（用户消息可能为空）                                |
| data[].message[].created_at | number | Unix时间戳（秒），仅assistant消息                          |
| data[].name               | string  | 会话名称                                             |
| data[].reference          | array   | 引用的文档片段与聚合信息                                     |
| data[].update\_date       | string  | 会话最后更新时间 (GMT)                                   |
| data[].update\_time       | integer | 最后更新时间戳（毫秒 Unix）                                 |
| data[].user\_id           | string  | 发起会话的用户 ID                                       |
| message                   | string  | 响应消息                                             |

---

## 8. 会话回复流式输出

- **接口路径**：`/v1/conversation/completion`
- **请求方法**：POST (SSE)
- **功能描述**：通过 SSE 实时推送 AI 助理的逐步回复。
- **调用场景**：用户在聊天界面发送消息时，通过此接口获取AI助理的实时回复。支持流式传输，可实现打字机效果。

### 请求示例

- **Headers**：Authorization, Content-Type: application/json
- **Body**：

```json
{
  "conversation_id": "4f248dd6e67b4bbbbaf47cef01efa238",
  "messages": [
    {"role":"assistant","content":"你好！..."},
    {"id":"eec6ba99-0d1c-4177-8c74-5f5bf4fc566b","role":"user","content":"阿拉伯通票如何退票","doc_ids":[]}  
  ]
}
```

### SSE 响应格式

逐行 `data: <JSON>`，最终以 `data: {"code":0,"data":true}` 结束。

#### 响应字段 (按事件顺序)

| 字段                 | 类型            | 说明                               |
| ------------------ | ------------- | -------------------------------- |
| code               | integer       | 返回码，0 表示成功                       |
| message            | string        | 消息，一般为空                          |
| data.answer        | string        | 当前分段回答内容                         |
| data.reference     | object        | 引用片段，详细结构见下方说明                   |
| data.audio\_binary | string / null | 音频二进制 Base64 或 null              |
| data.id            | string        | 本次请求的消息 ID                       |
| data.session\_id   | string        | 会话 ID                            |
| data (最后一条)        | boolean       | true，表示结束标志                      |

#### reference 字段结构说明

`data.reference` 对象包含检索到的知识库片段信息：

| 字段           | 类型     | 说明                                    |
| ------------ | ------ | ------------------------------------- |
| chunks       | array  | 文档片段数组                                |
| doc_aggs     | array  | 文档聚合统计                                |
| total        | number | 总检索到的片段数                              |

**chunks 数组元素结构：**

| 字段                | 类型     | 说明                        |
| ----------------- | ------ | ------------------------- |
| content           | string | 文档片段内容                    |
| dataset_id        | string | 数据集ID                     |
| doc_type          | string | 文档类型                      |
| document_id       | string | 文档ID                      |
| document_name     | string | 文档名称                      |
| id                | string | 片段ID                      |
| image_id          | string | 图片ID                      |
| positions         | array  | 位置信息数组                    |
| similarity        | number | 综合相似度（0-1）                |
| term_similarity   | number | 词项相似度（0-1）                |
| url               | string | URL地址，通常为null             |
| vector_similarity | number | 向量相似度（0-1）                |

**doc_aggs 数组元素结构：**

| 字段       | 类型     | 说明        |
| -------- | ------ | --------- |
| count    | number | 该文档的片段数量  |
| doc_id   | string | 文档ID      |
| doc_name | string | 文档名称      |

---

## 9. 获取文档缩略图

- **接口路径**：`/v1/document/thumbnails`
- **请求方法**：GET
- **功能描述**：获取指定文档的缩略图 Base64 编码或空占位。

### 请求参数

| 参数       | 位置    | 类型     | 必填 | 说明            |
| -------- | ----- | ------ | -- | ------------- |
| doc\_ids | query | string | 是  | 逗号分隔的文档 ID 列表 |

### 响应示例

```json
{ "code":0, "data":{ "83a655f4522911f08abb000c29d1a431":"" }, "message":"success" }
```

| 字段              | 类型      | 说明              |
| --------------- | ------- | --------------- |
| data.\<doc\_id> | string  | 对应文档的缩略图 Base64 |
| code            | integer | 返回码，0 表示成功      |
| message         | string  | 响应消息            |

---

## 10. 获取会话详情

- **接口路径**：`/v1/conversation/get`
- **请求方法**：GET
- **功能描述**：获取完整会话消息及对应引用文档片段。

### 请求参数

| 参数               | 位置    | 类型     | 必填 | 说明    |
| ---------------- | ----- | ------ | -- | ----- |
| conversation\_id | query | string | 是  | 会话 ID |

### 响应示例

```json
{
  "code":0,
  "data":{
    "avatar":"",
    "create_date":"Mon, 30 Jun 2025 21:08:10 GMT",
    "create_time":1751288890799,
    "dialog_id":"0d3bb0a6522b11f09ad3000c29d1a431",
    "id":"4f248dd6e67b4bbbbaf47cef01efa238",
    "message":[ ... ],
    "name":"阿拉伯通票如何退票",
    "reference": [
                {
                    "chunks": [
                        {
                            "content": "\u4ee5\u4e0b......",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95c1b1ee522d11f097e3000c29d1a431",
                            "document_name": "20241223 SC \u4e1a\u52a1\u901a...\u4ef6(20250101).md",
                            "id": "2e88bef0daa08039",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.7602817697873265,
                            "term_similarity": 0.8406851686464784,
                            "url": null,
                            "vector_similarity": 0.5726738391159725
                        },
                        {
                            "content": "\u4ee5\u4e0b...\u636e\u3002",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95c96650522d11f097e3000c29d1a431",
                            "document_name": "20250306 Y8 \u91d1...\u901a\u544a.md",
                            "id": "4883a2b82dbde0b4",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.7335284432117006,
                            "term_similarity": 0.8406851686464784,
                            "url": null,
                            "vector_similarity": 0.4834960838638862
                        },
                        {
                            "content": "\u4ee5..u542b\uff09**\uff1a70%\uff1b\n  - ...\u3002",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95c80792522d11f097e3000c29d1a431",
                            "document_name": "20250306 Y8 \u300a\...u544a.md",
                            "id": "ad9e8e4f6ef58f52",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.7295932062720982,
                            "term_similarity": 0.8406851686464784,
                            "url": null,
                            "vector_similarity": 0.47037862739854497
                        },
                        {
                            "content": "\u4ee5\u4e0b\...\u3002",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95c96650522d11f097e3000c29d1a431",
                            "document_name": "20250306 Y8 \u91d1\...u901a\u544a.md",
                            "id": "321b1ba0a209e548",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.7206417807867256,
                            "term_similarity": 0.8406851686464784,
                            "url": null,
                            "vector_similarity": 0.44054054244730245
                        },
                        {
                            "content": "\u4ee5\u4e0b...\u9020\u3002**",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95cfad58522d11f097e3000c29d1a431",
                            "document_name": "shandong_1.md",
                            "id": "db3260a76d0ff0dc",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.709584113739441,
                            "term_similarity": 0.7723582369539453,
                            "url": null,
                            "vector_similarity": 0.5631111595722641
                        },
                        {
                            "content": "\u4ee5\u4e0b...\u3002**",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95cfad58522d11f097e3000c29d1a431",
                            "document_name": "shandong_1.md",
                            "id": "4210822e8d2b32a8",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.7069472011646597,
                            "term_similarity": 0.7723582369539453,
                            "url": null,
                            "vector_similarity": 0.55432145098966
                        },
                        {
                            "content": "\u4ee5\u4e0b...\u3002",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95ddee68522d11f097e3000c29d1a431",
                            "document_name": "\u4e2d\u8054\u822a.md",
                            "id": "868f5bec207d4f73",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.6987529787608726,
                            "term_similarity": 0.7723582369539453,
                            "url": null,
                            "vector_similarity": 0.5270073763103698
                        },
                        {
                            "content": "\u4e...u7f16\u9020\u3002**",
                            "dataset_id": "37e5c164522811f0a6b8000c29d1a431",
                            "doc_type": "",
                            "document_id": "95cfad58522d11f097e3000c29d1a431",
                            "document_name": "shandong_1.md",
                            "id": "12ac6a08204b314f",
                            "image_id": "",
                            "positions": [],
                            "similarity": 0.6938593674846437,
                            "term_similarity": 0.7723582369539453,
                            "url": null,
                            "vector_similarity": 0.51069533872294
                        }
                    ],
                    "doc_aggs": [
                        {
                            "count": 3,
                            "doc_id": "95cfad58522d11f097e3000c29d1a431",
                            "doc_name": "shandong_1.md"
                        },
                        {
                            "count": 1,
                            "doc_id": "95c80792522d11f097e3000c29d1a431",
                            "doc_name": "20250306 Y8 \u300a\u91d1\...901a\u544a.md"
                        },
                        {
                            "count": 1,
                            "doc_id": "95ddee68522d11f097e3000c29d1a431",
                            "doc_name": "\u4e2d\u8054\u822a.md"
                        }
                    ],
                    "total": 63
                }
    ],
    "update_date":"Mon, 30 Jun 2025 21:08:19 GMT",
    "update_time":1751288899484,
    "user_id":"de9f5c834e69421083ceb2cb9641d241"
  },
  "message":"success"
}
```

| 字段                | 类型      | 说明                                             |
| ----------------- | ------- | ---------------------------------------------- |
| data.avatar       | string  | 会话头像                                           |
| data.create\_date | string  | 会话创建日期 (GMT)                                   |
| data.create\_time | integer | 创建时间戳（毫秒 Unix）                                 |
| data.dialog\_id   | string  | 所属对话模板 ID                                      |
| data.id           | string  | 会话 ID                                          |
| data.message      | array   | 完整消息数组，包括 content、role、doc\_ids、created\_at、id |
| data.name         | string  | 会话标题                                           |
| data.reference    | array   | 引用的知识片段及聚合信息                                   |
| data.update\_date | string  | 最后更新时间 (GMT)                                   |
| data.update\_time | integer | 最后更新时间戳（毫秒 Unix）                               |
| data.user\_id     | string  | 会话所属用户 ID                                      |
| message           | string  | 响应消息                                           |



| 字段                    | 类型    | 说明                                                         |
| ----------------------- | ------- | ------------------------------------------------------------ |
| data.reference.chunks   | array   | 引用片段数组，包含以下字段：- content (string)- dataset_id (string)- doc_type (string)- document_id (string)- document_name (string)- id (string)- image_id (string)- positions (array)- similarity (number)- term_similarity (number)- url (string |
| data.reference.doc_aggs | array   | 文档聚合数组，包含以下字段：- count (integer)- doc_id (string)- doc_name (string) |
| data.reference.total    | integer | 引用片段总数                                                 |

**注意：** assistant 角色的消息可能包含额外字段：

| 字段      | 类型      | 说明                      |
| ------- | ------- | ----------------------- |
| thumbup | boolean | 用户点赞状态（可选字段，点赞后出现）      |

---

## 11. 重命名会话

- **接口路径**：`/v1/conversation/set`
- **请求方法**：POST
- **功能描述**：修改会话标题。

### 请求参数

| 参数               | 类型      | 必填 | 说明                          |
| ---------------- | ------- | -- | --------------------------- |
| conversation\_id | string  | 是  | 会话ID                        |
| name             | string  | 是  | 新的会话标题                      |
| is\_new          | boolean | 否  | 是否为新会话，通常为false（修改现有会话标题） |

### 请求示例

```json
{
  "conversation_id":"d0ec8a67af064b2d8a396cf33bce2377",
  "name":"新会话标题",
  "is_new":false
}
```

### 响应示例

返回与"获取会话详情"相同的完整对象。

---

## 12. 删除会话

- **接口路径**：`/v1/conversation/rm`
- **请求方法**：POST
- **功能描述**：删除一个或多个会话线程。

### 请求示例

```json
{
  "conversation_ids":["4f248dd6e67b4bbbbaf47cef01efa238"],
  "dialog_id":"0d3bb0a6522b11f09ad3000c29d1a431"
}
```

### 响应示例

```json
{ "code":0, "data":true, "message":"success" }
```

---

## 13. 删除单条消息

- **接口路径**：`/v1/conversation/delete_msg`
- **请求方法**：POST
- **功能描述**：删除指定会话中的单条消息。

### 请求示例

```json
{
  "message_id":"8b98b8b8-463b-44b4-b3c4-b7aba2be3d42",
  "conversation_id":"657107c7a044439089ac902115067d01"
}
```

### 响应示例

返回与"获取会话详情"相同的完整对象。

---

## 14. 上传并解析文档

- **接口路径**：`/v1/document/upload_and_parse`
- **请求方法**：POST (multipart/form-data)
- **功能描述**：上传文件并解析到知识库，返回新文档 ID。

### 表单字段

| 字段               | 类型     | 说明    |
| ---------------- | ------ | ----- |
| conversation\_id | string | 会话 ID |
| file             | binary | 文件二进制 |

### 响应示例

```json
{ "code":0, "data":["f945da9e561d11f08a2d000c29d1a431"], "message":"success" }
```

---

## 15. 获取文档信息

- **接口路径**：`/v1/document/infos`
- **请求方法**：POST
- **功能描述**：查询文档的元信息及解析进度。

### 请求示例

```json
{ "doc_ids":["f945da9e561d11f08a2d000c29d1a431"] }
```

### 响应示例

```json
{
  "code": 0,
  "data": [
    {
      "chunk_num": 2,
      "create_date": "Tue, 01 Jul 2025 09:51:58 GMT",
      "create_time": 1751334718463,
      "created_by": "e08c2142481511f0b121010101010000",
      "id": "f945da9e561d11f08a2d000c29d1a431",
      "kb_id": "37e5c164522811f0a6b8000c29d1a431",
      "location": "阿拉伯通票(1).md",
      "meta_fields": {},
      "name": "阿拉伯通票(1).md",
      "parser_config": { /* 完整配置参见官方文档 */ },
      "parser_id": "naive",
      "process_begin_at": null,
      "process_duation": 0.0,
      "progress": 0.0,
      "progress_msg": "",
      "run": "0",
      "size": 5933,
      "source_type": "local",
      "status": "1",
      "thumbnail": "",
      "token_num": 2730,
      "type": "doc",
      "update_date": "Tue, 01 Jul 2025 09:52:47 GMT",
      "update_time": 1751334767020
    }
  ],
  "message": "success"
}
```

| 字段                        | 类型            | 说明                 |
| ------------------------- | ------------- | ------------------ |
| data[].chunk\_num         | integer       | 分片数量               |
| data[].create\_date       | string        | 文档创建日期 (GMT)       |
| data[].create\_time       | integer       | 创建时间戳（毫秒 Unix）     |
| data[].created\_by        | string        | 创建者 ID             |
| data[].id                 | string        | 文档 ID              |
| data[].kb\_id             | string        | 所属知识库 ID           |
| data[].location           | string        | 原文件路径/名称           |
| data[].meta\_fields       | object        | 用户自定义元字段           |
| data[].name               | string        | 文档名称               |
| data[].parser\_config     | object        | 解析器配置              |
| data[].parser\_id         | string        | 解析器 ID             |
| data[].process\_begin\_at | string / null | 解析开始时间             |
| data[].process\_duation   | number        | 解析时长（秒）            |
| data[].progress           | number        | 解析进度（0-1）          |
| data[].progress\_msg      | string        | 进度消息               |
| data[].run                | string        | 运行状态               |
| data[].size               | integer       | 文档大小（字节）           |
| data[].source\_type       | string        | 来源类型（local/remote） |
| data[].status             | string        | 文档状态               |
| data[].thumbnail          | string        | 缩略图 Base64         |
| data[].token\_num         | integer       | 分词数量               |
| data[].type               | string        | 文档类型               |
| data[].update\_date       | string        | 最后更新时间 (GMT)       |
| data[].update\_time       | integer       | 最后更新时间戳（毫秒 Unix）   |
| message                   | string        | 响应消息               |