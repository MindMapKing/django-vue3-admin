// 导入 Vue 插件，用于处理 .vue 单文件组件
import vue from '@vitejs/plugin-vue';
// 导入 Node.js 的 path 模块，用于路径解析
import { resolve } from 'path';
// 导入 Vite 的核心配置函数和类型
import { defineConfig, loadEnv, ConfigEnv } from 'vite';
// 导入 Vue setup 语法糖扩展插件，支持在 <script setup> 中使用 name 属性
import vueSetupExtend from 'vite-plugin-vue-setup-extend';
// 导入 Vue JSX 插件，支持在 Vue 中使用 JSX 语法
import vueJsx from '@vitejs/plugin-vue-jsx'
// 导入版本文件生成工具函数
import { generateVersionFile } from "/@/utils/upgrade";

/**
 * 路径解析函数
 * @param dir 目录名
 * @returns 返回基于当前文件目录的绝对路径
 */
const pathResolve = (dir: string) => {
	// __dirname 是 Node.js 中的全局变量，表示当前执行脚本所在的目录的绝对路径
	// 在 ES 模块中，需要使用 import.meta.url 和 fileURLToPath 来获取当前文件目录
	// 这里使用 resolve 函数将当前目录、相对路径标识符 '.' 和传入的目录名组合成绝对路径
	return resolve(process.cwd(), dir);
};

/**
 * 路径别名配置
 * 定义模块导入的路径别名，简化导入路径
 */
// Record<K, V> 是 TypeScript 的内置工具类型，用于创建一个对象类型
// 其中所有属性的键类型为 K，值类型为 V
// Record<string, string> 表示一个对象，键和值都是字符串类型
// 等价于 { [key: string]: string }
const alias: Record<string, string> = {
	'/@': pathResolve('./src/'),  // 将 /@/ 映射到 src 目录
	'@great-dream': pathResolve('./node_modules/@great-dream/'),  // 第三方组件库路径
	'@views': pathResolve('./src/views'),  // 视图组件路径别名
	'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',  // vue-i18n 国际化库路径
	'@dvaformflow':pathResolve('./src/viwes/plugins/dvaadmin_form_flow/src/')  // 表单流插件路径
};

/**
 * Vite 配置定义
 * 根据不同的构建模式（开发/生产）返回相应的配置
 */
