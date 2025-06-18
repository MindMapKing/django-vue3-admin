# Python 和 TypeScript 实战学习计划（优化版）

**目标用户**：有 Java 基础，想通过实际项目学习 Python 和 TypeScript
**项目技术栈**：
- 后端：Python + Django
- 前端：TypeScript + Vue3
**更新时间**：2025-06-18 09:15:00

---
## 学习阶段规划

### 阶段1：环境与基础结构
**学习目标**
- 掌握项目目录结构
- 理解前后端分离架构

**关键文件**
- `backend/application/settings.py` (Django配置)
- `web/vite.config.ts` (前端构建配置)
- `docker_env/docker-compose.yml` (容器环境)

**实践任务**
- [ ] 使用`docker-compose up`启动完整项目
- [ ] 修改`web/src/main.ts`添加启动日志

### 阶段2：启动流程解析
**后端启动流程**
1. 加载Django配置 (`settings.py`)
2. 初始化中间件和路由 (`urls.py`)
3. 启动WSGI服务器 (`manage.py runserver`)

**前端启动流程**
1. Vite编译TS/SCSS (`vite.config.ts`)
2. 挂载Vue实例 (`main.ts`)
3. 加载路由配置 (`src/router/route.ts`)

**实践任务**
- [ ] 在`backend/application/__init__.py`添加启动钩子
- [ ] 追踪`web/src/layout/index.vue`组件加载过程

### 阶段3：请求处理流程
**前端请求发起**
```typescript
// web/src/utils/request.ts
axios.request({
  url: "/api/data",
  method: "GET",
  headers: { Authorization: "Bearer xxx" }
})
```

**后端处理流程**
1. 请求进入中间件 (认证/限流)
2. 路由匹配 (`urls.py -> views.py`)
3. ORM数据库操作 (`models.py`)
4. 响应序列化 (`serializers.py`)

**实践任务**
- [ ] 添加请求日志中间件 (`backend/middleware/logging.py`)
- [ ] 创建带JWT认证的API端点

### 阶段4：核心模块深度
#### 1. 权限控制系统
**实现路径** `web/src/plugin/permission/`
```typescript
// 指令式权限控制 (directive.permission.ts)
v-auth="'system:user:add'" // 按钮级权限

// 函数式权限校验 (func.permission.ts)
authFunction("system:dept:edit")

// 路由守卫 (index.ts)
router.beforeEach(permission)
```

**学习任务**
- [ ] 在`web/src/views/system/role/`跟踪权限分配流程

#### 2. 状态管理 (Pinia)
**核心文件** `web/src/stores/`
```typescript
// 创建store (dept.ts)
export const useDeptStore = defineStore("dept", {
  state: () => ({ deptData: [] }),
  actions: {
    async getDeptList() {
      this.deptData = await getDeptListApi();
    }
  }
})

// 组件中使用
const store = useDeptStore()
store.getDeptList()
```

#### 3. 动态路由系统
**入口文件** `web/src/router/route.ts`
```typescript
// 路由结构
const routes: Array<Route> = [
  {
    path: "/system",
    component: layout,
    children: [
      {
        path: "user",
        name: "SystemUser",
        component: () => import("@/views/system/user/index.vue")
      }
    ]
  }
]

// 路由守卫添加权限验证
router.beforeEach(async (to, from, next) => {
  if (!store.permissionState) {
    await store.setFilterRoutes()
  }
  next()
})
```

**实践任务**
- [ ] 添加需要权限验证的新路由
- [ ] 创建带状态管理的部门选择器组件

### 阶段5：全栈集成实战
1. [ ] 商品管理模块 (CRUD+分页+搜索)
2. [ ] 实时消息通知 (WebSocket)
3. [ ] 自动化部署脚本 (CI/CD)

---
## 学习资源
1. [Django 中间件机制](https://docs.djangoproject.com/en/5.0/topics/http/middleware/)
2. [Vue3 组合式API](https://vuejs.org/guide/extras/composition-api-faq.html)
3. [Axios 拦截器文档](https://axios-http.com/docs/interceptors)
4. [Django REST Framework](https://www.django-rest-framework.org/)

> 提示：使用 `search_files` 工具快速定位代码模式 (如搜索`axios\.request`)