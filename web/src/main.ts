// 应用程序主入口文件 - 负责Vue 3应用的初始化和配置
// 此文件是整个前端应用的启动点，配置所有必要的插件、组件库、国际化、路由等

// 导入Vue 3的核心createApp函数，用于创建Vue应用实例
import { createApp } from 'vue';
// 导入根组件App.vue
import App from './App.vue';
// 导入路由配置
import router from './router';
// 导入自定义指令集合
import { directive } from '/@/directive/index';
// 导入国际化(i18n)配置
import { i18n } from '/@/i18n';
// 导入其他工具函数
import other from '/@/utils/other';
// 导入Tailwind CSS样式，需要先导入以避免与Element Plus样式冲突
import '/@/assets/style/tailwind.css'; // 先引入tailwind css, 以免element-plus冲突
// 导入Element Plus UI组件库
import ElementPlus from 'element-plus';
// 导入Element Plus的默认样式
import 'element-plus/dist/index.css';
// 导入项目自定义主题样式
import '/@/theme/index.scss';
// 导入mitt事件总线库，用于组件间通信
import mitt from 'mitt';
// 导入Vue网格布局组件库
import VueGridLayout from 'vue-grid-layout';
// 导入Pinia状态管理持久化插件
import piniaPersist from 'pinia-plugin-persist';
// 导入设置配置(使用@ts-ignore忽略TypeScript类型检查)
// @ts-ignore
import fastCrud from './settings.ts';
// 导入Pinia状态管理实例
import pinia from './stores';
// 导入权限管理插件注册函数
import {RegisterPermission} from '/@/plugin/permission/index';
// 导入图标选择器组件和相关工具函数(忽略TypeScript类型检查)
// @ts-ignore
import eIconPicker, { iconList, analyzingIconForIconfont } from 'e-icon-picker';
// 导入图标选择器的基本彩色图标库
import 'e-icon-picker/icon/default-icon/symbol.js'; //基本彩色图标库
// 导入图标选择器的基本样式文件
import 'e-icon-picker/index.css'; // 基本样式，包含基本图标
// 导入Font Awesome字体图标样式
import 'font-awesome/css/font-awesome.min.css';
// 导入Element Plus图标集
import elementPlus from 'e-icon-picker/icon/ele/element-plus.js'; //element-plus的图标
// 导入Font Awesome 4.7.0版本图标集
import fontAwesome470 from 'e-icon-picker/icon/fontawesome/font-awesome.v4.7.0.js'; //fontAwesome470的图标
// 导入默认图标列表
import eIconList from 'e-icon-picker/icon/default-icon/eIconList.js';
// 导入项目自定义iconfont图标配置文件
import iconfont from '/@/assets/iconfont/iconfont.json'; //引入json文件
// 导入项目自定义iconfont样式文件
import '/@/assets/iconfont/iconfont.css'; //引入css
// 导入插件自动扫描和安装功能
// 自动注册插件
import { scanAndInstallPlugins } from '/@/views/plugins/index';
// 导入VXE Table表格组件库
import VXETable from 'vxe-table'
// 导入VXE Table的样式文件
import 'vxe-table/lib/style.css'

// 导入项目重置样式文件
import '/@/assets/style/reset.scss';
// 导入element树形组件连线样式
import 'element-tree-line/dist/style.css'

// 解析自定义iconfont图标，将JSON配置转换为可用的图标class列表
let forIconfont = analyzingIconForIconfont(iconfont); //解析class
// 将解析后的自定义图标添加到图标选择器的图标列表中
iconList.addIcon(forIconfont.list); // 添加iconfont dvadmin3的icon
// 将Element Plus图标集添加到图标选择器
iconList.addIcon(elementPlus); // 添加element plus的图标
// 将Font Awesome 4.7.0图标集添加到图标选择器
iconList.addIcon(fontAwesome470); // 添加fontAwesome 470版本的图标

// 创建Vue应用实例
let app = createApp(App);

// 扫描并自动安装项目中的插件
scanAndInstallPlugins(app);

// 配置图标选择器插件
app.use(eIconPicker, {
	addIconList: eIconList, //全局添加图标
	removeIconList: [], //全局删除图标
	zIndex: 3100, //选择器弹层的最低层,全局配置
});

// 为Pinia状态管理添加持久化插件
pinia.use(piniaPersist);
// 注册自定义指令到应用实例
directive(app);
// 注册Element Plus的SVG图标到应用实例
other.elSvg(app);

// 链式调用安装各种插件和配置到Vue应用实例
// @ts-ignore - 忽略VXETable的TypeScript类型检查
app.use(VXETable) // 安装VXE Table表格组件
	.use(pinia) // 安装Pinia状态管理
	.use(router) // 安装Vue Router路由
	.use(ElementPlus) // 安装Element Plus UI库
	.use(i18n) // 安装Vue I18n国际化
	.use(VueGridLayout) // 安装网格布局组件
	.use(fastCrud) // 安装快速CRUD组件
	.mount('#app'); // 将应用挂载到id为'app'的DOM元素上

// 在应用的全局属性中添加mitt事件总线，用于跨组件通信
app.config.globalProperties.mittBus = mitt();
