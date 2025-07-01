此项目是著名开源项目ragflow的前端，搜索任何代码时一定要排除node_modules文件夹。

项目根目录为“web”，使用 **Umi 4** 框架（基于 React），采用 **TypeScript** 编写，目录结构包含典型的前端源代码目录和配置，例如：`src/`（源码）、`public/`（静态资源）、配置文件（如 `.umirc.ts`、`tsconfig.json`、`.eslintrc.js` 等）以及样式相关文件（如 `tailwind.config.js`、`tailwind.css`）。在 `src/` 下有子目录：`components`（通用组件）、`pages`（业务页面）、`layouts`（布局）、`services`（API 服务）、`utils`（工具函数）、`hooks`（自定义React Hook）、`constants`（常量）、`assets`（资源文件）、`locales`（本地化文件）等。这表明**该项目是一个使用 Ant Design Pro 技术栈的 React 管理系统**，包含国际化、本地存储、布局框架等通用模块。

**主要开发语言**：TypeScript/TSX（React JSX+TS），以及少量Less和Tailwind CSS用于样式。

**主要依赖**（根据 `package.json`）：

* **UI框架**：Ant Design 系列（如 `@ant-design/pro-components`，`@ant-design/pro-layout`）以及 Ant Design 图标库。这意味着界面大量使用 Ant Design 提供的组件和布局。
* **可视化库**：AntV 图表库 G2/G6（用于图表和流程图），这些库是框架无关的，可在 Vue 项目中继续使用。
* **表单与验证**：React Hook Form 相关（`@hookform/resolvers`），React 体系特有，在 Vue 需寻找替代方案。
* **富文本/编辑器**：Facebook Lexical 富文本（`@lexical/react`）和 Monaco 编辑器（`@monaco-editor/react`）等。这些都是 React 实现，需要换用 Vue 兼容的富文本编辑器组件（例如 TipTap、Quill 等）和 Monaco 的Vue包装。
* **基础工具库**：包含 Lodash、UUID 等工具类型库（通过类型声明可见），可直接在新项目复用。
* **React基础**：Umi 框架自身和 React 相关依赖（如 `umi`、`umi-request` 请求库）。React、React-DOM本身可能由 Umi 间接依赖管理，因此未直接列出。状态管理方面未显式看到 Redux 等，但有 `@redux-devtools/extension` 用于调试，推测**原项目使用了 Umi 提供的 model 插件或 Zustand 等进行状态管理**。

项目环境搭建：

​     安装nodejs最新版，然后在web目录下，执行npm install。

​     执行：npm  run dev

​     访问：http://localhost/

项目结构如下

web/

.husky/          \# git hooks

public/              # 公共静态资源

     pdfjs-dist 这个下面是预览pdf相关的脚本

src/

     app.tsx # 入口文件
    
     routes.ts  # 路由定义
    
     assets/            # 图片/静态资源
    
     components/        # 组件库
    
     constants/         # 常量
    
     hooks/             # React hooks
    
      interfaces/        # TypeScript 接口
    
     layouts/           # 布局相关
    
     less/              # 样式
    
      lib/               # 工具库
    
     locales/           # 多语言
    
     pages/             # 页面级组件
    
     services/          # API服务
    
     theme/             # 主题
    
     utils/             # 工具函数
    
     wrappers/      # 包装组件（高阶组件）

### 模块说明

| 目录/文件 | 作用描述 |
| --- | --- |
| `app.tsx` | 应用入口文件，挂载根组件并引入全局配置 |
| `routes.ts` | Umi 路由配置与菜单映射 |
| `assets/` | 静态图片等资源 |
| `components/` | 可复用的通用 React 组件库 |
| `constants/` | 枚举及常量定义 |
| `hooks/` | 自定义 React Hooks，封装业务逻辑 |
| `interfaces/` | TypeScript 类型与接口声明 |
| `layouts/` | 页面布局相关组件 |
| `less/` | 全局 Less 样式与变量 |
| `lib/` | 小工具库，独立于框架 |
| `locales/` | 多语言国际化文件 |
| `pages/` | 业务页面目录，对应路由页面 |
| `services/` | 与后端交互的 API 服务封装 |
| `theme/` | 主题配置及样式变量 |
| `utils/` | 通用工具函数 |
| `wrappers/` | 路由包装或高阶组件 |
## 页面迁移分析

