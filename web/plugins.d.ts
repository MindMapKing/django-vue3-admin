/**
 * 第三方插件/库的 TypeScript 模块声明文件
 * 为没有官方 TypeScript 类型定义的第三方库提供基础模块声明
 * 避免 TypeScript 编译时出现"找不到模块"的错误
 */

// Vue 网格布局组件库声明
// vue-grid-layout: 提供可拖拽、可调整大小的网格布局组件
// 常用于仪表板、管理后台的拖拽布局功能
declare module 'vue-grid-layout';

// 二维码生成库声明  
// qrcodejs2-fixes: QRCode.js 的修复版本，用于生成二维码
// 支持多种格式输出（Canvas、SVG、Image等）
declare module 'qrcodejs2-fixes';

// 分割面板组件库声明
// splitpanes: 提供可调整大小的分割面板组件
// 常用于代码编辑器、文件管理器等需要分屏显示的场景
declare module 'splitpanes';

// Cookie 操作工具库声明
// js-cookie: 简单易用的 JavaScript Cookie 操作库
// 提供设置、获取、删除 Cookie 的便捷方法
declare module 'js-cookie';
