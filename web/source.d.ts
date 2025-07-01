// JSON 文件模块声明 - 允许在 TypeScript 中导入 .json 文件
// 例如: import data from './config.json'
declare module '*.json';

// PNG 图片文件模块声明 - 允许导入 .png 格式的图片文件
// 例如: import logo from './assets/logo.png'
declare module '*.png';

// JPG 图片文件模块声明 - 允许导入 .jpg 格式的图片文件
// 例如: import banner from './assets/banner.jpg'
declare module '*.jpg';

// SCSS 样式文件模块声明 - 允许导入 .scss 样式文件
// 例如: import styles from './components/Button.scss'
declare module '*.scss';

// TypeScript 文件模块声明 - 允许导入 .ts 文件作为模块
// 例如: import utils from './utils/helper.ts'
declare module '*.ts';

// JavaScript 文件模块声明 - 允许导入 .js 文件作为模块
// 例如: import legacy from './legacy/old-script.js'
declare module '*.js';