项目的路由定义集中在 `src/routes.ts`。`/login` 和 `/login-next` 两个登录页不使用认证包裹，其余路由都通过 `wrappers/auth` 进行登录校验。当用户未登录访问受限页面时会被重定向到登录页。

登录成功后，`pages/login/index.tsx` 会调用 `navigate('/knowledge')` 跳转到知识库首页。此页面展示知识库列表，可通过创建按钮跳转至 `/knowledge/dataset?id=KB_ID` 等子路由继续配置、测试或上传文档。

主框架下还包含聊天、搜索、代理管理等模块，例如 `/next-chats`、`/next-searches`、`/agents` 等。所有这些页面在登录后都可以通过顶部菜单或侧边栏进行切换，页面迁移都由 `useNavigate` 或 `<Link>` 组件完成。

整体流程如下：
1. 访问 `/login` 进行登录 → 成功后跳转 `/knowledge`。
2. 在知识库页可以进一步跳转至数据集上传、配置或测试等子模块。
3. 通过导航栏可切换到聊天、搜索、文件管理、个人设置等其它页面，路由切换保持登录态。
## 页面布局分析

`src/layouts` 目录下定义了全局页面框架，各路由通过配置 `layout` 属性决定使用哪种布局。

- **index.tsx**：默认布局，顶部使用 `components/header`，主体为 Ant Design `Layout` 的 `Content` 区域，通过 `<Outlet />` 渲染子路由。根据用户角色决定使用何种头部组件。
- **next.tsx**：为新版界面提供轻量布局，包含 `next-header` 头部和内容区域，常用于 `/home`、`/datasets` 等路由。
- **chat-only.tsx**：仅保留聊天相关的最小界面，依旧通过 `ChatOnlyHeader` 配合 `<Outlet />` 呈现内容。
- 三个布局都使用 `<Outlet />` 作为子路由占位，确保页面切换时保持统一框架。
- 各布局头部组件（如 `next-header`、`chat-only-header`）内实现导航跳转、主题与语言切换等交互，内部大多依赖 `useNavigate` 相关 Hook。

## 用户角色模式（基于role字段）

项目根据用户的 `role` 字段实现不同的界面模式，替代了之前的 `simple=1` 参数模式：

### 角色分类
- **普通用户（role: "normal"）**：系统自动进入简化模式（ChatOnly模式）
- **非普通用户（role不为"normal"）**：显示完整的管理界面功能

### 核心实现逻辑
- **登录跳转**：`pages/login/index.tsx` 中，普通用户登录后跳转到 `/chat`，其他用户跳转到 `/knowledge`
- **角色判断**：通过 `authorizationUtil.isNormalRole()` 函数判断是否为普通用户（`role === 'normal'`）
- **界面切换**：各布局组件使用 `isNormalRole()` 来决定渲染方式

### 主要影响点
- **头部导航**：`layouts/index.tsx` 和 `layouts/next.tsx` 根据 `isNormalRole()` 决定显示 `ChatOnlyHeader` 或完整 `Header`
- **用户设置侧边栏**：`pages/user-setting/sidebar/index.tsx` 中，普通用户仅显示：
  - Profile（个人资料）
  - Password（修改密码）  
  - Logout（退出登录）
  
  隐藏管理功能：Model（模型提供商）、System（系统设置）、Api（API管理）、Team（团队管理）
- **聊天页面**：`pages/chat/index.tsx` 普通用户不显示新建助手等高级功能，只保留基础聊天界面

