import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Session } from '/@/utils/storage';
import qs from 'qs';

// 配置新建一个 axios 实例
// 配置新建一个 axios 实例
// allowDots: true 允许在查询参数中使用点号(.)来表示嵌套对象
// 例如: { user: { name: 'John', age: 25 } } 会被序列化为 "user.name=John&user.age=25"
// 而不是默认的 "user[name]=John&user[age]=25" 格式
const service: AxiosInstance = axios.create({
	baseURL: import.meta.env.VITE_API_URL,
	timeout: 50000,
	headers: { 'Content-Type': 'application/json' },
	paramsSerializer: {
		serialize(params) {
			return qs.stringify(params, { allowDots: true });
		},
	},
});

// 添加请求拦截器
service.interceptors.request.use(
	(config: AxiosRequestConfig) => {
		// 在发送请求之前做些什么 token
		if (Session.get('token')) {
			// config.headers! 中的感叹号(!)是TypeScript的非空断言操作符
			// 它告诉TypeScript编译器：我确定config.headers不是null或undefined
			// 即使TypeScript认为它可能是undefined，我们强制告诉它这里一定有值
			// 这样可以避免TypeScript的类型检查错误
			// 
			// 这行代码的作用是：
			// 1. 获取config对象的headers属性
			// 2. 使用!断言headers不为空
			// 3. 在headers中设置Authorization字段
			// 4. 值为从Session中获取的token
			config.headers!['Authorization'] = `${Session.get('token')}`;
		}
		return config;
	},
	(error) => {
		// 对请求错误做些什么
		return Promise.reject(error);
	}
);

// 添加响应拦截器
service.interceptors.response.use(
	(response) => {
		// 对响应数据做点什么
		const res = response.data;
		if (res.code && res.code !== 0) {
			// `token` 过期或者账号已在别处登录
			if (res.code === 401 || res.code === 4001) {
				Session.clear(); // 清除浏览器全部临时缓存
				window.location.href = '/'; // 去登录页
				ElMessageBox.alert('你已被登出，请重新登录', '提示', {})
					.then(() => {})
					.catch(() => {});
			}
			return Promise.reject(service.interceptors.response);
		} else {
			return response.data;
		}
	},
	(error) => {
		// 对响应错误做点什么
		if (error.message.indexOf('timeout') != -1) {
			ElMessage.error('网络超时');
		} else if (error.message == 'Network Error') {
			ElMessage.error('网络连接错误');
		} else {
			if (error.response.data) ElMessage.error(error.response.statusText);
			else ElMessage.error('接口路径找不到');
		}
		return Promise.reject(error);
	}
);

// 导出 axios 实例
export default service;