const viteConfig = defineConfig((mode: ConfigEnv) => {
	// 加载环境变量配置文件（.env）
	const env = loadEnv(mode.mode, process.cwd());
	
	// 当Vite构建时，生成版本文件用于版本管理
	generateVersionFile()
	
	return {
		// 插件配置数组
		plugins: [
			vue(),  // Vue 单文件组件支持
			vueJsx(),  // Vue JSX 语法支持
			vueSetupExtend()  // Vue setup 语法糖扩展
		],
		
		// 项目根目录
		root: process.cwd(),
		
		// 路径解析配置
		resolve: { alias },
		
		// 基础公共路径：开发模式使用相对路径，生产模式使用环境变量配置
		base: mode.command === 'serve' ? './' : env.VITE_PUBLIC_PATH,
		
		// 依赖预构建配置
		optimizeDeps: {
			// 预构建包含的依赖项（Element Plus 的不同语言包）
			include: [
				'element-plus/es/locale/lang/zh-cn',  // 中文简体
				'element-plus/es/locale/lang/en',     // 英文
				'element-plus/es/locale/lang/zh-tw'   // 中文繁体
			],
		},
		
		// 开发服务器配置
		server: {
			host: '0.0.0.0',  // 监听所有网络接口
			// 这是TypeScript的双重类型断言用法：
			// 1. env.VITE_PORT 从环境变量获取，类型为 string | undefined
			// 2. 'as unknown' 将其断言为 unknown 类型（万能类型）
			// 3. 'as number' 再将 unknown 断言为 number 类型
			// 这样可以绕过TypeScript的类型检查，强制将字符串转换为数字类型
			// 注意：实际运行时需要确保 VITE_PORT 是有效的数字字符串
			port: env.VITE_PORT as unknown as number,  // 端口号从环境变量获取
			open: false,  // 启动时不自动打开浏览器
			hmr: true,  // 启用热模块替换
			
			// 代理配置，用于解决开发环境的跨域问题
			proxy: {
				'/gitee': {
					target: 'https://gitee.com',  // 代理目标地址
					ws: true,  // 支持 WebSocket
					changeOrigin: true,  // 改变请求头中的 Origin
					rewrite: (path) => path.replace(/^\/gitee/, ''),  // 重写路径，移除 /gitee 前缀
				},
			},
		},
		
		// 生产构建配置
		build: {
			outDir: env.VITE_DIST_PATH || 'dist',  // 构建输出目录
			// chunkSizeWarningLimit: chunk 大小警告阈值配置
			// 作用：设置单个 chunk 文件大小的警告阈值（单位：KB）
			// 当打包后的 chunk 文件超过此大小时，Vite 会在构建时输出警告信息
			// 默认值：500KB，这里设置为 1500KB（1.5MB）
			// 用途：
			// 1. 帮助开发者识别过大的代码块，优化打包性能
			// 2. 避免单个文件过大影响首屏加载速度
			// 3. 提醒开发者进行代码分割优化
			chunkSizeWarningLimit: 1500,  // chunk 大小警告阈值（KB）
			
			// Rollup 打包选项
			rollupOptions: {
				output: {
					// 入口文件命名格式
					entryFileNames: `assets/[name].[hash].js`,
					// 代码分割后的 chunk 文件命名格式
					chunkFileNames: `assets/[name].[hash].js`,
					// 静态资源文件命名格式
					assetFileNames: `assets/[name].[hash].[ext]`,
					compact: true,  // 压缩输出
					
					// 手动代码分割配置
					// manualChunks: 手动代码分割配置
					// 作用：将特定的模块打包到指定的 chunk 文件中，而不是放在默认的 vendor chunk 里
					// 优势：
					// 1. 缓存优化：不同库分别打包，更新其中一个库时不影响其他库的缓存
					// 2. 并行加载：浏览器可以同时下载多个较小的文件，提升加载速度
					// 3. 按需加载：可以根据路由或功能模块进行更精细的代码分割
					// 4. 减少重复：避免相同依赖在多个 chunk 中重复打包
					manualChunks: {
						vue: ['vue', 'vue-router', 'pinia'],  // Vue 生态系统库单独打包为 vue.js
						echarts: ['echarts'],  // 图表库单独打包为 echarts.js，因为体积较大且不是每个页面都需要
					},
				},
			},
		},
		
		// CSS 预处理器配置
		// CSS 预处理器配置
		// css: CSS 相关配置选项
		// 作用：配置 CSS 预处理器和 CSS 处理相关的选项
		// preprocessorOptions: 预处理器选项配置
		// 作用：为不同的 CSS 预处理器（如 Sass、Less、Stylus）提供特定的配置选项
		// css.charset: CSS 字符集声明控制
		// 作用：控制是否在生成的 CSS 文件开头添加 @charset "UTF-8"; 声明
		// 设置为 false 的原因：
		// 1. 避免字符集冲突：某些情况下多个 @charset 声明会导致 CSS 解析错误
		// 2. 减少文件体积：去除不必要的字符集声明，稍微减小打包后的文件大小
		// 3. 兼容性考虑：某些老旧的 CSS 处理工具可能对 @charset 声明处理不当
		// 4. 现代浏览器默认使用 UTF-8：大多数现代浏览器会自动使用 UTF-8 编码处理 CSS
		css: { 
			preprocessorOptions: { 
				css: { charset: false }  // 禁用 CSS 字符集声明，避免重复声明和兼容性问题
			} 
		},
		
		// 全局常量定义，在代码中可直接使用
		define: {
			// Vue I18n 配置项
			__VUE_I18N_LEGACY_API__: JSON.stringify(false),  // 禁用旧版 API
			__VUE_I18N_FULL_INSTALL__: JSON.stringify(false),  // 不完整安装
			__INTLIFY_PROD_DEVTOOLS__: JSON.stringify(false),  // 生产环境禁用开发工具
			__VERSION__: JSON.stringify(process.env.npm_package_version),  // 注入版本号
		},
	};
});

// 导出 Vite 配置
export default viteConfig;

