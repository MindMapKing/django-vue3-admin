/**
 * Fast-CRUD 框架全局配置文件
 * 
 * 此文件负责配置整个项目中 Fast-CRUD 框架的全局设置，包括：
 * - CRUD 操作的通用配置
 * - 字典数据请求配置
 * - 文件上传配置
 * - 富文本编辑器配置
 * - 组件样式统一设置
 * 
 * @author Django-Vue3-Admin
 * @description Fast-CRUD 配置模块
 */

// 引入 Fast-CRUD 核心模块和类型工具
import {FastCrud, useTypes} from '@fast-crud/fast-crud';

// 获取组件类型配置函数
const {getType} = useTypes();

// 引入 Fast-CRUD 样式文件
import '@fast-crud/fast-crud/dist/style.css';

// 引入日志设置函数
import {setLogger} from '@fast-crud/fast-crud';

// 引入项目工具函数
import {getBaseURL} from '/@/utils/baseUrl';

// 引入 Element UI 适配器
import ui from '@fast-crud/ui-element';

// 引入项目的请求工具
import {request} from '/@/utils/service';

// 引入 Fast-CRUD 扩展包（富文本编辑器和文件上传器）
import {FsExtendsEditor, FsExtendsUploader } from '@fast-crud/fast-extends';

// 引入扩展包样式文件
import '@fast-crud/fast-extends/dist/style.css';

// 引入成功通知组件
import {successNotification} from '/@/utils/message';

// 引入 XE-Utils 工具库（用于数据转换）
import XEUtils from "xe-utils";

/**
 * Fast-CRUD 配置对象
 * 实现 Vue 插件接口，在应用启动时进行配置安装
 */
