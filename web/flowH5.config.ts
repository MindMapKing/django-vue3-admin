// 导入 Vite 的配置定义函数
import { defineConfig } from 'vite';
// 导入 Vue 单文件组件支持插件
import vue from '@vitejs/plugin-vue';
// 导入 Node.js 路径处理模块，resolve 用于解析绝对路径
import path, {resolve} from 'path';
// 导入 Vue JSX 语法支持插件
import vueJsx from "@vitejs/plugin-vue-jsx";
// 导入 Vue setup 语法扩展插件，支持在 <script setup> 中使用 name 属性
import vueSetupExtend from "vite-plugin-vue-setup-extend";
// 导入 Rollup 代码压缩插件
import { terser } from 'rollup-plugin-terser';
// 导入 Rollup PostCSS 处理插件
import postcss from 'rollup-plugin-postcss';
// 导入 PostCSS 的 px 转 rem 插件，用于移动端适配
import pxtorem from 'postcss-pxtorem';
// 定义路径解析辅助函数，用于生成相对于当前文件的绝对路径
const pathResolve = (dir: string) => {
  // 返回相对于当前文件目录的绝对路径
  return resolve(__dirname, '.', dir);
};
// 导出 Vite 配置对象
export default defineConfig({
  // 构建配置
  build: {
    // outDir: '../backend/static/previewer', // 可选：输出到后端静态文件目录
    // 库模式构建配置
    lib: {
      // 库的入口文件路径，指向 flowH5 模块
      entry: path.resolve(__dirname, 'src/views/plugins/dvadmin3-flow-web/src/flowH5/index.ts'), 
      // 库的全局变量名称，在 UMD 格式下使用
      name: 'previewer', 
      // 输出文件名格式函数，根据不同格式生成对应文件名
      fileName: (format) => `index.${format}.js`, 
    },
    // Rollup 特定配置选项
    rollupOptions: {
      // 多入口配置，定义 previewer 入口
      input:{
        previewer: path.resolve(__dirname, 'src/views/plugins/dvadmin3-flow-web/src/flowH5/index.ts'),
      },
      // 外部依赖配置，这些依赖不会被打包进最终文件
      external: ['vue','xe-utils'], 
      // 输出配置
      output:{
        // dir: '../backend/static/previewer', // 可选：指定输出目录
        // 入口文件命名格式
        entryFileNames: 'index.[format].js', 
        // 输出格式为 CommonJS
        format: 'commonjs',
        // 全局变量映射，将外部依赖映射为全局变量
        globals: {
          vue: 'Vue'
        },
        // 代码分割文件命名格式，包含哈希值
        chunkFileNames: `[name].[hash].js`
      },
      // Rollup 插件配置
      plugins: [
        // 代码压缩插件配置
        terser({
          compress: {
            // 保留 console.log 语句，不在压缩时移除
            drop_console: false, 
          },
        }),
        // PostCSS 处理插件配置
        postcss({
          plugins: [
            // px 转 rem 插件配置，用于移动端响应式适配
            pxtorem({
              rootValue: 37.5,        // 根字体大小，通常为设计稿宽度/10
              unitPrecision: 5,       // rem 值的小数位精度
              propList: ['*'],        // 需要转换的 CSS 属性，* 表示所有属性
              selectorBlackList: [],  // 选择器黑名单，这些选择器下的属性不转换
              replace: true,          // 是否替换原值
              mediaQuery: false,      // 是否在媒体查询中转换
              minPixelValue: 0,       // 最小转换像素值
              exclude: /node_modules/i, // 排除 node_modules 目录
            }),
          ],
        }),
      ],
    },
  },
  // Vite 插件配置
  plugins: [
    // Vue 单文件组件支持
    vue(),
    // Vue JSX 语法支持
    vueJsx(),
    // Vue setup 语法扩展支持
    vueSetupExtend(),
  ],
  // 模块解析配置
  resolve: {
    // 路径别名配置，简化导入路径
    alias: {
      // '@' 别名指向 'src' 目录，使用 Vite 风格的别名
      '/@': path.resolve(__dirname, 'src'), 
      // '@views' 别名指向 views 目录
      '@views': pathResolve('./src/views'),
      // '/src' 别名指向 src 目录
      '/src':path.resolve(__dirname, 'src')
    },
  },
  // CSS 处理配置
  css:{
    // PostCSS 配置（当前为空，可根据需要添加全局 CSS 处理规则）
    postcss:{

    }
  },
  // 全局常量定义，用于代码中的条件编译
  define: {
    // 定义 process.env 为空对象，避免浏览器环境下的 Node.js 变量错误
    'process.env': {}
  }
});