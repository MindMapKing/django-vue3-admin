/**
 * PostCSS 配置文件
 * PostCSS 是一个用 JavaScript 工具和插件转换 CSS 代码的工具
 * 在构建过程中对 CSS 进行预处理和后处理
 */
module.exports = {
  // PostCSS 插件配置对象
  // 插件按照数组顺序依次执行，顺序很重要
  plugins: {
    // Tailwind CSS 插件配置
    // 用于处理 Tailwind CSS 实用程序类，生成最终的 CSS 代码
    // {} 表示使用默认配置，会自动读取 tailwind.config.js 文件
    tailwindcss: {},
    
    // Autoprefixer 插件配置  
    // 自动为 CSS 属性添加浏览器厂商前缀（如 -webkit-, -moz- 等）
    // 基于 Can I Use 数据库，确保 CSS 在不同浏览器中的兼容性
    // {} 表示使用默认配置，会读取 .browserslistrc 或 package.json 中的 browserslist 配置
    autoprefixer: {},
  },
}
