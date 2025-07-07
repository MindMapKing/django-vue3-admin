/**
 * 判断两数组字符串是否相同（用于按钮权限验证），数组字符串中存在相同时会自动去重（按钮权限标识不会重复）
 * @param news 新数据
 * @param old 源数据
 * @returns 两数组相同返回 `true`，反之则反
 */
export function judementSameArr(newArr: unknown[] | string[], oldArr: string[]): boolean {
	const news = removeDuplicate(newArr);
	const olds = removeDuplicate(oldArr);
	let count = 0;
	const leng = news.length;
	for (let i in olds) {
		for (let j in news) {
			if (olds[i] === news[j]) count++;
		}
	}
	return count === leng ? true : false;
}

/**
 * 判断两个对象是否相同
 * @param a 要比较的对象一
 * @param b 要比较的对象二
 * @returns 相同返回 true，反之则反
 */
export function isObjectValueEqual<T>(a: T, b: T): boolean {
	if (!a || !b) return false;
	let aProps = Object.getOwnPropertyNames(a);
	let bProps = Object.getOwnPropertyNames(b);
	if (aProps.length != bProps.length) return false;
	for (let i = 0; i < aProps.length; i++) {
		let propName = aProps[i];
		let propA = a[propName];
		let propB = b[propName];
		if (!b.hasOwnProperty(propName)) return false;
		if (propA instanceof Object) {
			if (!isObjectValueEqual(propA, propB)) return false;
		} else if (propA !== propB) {
			return false;
		}
	}
	return true;
}

/**
 * 数组、数组对象去重
 * @param arr 数组内容
 * @param attr 需要去重的键值（数组对象）
 * @returns
 */
export function removeDuplicate(arr: EmptyArrayType, attr?: string) {
	// 检查数组是否为空，如果为空则直接返回原数组
	// Object.keys()` 是一个 JavaScript 内置方法，用于获取对象自身可枚举属性的键名数组。
	// 在这个上下文中，它被用来检查数组是否为空，但这种方式存在问题。
	if (!Object.keys(arr).length) {
		return arr;
	} else {
		// 判断是否需要根据指定属性去重（数组对象去重）
		if (attr) {
			// 创建一个空对象用于记录已出现的属性值
			const obj: EmptyObjectType = {};
			// 使用 reduce 方法遍历数组，进行去重操作
			return arr.reduce((cur: EmptyArrayType[], item: EmptyArrayType) => {
				// 检查当前项的指定属性值是否已存在：
				// - 如果已存在则跳过（返回空字符串）
				// - 如果不存在则标记为已存在，并将当前项添加到结果数组中
				obj[item[attr]] ? '' : (obj[item[attr]] = true && item[attr] && cur.push(item));
				// 返回累积的结果数组
				return cur;
			}, []); // 初始值为空数组
		} else {
			// 对于普通数组，使用 Set 数据结构自动去重，然后展开为新数组
			return [...new Set(arr)];
		}
	}
}
