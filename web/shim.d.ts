/* eslint-disable */
// 禁用 ESLint 检查，因为声明文件通常包含特殊语法，可能会触发 ESLint 规则

// Vue 单文件组件模块声明
// 声明文件，*.vue 后缀的文件交给 vue 模块来处理
declare module '*.vue' {
	// 从 Vue 3 导入 DefineComponent 类型，用于定义组件的类型结构
	import type { DefineComponent } from 'vue';
	
	// 声明 .vue 文件导出的组件类型
	// DefineComponent<Props, RawBindings, Data, Computed, Methods>
	// {} - Props: 空对象表示不限制 props 类型
	// {} - RawBindings: 空对象表示不限制 setup 返回值类型  
	// any - Data: 允许任意数据类型，提供最大灵活性
	const component: DefineComponent<{}, {}, any>;
	
	// 默认导出该组件，使得 import Component from './Component.vue' 语法可用
	export default component;
}

// 全局 Window 接口扩展
// 声明文件，定义全局变量。其它 app.config.globalProperties.xxx，使用 getCurrentInstance() 来获取
interface Window {
	// 全局加载状态标识，用于控制页面加载效果
	// 通常在路由切换或异步操作时使用
	nextLoading: boolean;
}
