# OpenAI4S 科学展示前端

## 原始需求

为 GitHub 仓库 OpenAI4S 设计并实现用于宣传录屏的动态网页 demo。目标不是完整复现后端真实推理，而是通过高质量交互动画展示 OpenAI4S 作为 harness 如何借助 Qwen 或豆包等模型解决重要科学任务。

整体要求：浅色、简洁、现代、科学感；按 1920×1080 的 16:9 录屏优化；每部分为全屏 section；通过按钮推进页面；每个 section 内动画可自动播放；底部显示进度；整体不依赖不稳定外部接口；素材不足时使用可替换且视觉统一的占位内容。

技术建议：React + Vite + Tailwind CSS + Framer Motion；每个 section 为独立组件；添加启动说明。

页面结构：

1. 封面：OpenAI4S，突出“一个用于科学问题求解的 AI harness”，显示有机化学、生命科学、新材料，并以蛋白、DNA、分子结构、光谱线条作为浮动背景。
2. 有机化学总览：类药性优化、合成路径分析、混合物成分分析；默认高亮混合物成分分析。
3. 混合物成分分析：展示拉曼光谱，缩小嵌入输入框，逐字输入“请针对提供的未知混合物拉曼光谱开展一次盲测成分鉴定与解混分析”，展示 agent coding 和三个成分比例结果。
4. 生命科学总览：蛋白-分子靶点、蛋白定向突变；默认高亮蛋白-分子靶点。
5. 蛋白-分子靶点：展示蛋白口袋，缩小嵌入输入框，逐字输入“针对这一蛋白口袋形状，查找候选分子集合的合适分子”，展示 agent coding 和三个候选分子。
6. 结尾：强调 unified harness 能面向有机化学、生命科学、新材料进行 AI 驱动的问题求解；列出 natural language prompting、scientific entity grounding、agentic reasoning and coding、automated scientific analysis；显示 GitHub repo 名称和 URL。

动画：section 使用淡出淡入或从右向左；封面元素缓慢浮动；输入框为打字机效果；光谱和蛋白图有缩小嵌入输入框动画；code 界面分为 task description、code panel、execution log；结果简洁、可信、专业。

## 启动

```bash
cd /Users/lihao/Desktop/School-Work/Demo
npm install
npm run dev
```

可用右下角按钮或键盘左右方向键切换页面，`Space` 前进。

## 内容来源和可替换位置

- 矿物拉曼分析使用 `OpenAI4S/skills/mineral_spectra_analysis/examples/case1_analysis.json` 的盲分析摘要；`src/main.jsx` 的 `Spectrum` 可替换为真实光谱 PNG、SVG 或 CSV 绘图，`MineralResult` 可替换为新的 `case*_analysis.json` 输出。
- 蛋白演示按 `OpenAI4S/skills/protein-mutation-enhancement/SKILL.md` 的真实流程呈现：突变库、ESM 打分、ESMFold 结构评价和阈值排序。`ProteinVisual` 可替换为真实结构截图，`ProteinResult` 可替换为真实 `ranked_candidates.json`。
- 页面文案、任务卡片和仓库地址集中在 `src/main.jsx`；示意图均为页面内 SVG/CSS，可直接替换为真实素材。
