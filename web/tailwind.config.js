/** 
 * @type {import('tailwindcss').Config} 
 * 这是 TypeScript 的 JSDoc 类型注释，作用如下：
 * 1. 类型提示：告诉 TypeScript 编译器和 IDE 这个变量遵循 Tailwind CSS 的配置类型定义
 * 2. 智能提示：在编辑器中提供自动完成、参数提示和错误检查功能
 * 3. 类型安全：确保配置对象的属性和值符合 Tailwind CSS 的规范
 * 4. 开发体验：帮助开发者避免配置错误，提高开发效率
 * 5. 文档说明：明确标识这是一个 Tailwind CSS 配置文件
 */
module.exports = {
	// 内容扫描配置：指定 Tailwind 需要扫描的文件，只生成实际使用的样式
	content: ['./index.html', './src/**/*.{vue,js}'],
	
	// 主题配置：自定义 Tailwind CSS 的设计主题
	theme: {
		// 扩展默认主题配置，保留原有样式并添加自定义配置
		extend: {
			// 高度配置扩展：添加自定义的高度实用类
			height: {
				'screen/2': '50vh', // 创建 h-screen/2 类，高度为视口的50%
			},
		},
	},
	
	// 插件配置：扩展 Tailwind CSS 功能的插件数组
	plugins: [],
}; 