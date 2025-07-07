<template>
	<fs-page>
		<fs-crud ref="crudRef" v-bind="crudBinding"> </fs-crud>
		<PermissionDrawerCom />
		<RoleUser ref="RoleUserRef" />
	</fs-page>
</template>

<script lang="ts" setup name="role">
import { defineAsyncComponent, onMounted, ref} from 'vue';
import { useFs } from '@fast-crud/fast-crud';
import { createCrudOptions } from './crud';
import { RoleDrawerStores } from './stores/RoleDrawerStores';
import { RoleMenuBtnStores } from './stores/RoleMenuBtnStores';
import { RoleMenuFieldStores } from './stores/RoleMenuFieldStores';
import { RoleUsersStores } from './stores/RoleUsersStores';
import { RoleUserStores } from './stores/RoleUserStores';

const RoleUser = defineAsyncComponent(() => import('./components/searchUsers/index.vue'));
const RoleUserRef = ref();

const PermissionDrawerCom = defineAsyncComponent(() => import('./components/RoleDrawer.vue'));

const RoleDrawer = RoleDrawerStores(); // 角色-抽屉
const RoleMenuBtn = RoleMenuBtnStores(); // 角色-菜单
const RoleMenuField = RoleMenuFieldStores();// 角色-菜单-字段
const RoleUsers = RoleUsersStores();// 角色-用户
const RoleUserDrawer = RoleUserStores(); // 授权用户抽屉参数

// useFs是fast-crud的核心钩子函数，用于创建CRUD操作的完整生态系统
// 它返回三个核心对象：
// - crudBinding: 包含所有CRUD组件需要的绑定属性和配置
// - crudRef: 对CRUD组件的引用，用于直接操作组件
// - crudExpose: 暴露的CRUD操作方法，如增删改查、刷新等

// 其他相关钩子函数的作用：
// - useCrud: 基础的CRUD钩子，提供基本的增删改查功能
// - useFsAsync: 异步版本的useFs，用于处理异步数据加载和操作
// - usePage: 处理分页相关的逻辑
// - useUi: 处理UI相关的配置和交互

const { crudBinding, crudRef, crudExpose } = useFs({
	createCrudOptions, // CRUD配置选项的创建函数
	context: { RoleDrawer, RoleMenuBtn, RoleMenuField, RoleUserDrawer, RoleUserRef }, // 上下文对象，传递给CRUD配置
});

// 页面打开后获取列表数据
onMounted(async () => {
	// 刷新
	crudExpose.doRefresh();
	// 获取全部用户
	RoleUsers.get_all_users();

});
</script>