export default {
    /**
     * Vue 插件安装函数
     * @param app Vue 应用实例
     * @param options 插件配置选项
     */
    async install(app: any, options: any) {
        // 第一步：安装 Element UI 适配器
        // 必须在 FastCrud 之前安装 UI 库
        app.use(ui);
        
        // 第二步：安装并配置 FastCrud 核心框架
        app.use(FastCrud, {
            // 国际化配置（可选）
            // i18n: i18n配置，默认使用中文
            // 具体用法请参考文档中的 src/i18n/index.js 文件
            
            /**
             * 字典请求配置函数
             * 用于统一处理所有字典数据的异步请求
             * @param dict 字典配置对象
             * @param url 请求地址
             * @returns Promise<Array> 返回字典数据数组
             */
            async dictRequest({dict,url}: any) {
                // 从字典配置中提取是否为树形结构标识
                const {isTree} = dict
                
                // 发送字典数据请求
                return await request({
                    url: url, 
                    params: dict.params || {} // 传递字典参数，默认为空对象
                }).then((res: any) => {
                    // 如果是树形结构数据，使用 XE-Utils 转换为树形数组
                    if (isTree) {
                        return XEUtils.toArrayTree(res.data, {parentKey: 'parent'})
                    }
                    // 普通数组直接返回数据部分
                    return res.data
                });
            },
            
            /**
             * CRUD 通用配置函数
             * 返回所有 CRUD 操作的默认配置
             * @returns Object 通用配置对象
             */
            commonOptions() {
                return {
                    // 请求相关配置
                    request: {
                        /**
                         * 查询参数转换函数
                         * 将 Fast-CRUD 的查询参数转换为后端 API 期望的格式
                         * @param page 分页参数 {currentPage, pageSize}
                         * @param form 表单查询参数
                         * @param sort 排序参数 {prop, asc}
                         * @returns Object 转换后的请求参数
                         */
                        transformQuery: ({page, form, sort}: any) => {
                            // 处理排序参数
                            if (sort.asc !== undefined) {
                                // Django REST framework 排序格式：
                                // 升序：字段名，降序：-字段名
                                form['ordering'] = `${sort.asc ? '' : '-'}${sort.prop}`;
                            }
                            
                            // 转换分页参数格式
                            // Fast-CRUD 使用 currentPage/pageSize
                            // 后端 API 期望 page/limit
                            return {
                                page: page.currentPage, 
                                limit: page.pageSize, 
                                ...form
                            };
                        },
                        
                        /**
                         * 响应数据转换函数
                         * 将后端 API 返回的数据转换为 Fast-CRUD 期望的格式
                         * @param res 后端响应数据
                         * @returns Object Fast-CRUD 格式的数据 {records, currentPage, pageSize, total}
                         */
                        transformRes: ({res}: any) => {
                            return {
                                records: res.data,        // 数据列表
                                currentPage: res.page,    // 当前页码
                                pageSize: res.limit,      // 每页数量
                                total: res.total          // 总记录数
                            };
                        },
                    },
                    
                    // 表单相关配置
                    form: {
                        /**
                         * 表单提交后的回调函数
                         * 用于处理提交成功后的用户提示
                         * @param ctx 上下文对象，包含响应数据
                         */
                        afterSubmit(ctx: any) {
                            const {res} = ctx
                            
                            // 检查响应状态码是否为成功
                            if (res?.code == 2000) {
                                // 显示成功通知消息
                                successNotification(ctx.res.msg);
                            } else {
                                // 失败时直接返回，不显示通知
                                return
                            }
                        },
                    },
                    
                    // 搜索配置（已注释，可根据需要启用）
                    /* search: {
                        layout: 'multi-line',    // 多行布局
                        collapse: true,          // 可折叠
                        col: {
                            span: 4,            // 列宽度
                        },
                        options: {
                            labelCol: {
                                style: {
                                    width: '100px',  // 标签宽度
                                },
                            },
                        },
                    }, */
                };
            },
            
            // 日志配置：关闭表格列的日志输出
            logger: { off: { tableColumns: false } }
        });
        
        // 第三步：配置富文本编辑器扩展
        app.use(FsExtendsEditor, {
            // wangEditor 配置
            wangEditor: {
                width: 300,  // 编辑器宽度
            },
        });
        
        // 第四步：配置文件上传器扩展
        app.use(FsExtendsUploader, {
            // 默认上传类型为表单上传
            defaultType: "form",
            
            // 表单上传配置
            form: {
                // 上传接口地址
                action: `/api/system/file/`,
                
                // 文件字段名
                name: "file",
                
                // 不携带认证信息
                withCredentials: false,
                
                /**
                 * 自定义上传请求函数
                 * @param action 上传地址
                 * @param file 要上传的文件
                 * @param onProgress 进度回调函数
                 * @returns Promise 上传结果
                 */
                uploadRequest: async ({ action, file, onProgress }: { action: string; file: any; onProgress: Function }) => {
                    // 忽略 TypeScript 类型检查（临时解决方案）
                    // @ts-ignore
                    const data = new FormData();
                    
                    // 将文件添加到表单数据中
                    data.append("file", file);
                    
                    // 发送上传请求
                    return await request({
                        url: action,
                        method: "post",
                        timeout: 60000,  // 60秒超时
                        headers: {
                            "Content-Type": "multipart/form-data"
                        },
                        data,
                        // 上传进度监听
                        onUploadProgress: (p: any) => {
                            // 计算并回调上传进度百分比
                            onProgress({percent: Math.round((p.loaded / p.total) * 100)});
                        }
                    });
                },
                
                /**
                 * 上传成功后的数据处理函数
                 * @param ret 服务器返回的数据
                 * @returns Object 标准化的文件信息 {url, key, ...}
                 */
                successHandle(ret: any) {
                    return {
                        url: getBaseURL(ret.data.url),  // 完整的文件 URL
                        key: ret.data.id,               // 文件 ID
                        ...ret.data                     // 其他文件信息
                    };
                }
            },
            
            /**
             * 值构建器函数
             * 用于在显示时构建完整的文件 URL
             * @param context 上下文对象 {row, key}
             * @returns string 完整的文件 URL
             */
            valueBuilder(context: any){
                const { row, key } = context
                return getBaseURL(row[key])
            }
        })

        // 第五步：设置全局日志级别为错误级别
        setLogger({level: 'error'});
        
        // 第六步：配置字典组件的默认样式
        // 定义需要设置自动染色的字典组件列表
        const dictComponentList = ['dict-cascader', 'dict-checkbox', 'dict-radio', 'dict-select', 'dict-switch', 'dict-tree'];
        
        // 遍历设置每个字典组件的样式
        dictComponentList.forEach((val) => {
            // 设置自动染色
            getType(val).column.component.color = 'auto';
            // 设置列内容居中对齐
            getType(val).column.align = 'center';
        });
        
        // 第七步：设置输入组件的默认占位符和样式
        // 定义需要设置占位符的组件配置
        const placeholderComponentList = [
            {key: 'text', placeholder: "请输入"},      // 文本输入框
            {key: 'textarea', placeholder: "请输入"},  // 文本域
            {key: 'input', placeholder: "请输入"},     // 输入框
            {key: 'password', placeholder: "请输入"}   // 密码输入框
        ]
        
        // 遍历设置每个输入组件的占位符和样式
        placeholderComponentList.forEach((val) => {
            // 设置搜索表单的占位符
            if (getType(val.key)?.search?.component) {
                getType(val.key).search.component.placeholder = val.placeholder;
            } else if (getType(val.key)?.search) {
                getType(val.key).search.component = {placeholder: val.placeholder};
            }
            
            // 设置编辑表单的占位符
            if (getType(val.key)?.form?.component) {
                getType(val.key).form.component.placeholder = val.placeholder;
            } else if (getType(val.key)?.form) {
                getType(val.key).form.component = {placeholder: val.placeholder};
            }
            
            // 设置列显示的对齐方式为居中
            if (getType(val.key)?.column?.align) {
                getType(val.key).column.align = 'center'
            } else if (getType(val.key)?.column) {
                getType(val.key).column = {align: 'center'};
            } else if (getType(val.key)) {
                getType(val.key).column = {align: 'center'};
            }
        });
    },
};