### 实现细节
- 角色信息存储在 `localStorage` 的 `userInfo` 中
- `authorizationUtil.getUserRole()` 从本地存储中获取角色
- `authorizationUtil.isNormalRole()` 判断当前用户是否为普通用户
- 所有角色相关的UI控制都基于这个统一的判断方法

该角色控制机制用于区分普通用户和管理用户，确保不同权限用户看到相应的功能界面。

## 登录与用户数据管理
登录接口为 `/v1/user/login`，成功后会返回包含用户信息的 JSON，如下所示：

```json
{
  "code": 0,
  "data": {
    "access_token": "aa3888324a6d11f09958001a7dda7113",
    "avatar": null,
    "color_schema": "Bright",
    "create_date": "Fri, 13 Jun 2025 13:18:46 GMT",
    "create_time": 1749791926098,
    "email": "xiyuan27@163.com",
    "id": "e08c2142481511f0b121010101010000",
    "is_active": "1",
    "is_anonymous": "0",
    "is_authenticated": "1",
    "is_superuser": false,
    "language": "Chinese",
    "last_login_time": "Fri, 13 Jun 2025 13:18:44 GMT",
    "login_channel": "password",
    "nickname": "xiyuan27",
    "password": "scrypt:32768:8:1$STnyHpi8QEpXwMT5$a3c1a07d6e9b1a276f56dce5df5bbc8bfbcd91b941e208ab8712a4ad279c157198fdf1e5373171c60efa553086d71a17297d4e75494e35a1fdfbf38e4d0f7e1e",
    "status": "1",
    "timezone": "UTC+8\tAsia/Shanghai",
    "update_date": ["Mon, 16 Jun 2025 12:52:11 GMT"],
    "update_time": [1750049531620]
  },
  "message": "Welcome back!"
}
```


`src/pages/login/index.tsx` 通过 `useLogin` 与后端接口交互，也可通过 `useLoginWithChannel` 跳转至如知乎等第三方渠道登录。成功后返回的用户数据结构在 `interfaces/database/user-setting.ts` 中定义：

```ts
export interface IUserInfo {
  access_token: string;
  avatar?: any;
  color_schema: string;
  create_date: string;
  create_time: number;
  email: string;
  id: string;
  is_active: string;
  is_anonymous: string;
  is_authenticated: string;
  is_superuser: boolean;
  language: string;
  last_login_time: string;
  login_channel: string;
  nickname: string;
  role: string;  // 用户角色：'normal' 为普通用户，其他为管理用户
  password: string;
  status: string;
  update_date: string;
  update_time: number;
}
```

`useLogin` 在登录成功后会提取响应头中的 `Authorization`，连同 `access_token` 与用户信息写入浏览器 `localStorage`：

```ts
authorizationUtil.setItems({
  Authorization: authorization,
  userInfo: JSON.stringify(userInfo),
  Token: token,
});
```

此后 `useFetchUserInfo` 会再次请求 `/user/info`，根据返回的 `language` 字段切换站点语言，并更新本地存储。

`hooks/auth-hooks.ts` 判断 URL 中是否存在 `auth` 参数或本地 `Authorization`，以确定 `isLogin` 状态；`wrappers/auth.tsx` 在路由层面拦截未登录访问并重定向到 `/login`。整体流程确保登录状态和用户数据在页面切换时保持一致。


## 登出处理

`useLogout` 钩子会发送 `GET /v1/user/logout` 请求。返回值 `code` 为 0 时会执行：
1. `authorizationUtil.removeAll()` 清除 `Authorization`、`token` 与 `userInfo` 等本地存储数据；
2. 通过 `redirectToLogin()` 将用户重定向到 `/login`；
3. 弹出 "logout" 提示信息。

在 `request.ts` 的响应拦截器中，若接口返回 `401` 也会调用相同的逻辑，确保失效的会话被清理并重新登录。

