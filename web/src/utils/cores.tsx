// 这是ES6模块的混合导入语法
// mitt 是默认导出(default export)，可以直接导入并命名
// { Emitter } 是命名导出(named export)，需要用花括号解构导入
// 一个模块可以同时有默认导出和命名导出，所以可以在一条语句中同时导入两者
// 语法格式：import 默认导出名, { 命名导出1, 命名导出2 } from '模块路径';
import mitt, { Emitter } from 'mitt';

export interface TaskProps {
	name: string;
	custom?: any;
}

// 定义自定义事件类型
export type BusEvents = {
	onNewTask: TaskProps | undefined;
};

export interface Task {
	id: number;
	handle: string;
	data: any;
	createTime: Date;
	custom?: any;
}

export interface Core {
	bus: Emitter<BusEvents>;
	// eslint-disable-next-line no-unused-vars
	showNotification(body: string, title?: string): Notification | undefined;
	taskList: Map<String, Task>;
}

const bus = mitt<BusEvents>();
export function getSystemNotification(body: string, title?: string) {
	if (!title) {
		title = '通知';
	}
	return new Notification(title ?? '通知', {
		body: body,
	});
}
export function showSystemNotification(body: string, title?: string): Notification | undefined {
	if (Notification.permission === 'granted') {
		return getSystemNotification(body, title);
	} else if (Notification.permission !== 'denied') {
		Notification.requestPermission().then((permission) => {
			if (permission === 'granted') {
				return getSystemNotification(body, title);
			}
		});
	}
	return void 0;
}
const taskList = new Map<String, Task>();

export function useCore(): Core {
	return {
		bus,
		showNotification: showSystemNotification,
		taskList,
	};
}
