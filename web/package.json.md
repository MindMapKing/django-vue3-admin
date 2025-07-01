# Package.json 配置详解

## 项目基本信息

### name: "django-vue3-admin"
- **功能**: 项目名称，通常与项目文件夹名称保持一致
- **用途**: NPM 包管理、项目识别

### version: "3.1.0"
- **功能**: 项目版本号，遵循语义化版本控制（SemVer）规范
- **格式**: 主版本.次版本.修订版本
- **用途**: 版本管理、依赖控制

### description
- **功能**: 项目描述信息，详细说明项目的特性和技术栈
- **内容**: 基于RBAC模型的权限控制开发平台，前后端分离架构

### license: "MIT"
- **功能**: 开源许可证类型
- **特点**: MIT 许可证允许自由使用、修改和分发

## NPM 脚本命令 (scripts)

### "dev": "vite --force"
- **功能**: 开发环境启动命令
- **参数**: --force 强制重新构建依赖
- **用途**: 本地开发调试

### "build:dev": "vite build --mode development"
- **功能**: 构建开发版本
- **用途**: 生成用于开发环境的打包文件

### "build": "vite build"
- **功能**: 生产环境构建命令
- **用途**: 生成优化后的生产版本

### "build:local": "vite build --mode local_prod"
- **功能**: 本地生产环境构建
- **用途**: 本地测试生产版本

### "lint-fix": "eslint --fix --ext .js --ext .jsx --ext .vue src/"
- **功能**: ESLint 代码检查和自动修复
- **范围**: 检查 JS、JSX、Vue 文件的代码规范

## 生产依赖 (dependencies)

### UI 组件库
- **@element-plus/icons-vue**: Element Plus 图标库，提供丰富的 SVG 图标组件
- **element-plus**: 基于 Vue 3 的桌面端组件库
- **@iconify/vue**: 统一的图标解决方案
- **font-awesome**: 图标字体库

### 状态管理与路由
- **pinia**: Vue 3 官方推荐的状态管理方案
- **pinia-plugin-persist**: Pinia 持久化插件，自动保存状态到本地存储
- **vue-router**: Vue 路由库，实现单页应用路由功能

### HTTP 请求与工具库
- **axios**: HTTP 请求库，用于与后端 API 通信
- **lodash-es**: Lodash ES 模块版本，提供实用工具函数
- **qs**: 查询字符串解析库，处理 URL 参数
- **js-cookie**: JavaScript Cookie 操作库

### 图表与可视化
- **echarts**: 核心图表库
- **echarts-gl**: 3D 渲染扩展
- **echarts-wordcloud**: 词云图扩展

### 富文本编辑器
- **@wangeditor/editor**: 编辑器核心
- **@wangeditor/editor-for-vue**: Vue 适配器

### 快速开发框架
- **@fast-crud/fast-crud**: 快速 CRUD 开发框架核心包
- **@fast-crud/fast-extends**: 扩展包
- **@fast-crud/ui-element**: Element Plus UI 适配器
- **@fast-crud/ui-interface**: UI 接口定义

### 表格组件
- **vxe-table**: 高性能表格组件
- **xe-utils**: 实用工具库，配合 VXE Table 使用

### CSS 框架与样式
- **tailwindcss**: 实用程序优先的 CSS 框架
- **autoprefixer**: CSS 自动前缀工具，确保浏览器兼容性
- **postcss**: CSS 后处理工具

### 功能性库
- **vue-i18n**: Vue 国际化库，支持多语言
- **countup.js**: 数字动画库，实现数字递增效果
- **cropperjs**: 图片裁剪库
- **vue-cropper**: Vue 图片裁剪组件
- **nprogress**: 页面加载进度条库
- **mitt**: 轻量级事件总线，用于组件间通信
- **sortablejs**: 拖拽排序库
- **splitpanes**: 分割面板组件
- **vue-grid-layout**: Vue 网格拖拽布局组件
- **jsplumb**: 连线图库，用于创建流程图、拓扑图等
- **screenfull**: 全屏 API 封装库
- **print-js**: 打印功能库
- **qrcodejs2-fixes**: 二维码生成库
- **vue-clipboard3**: Vue 剪贴板操作库

### 特殊功能库
- **date-holidays**: 假期日期库，处理各国假期信息
- **lunar-javascript**: 农历 JavaScript 库
- **ts-md5**: TypeScript MD5 哈希库
- **js-table2excel**: 表格导出 Excel 功能库

## 开发依赖 (devDependencies)

### 构建工具
- **vite**: 现代化的前端构建工具
- **@vitejs/plugin-vue**: Vite Vue 插件，支持 Vue 单文件组件
- **@vitejs/plugin-vue-jsx**: Vite Vue JSX 插件
- **vite-plugin-vue-setup-extend**: Vue Setup 扩展插件

### TypeScript 相关
- **typescript**: TypeScript 编译器
- **@vue/compiler-sfc**: Vue 单文件组件编译器
- **@types/node**: Node.js 类型定义文件
- **@types/nprogress**: NProgress 类型定义文件
- **@types/sortablejs**: SortableJS 类型定义文件

### 代码质量工具
- **eslint**: 代码检查工具
- **eslint-plugin-vue**: Vue ESLint 插件
- **vue-eslint-parser**: Vue ESLint 解析器
- **@typescript-eslint/eslint-plugin**: TypeScript ESLint 插件
- **@typescript-eslint/parser**: TypeScript 解析器
- **prettier**: 代码格式化工具

### 样式处理
- **sass**: CSS 预处理器

## 浏览器支持 (browserslist)

### "> 1%"
- **功能**: 支持全球使用率大于 1% 的浏览器
- **用途**: 确保覆盖主流用户群体

### "last 2 versions"
- **功能**: 支持每个浏览器的最后 2 个版本
- **用途**: 保持现代浏览器特性支持

### "not dead"
- **功能**: 排除已停止维护的浏览器
- **用途**: 避免为过时浏览器提供支持

## 运行环境要求 (engines)

### "node": ">=16.0.0"
- **功能**: 要求 Node.js 版本 16.0.0 及以上
- **原因**: 确保支持现代 JavaScript 特性

### "npm": ">= 7.0.0"
- **功能**: 要求 NPM 版本 7.0.0 及以上
- **原因**: 利用新版本 NPM 的性能优化

## 项目元数据

### keywords
- **功能**: 项目关键词，用于 NPM 包搜索和分类
- **内容**: vue, vue3, element-ui, element-plus, django-vue3-admin, django, django-restframework

### repository
- **功能**: 代码仓库信息
- **地址**: https://gitee.com/huge-dream/django-vue3-admin.git
- **用途**: 指向项目的 Git 仓库地址 