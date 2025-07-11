import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet } from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import { auth } from "/@/utils/authFunction";

//此处为crudOptions配置
// 这里使用了TypeScript的解构赋值语法和类型注解
// { crudExpose }: 这是ES6的解构赋值，从传入的参数对象中直接提取出crudExpose属性
// { crudExpose: CrudExpose }: 这是TypeScript的类型注解，定义了参数对象的结构
//   - 表示传入的参数是一个对象，这个对象必须包含一个名为crudExpose的属性
//   - 该属性的类型必须是CrudExpose类型
// 相当于传统写法：
// function (params: { crudExpose: CrudExpose }) {
//   const crudExpose = params.crudExpose;
// }
export default function ({ crudExpose }: { crudExpose: CrudExpose }): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
        return await api.GetList(query);
    };
    const editRequest = async ({ form, row }: EditReq) => {
        if (row.id) {
            form.id = row.id;
        }
        return await api.UpdateObj(form);
    };
    const delRequest = async ({ row }: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({ form }: AddReq) => {
        return await api.AddObj(form);
    };

    const exportRequest = async (query: UserPageQuery) => {
        return await api.exportData(query)
    };

    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            actionbar: {
                buttons: {
                    export: {
                        // 注释编号:django-vue3-admin-crud210716:注意这个auth里面的值，最好是使用index.vue文件里面的name值并加上请求动作的单词
                        show: auth('VIEWSETNAME:Export'),
                        text: "导出",//按钮文字
                        title: "导出",//鼠标停留显示的信息
                        click() {
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('VIEWSETNAME:Create'),
                    },
                }
            },
            rowHandle: {
                //固定右侧
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('VIEWSETNAME:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('VIEWSETNAME:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('VIEWSETNAME:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('VIEWSETNAME:Delete')
                    },
                },
            },
            columns: {
                // COLUMNS_CONFIG
            },
        },
    };
}