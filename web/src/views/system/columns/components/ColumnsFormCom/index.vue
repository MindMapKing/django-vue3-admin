<template>
	<div class="columns-form-com">
		<el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
			<el-form-item label="字段名" prop="field_name">
				<el-input v-model="formData.field_name" placeholder="请输入字段名" />
			</el-form-item>

			<el-form-item label="列名" prop="title">
				<el-input v-model="formData.title" placeholder="请输入列名" />
			</el-form-item>

			<el-form-item label="创建显示">
				<el-switch v-model="formData.is_create" />
			</el-form-item>

			<el-form-item label="编辑显示">
				<el-switch v-model="formData.is_update" />
			</el-form-item>

			<el-form-item label="查询显示">
				<el-switch v-model="formData.is_query" />
			</el-form-item>

			<el-form-item>
				<el-button type="primary" @click="handleSubmit" :loading="btnLoading"> 确定 </el-button>
				<el-button @click="handleClose">取消</el-button>
			</el-form-item>
		</el-form>
	</div>
</template>

<script lang="ts" setup>
// setup 是 Vue 3 Composition API 的语法糖
// 主要作用：
// 1. 简化组件定义：不需要显式返回响应式数据和方法，自动暴露给模板
// 2. 更好的 TypeScript 支持：提供更好的类型推断
// 3. 编译时优化：减少运行时开销，提高性能
// 4. 代码更简洁：避免了传统 setup() 函数中的 return 语句
// 5. 顶层绑定自动暴露：所有顶层变量、函数都可以在模板中直接使用
import { reactive, ref, onMounted } from 'vue';
import { addColumnsData, updateColumnsData } from '../ColumnsTableCom/api';
import { successNotification } from '/@/utils/message';
import { CurrentInfoType, ColumnsFormDataType } from '../../types';
import type { FormInstance } from 'element-plus';

// defineProps 是 Vue 3 Composition API 中用于声明组件 props 的函数
// 主要作用：
// 1. 类型声明：为 props 提供 TypeScript 类型支持，确保类型安全
// 2. 运行时验证：可以设置类型、默认值、验证规则等，Vue 会在开发模式下进行验证
// 3. 编译时优化：Vue 编译器会对 defineProps 进行静态分析和优化
// 4. 响应式代理：返回的 props 对象是响应式的，可以在模板和逻辑中直接使用
// 5. 父子组件通信：接收父组件传递的数据，实现组件间的数据流动
// 6. 只读特性：props 是只读的，不能在子组件中直接修改，保证数据流的单向性
const props = defineProps({
	currentInfo: {
		// 这句话的作用是为 Vue 组件的 prop 提供 TypeScript 类型断言
		// 主要功能：
		// 1. 类型声明：将 Object 类型强制转换为函数类型 () => CurrentInfoType
		// 2. 类型安全：确保传入的 currentInfo 对象符合 CurrentInfoType 接口定义
		// 3. 智能提示：在使用 props.currentInfo 时，IDE 能够提供准确的代码提示和类型检查
		// 4. 运行时保护：Vue 会验证传入的数据是否为对象类型
		// 5. 编译优化：帮助 Vue 编译器进行更好的类型推断和优化
		type: Object as () => CurrentInfoType,
		required: true,
		default: () => {},
	},
	initFormData: {
		type: Object as () => Partial<ColumnsFormDataType>,
		default: () => {},
	},
});
// defineEmits 是 Vue 3 Composition API 中用于声明组件自定义事件的函数
// 主要作用：
// 1. 事件声明：声明组件可以向父组件发出的自定义事件名称
// 2. 类型支持：为事件提供 TypeScript 类型支持，确保事件名称和参数类型正确
// 3. 编译时验证：Vue 编译器会验证事件的使用是否符合声明
// 4. 父子组件通信：实现子组件向父组件传递数据或触发操作的机制
// 5. 代码提示：IDE 能够提供准确的事件名称自动补全和参数提示
// 6. 运行时优化：帮助 Vue 进行更好的性能优化
// 这里声明了一个名为 'drawerClose' 的事件，用于通知父组件关闭抽屉或弹窗
const emit = defineEmits(['drawerClose']);

