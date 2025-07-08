import {App} from "vue/dist/vue";

// WeakMap 是一种特殊的 Map 数据结构，具有以下特点：
// 1. 键只能是对象类型（不能是原始值）
// 2. 键是弱引用的，不会阻止垃圾回收
// 3. 当键对象被垃圾回收时，对应的键值对会自动从 WeakMap 中删除
// 4. 不可枚举，无法获取所有键或进行遍历
// 5. 适用于存储与 DOM 元素相关的私有数据，避免内存泄漏
const map = new WeakMap()
const ob = new ResizeObserver((entries) => {
    for(const  entry of entries){
        const handler = map.get(entry.target);
        handler && handler({
            width: entry.borderBoxSize[0].inlineSize,
            height: entry.borderBoxSize[0].blockSize
        });
    }
});
export function resizeObDirective(app: App){
    app.directive('resizeOb', {
        mounted(el,binding) {
            map.set(el,binding.value);
            ob.observe(el); // 监听目标元素
        },
        unmounted(el) {
            ob.unobserve(el); // 停止监听
        },
    })
}
