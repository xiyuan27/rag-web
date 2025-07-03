 /v1/system/token_list 接口详细分析

  基于我对代码的深入分析，现在为你提供完整的接口功能分析：

  🔍 接口基本信息

  - 路径: GET /v1/system/token_list
  - 认证: 需要登录 (@login_required)
  - 功能: 获取当前用户租户的所有API Token列表

  📥 输入参数

  请求方式: GET
  请求头:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json
  请求体: 无（GET请求）

  📤 输出数据结构

  成功响应 (HTTP 200):
  {
    "code": 0,
    "message": "",
    "data": [
      {
        "tenant_id": "租户ID",
        "token": "API密钥字符串",
        "dialog_id": "关联的对话ID（可选）",
        "source": "来源类型: none|agent|dialog",
        "beta": "Beta密钥（32位字符串）",
        "create_date": "创建日期",
        "create_time": 1234567890,
        "update_date": "更新日期",
        "update_time": 1234567890
      }
    ]
  }

  错误响应:
  {
    "code": 500,
    "message": "错误描述",
    "data": false
  }

  ⚙️ 核心处理逻辑

  def token_list():
      # 1. 获取当前用户的租户信息
      tenants = UserTenantService.query(user_id=current_user.id)

      # 2. 找到用户拥有owner权限的租户
      tenant_id = [tenant for tenant in tenants if tenant.role == 'owner'][0].tenant_id
    
      # 3. 查询该租户下的所有API Token
      objs = APITokenService.query(tenant_id=tenant_id)
    
      # 4. 处理beta字段 - 如果为空则生成新的beta密钥
      for o in objs:
          if not o["beta"]:
              # 基于租户ID生成双重加密的32位beta密钥
              o["beta"] = generate_confirmation_token(
                  generate_confirmation_token(tenants[0].tenant_id)
              ).replace("ragflow-", "")[:32]
              # 更新数据库
              APITokenService.filter_update([
                  APIToken.tenant_id == tenant_id,
                  APIToken.token == o["token"]
              ], o)
    
      return get_json_result(data=objs)

  🔑 API Token数据模型

  数据库表结构 (api_token):
  CREATE TABLE api_token (
    tenant_id VARCHAR(32) NOT NULL,    -- 租户ID
    token VARCHAR(255) NOT NULL,       -- API密钥
    dialog_id VARCHAR(32),             -- 关联对话ID（可选）
    source VARCHAR(16),                -- 来源: none|agent|dialog
    beta VARCHAR(255),                 -- Beta密钥（用于特殊认证）
    create_time BIGINT,                -- 创建时间戳
    create_date VARCHAR(50),           -- 创建日期字符串
    update_time BIGINT,                -- 更新时间戳
    update_date VARCHAR(50),           -- 更新日期字符串
    PRIMARY KEY (tenant_id, token)
  );

  🎯 使用场景和目的

  1. API管理界面: 用于显示用户创建的所有API Token
  2. 外部系统集成: 获取可用的API密钥列表
  3. 聊天嵌入: 为嵌入聊天窗口提供认证Token
  4. 开发者工具: 管理和监控API访问权限

  🔒 安全机制

  1. 权限控制: 只有租户owner才能查看Token列表
  2. Beta密钥: 自动生成双重加密的辅助密钥
  3. 租户隔离: 用户只能看到自己租户的Token
  4. JWT认证: 需要有效的登录态

  💡 Beta密钥生成逻辑

  # 双重加密生成32位beta密钥
  def generate_beta_key(tenant_id):
      # 第一次加密
      inner_token = generate_confirmation_token(tenant_id)
      # 第二次加密
      outer_token = generate_confirmation_token(inner_token)
      # 提取32位字符作为beta密钥
      return outer_token.replace("ragflow-", "")[:32]

  🚀 前端集成方式

  // 1. 获取Token列表
  const { data: tokenList } = await userService.listToken();

  // 2. 使用Token进行API调用
  const response = await fetch('/api/v1/conversation/completion', {
    headers: {
      'Authorization': `Bearer ${tokenList[0].token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({...})
  });

  🎯 嵌入聊天窗口的关键用途

  1. 获取API密钥: 为外部系统提供访问RAGFlow的认证凭据
  2. 管理多个Token: 支持为不同的外部系统创建独立的API密钥
  3. Token状态管理: 监控Token的使用情况和有效期
  4. 安全隔离: 确保不同外部系统之间的访问隔离

  这个接口是实现聊天窗口嵌入功能的重要基础，通过它获取的API Token可以用于外部系统调用RAGFlow的对话接口。