// ref 是 Vue 3 中创建响应式引用的函数，主要作用：
// 1. 基本类型响应式：将基本类型（string、number、boolean）包装成响应式对象
// 2. 对象引用：可以存储对象引用，通过 .value 访问实际值
// 3. 模板引用：用于获取 DOM 元素或组件实例的引用
// 4. 浅层响应式：只对 .value 属性进行响应式处理
// 
// ref 与 reactive 的区别：
// 1. 数据类型：ref 适用于基本类型和单一值，reactive 适用于对象和数组
// 2. 访问方式：ref 需要通过 .value 访问，reactive 可以直接访问属性
// 3. 响应式深度：ref 是浅层响应式，reactive 是深层响应式
// 4. 重新赋值：ref 可以重新赋值整个对象，reactive 不能重新赋值根对象
// 5. 模板使用：ref 在模板中自动解包，不需要 .value；reactive 直接使用
// 6. 性能：ref 开销更小，reactive 对深层对象有更好的响应式支持
//
// 这里使用 ref 是因为需要获取表单组件实例的引用，用于调用表单验证等方法
const formRef = ref<FormInstance>();
const formRules = reactive({
	field_name: [{ required: true, message: '请输入字段名！', trigger: 'blur' }],
	title: [{ required: true, message: '请输入列名！', trigger: 'blur' }],
});

let formData = reactive<ColumnsFormDataType>({
	field_name: '',
	title: '',
	is_create: true,
	is_update: true,
	is_query: true,
});
let btnLoading = ref(false);
// 双感叹号(!!)是JavaScript中的强制类型转换操作符，也叫"双重否定"操作符
// 主要作用是将任何值转换为对应的布尔值：
// 1. 第一个感叹号(!)：将值转换为布尔值并取反
// 2. 第二个感叹号(!)：再次取反，得到原值对应的布尔值
//
// 转换规则：
// - 假值(falsy)转换为 false：undefined、null、0、''、false、NaN
// - 真值(truthy)转换为 true：除假值外的所有值
//
// 使用场景：
// 1. API返回的数据可能是数字(0/1)、字符串('true'/'false')等，需要转换为布尔值
// 2. 确保数据类型一致性，避免在条件判断中出现意外结果
// 3. 组件props类型验证，确保传入的值是标准布尔值
//
// 例子：
// !!0 → false
// !!1 → true  
// !!'false' → true (注意：字符串'false'是真值)
// !!undefined → false
// !!{} → true (空对象是真值)
const setMenuFormData = () => {
	if (props.initFormData?.id) {
		formData.id = props.initFormData?.id || '';
		formData.field_name = props.initFormData.field_name || '';
		formData.title = props.initFormData.title || '';
		formData.is_create = !!props.initFormData.is_create;
		formData.is_update = !!props.initFormData.is_update;
		formData.is_query = !!props.initFormData.is_query;
	}
};

const handleSubmit = () => {
	formRef.value?.validate(async (valid) => {
		if (!valid) return;
		try {
			btnLoading.value = true;
			let res;
			if (formData.id) {
				res = await updateColumnsData({ ...formData, ...props.currentInfo });
			} else {
				res = await addColumnsData({ ...formData, ...props.currentInfo });
			}
			if (res?.code === 2000) {
				successNotification(res.msg as string);
				handleClose('submit');
			}
		} finally {
			btnLoading.value = false;
		}
	});
};

const handleClose = (type: string = '') => {
	emit('drawerClose', type);
	formRef.value?.resetFields();
};

onMounted(() => {
	setMenuFormData();
});
</script>

<style lang="scss" scoped>
.columns-form-com {
	height: 100%;
	padding: 20px;
	box-sizing: border-box;
}
</style>
