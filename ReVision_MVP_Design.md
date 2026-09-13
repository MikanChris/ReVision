# ReVision MVP 需求设计

> **项目目标：** 做一个小而完整的视觉反馈型 AI Agent。用户提供一张网页截图，ReVision 自动生成静态 HTML/CSS 页面，在真实浏览器中渲染并截图，然后基于视觉差异进行多轮修改，让结果逐步接近目标截图。

> **当前原则：** 先跑通完整闭环，再优化质量；先做静态视觉复刻，再考虑交互和多页面能力。

---

## 1. 项目定位

### 一句话 Pitch

**ReVision is a visual feedback agent that recreates a webpage from a screenshot, renders its own HTML/CSS in a real browser, and iteratively repairs visual mismatches.**

更直白地说：

> 给 ReVision 一张网页截图，它先照着生成一个静态网页，然后“看见”自己生成出来的浏览器截图，再根据差异修改代码，逐轮接近原图。

### MVP 要验证的问题

第一版只回答一个问题：

> **迭代式视觉反馈，是否能比一次性 screenshot-to-code 生成更接近目标网页截图？**

Baseline:

```text
target.png -> generate once -> rendered screenshot
```

ReVision:

```text
target.png
-> generate HTML/CSS
-> render in browser
-> screenshot
-> visual critique
-> repair HTML/CSS
-> repeat
-> final result
```

---

## 2. 已确认的产品决策

1. **第一版只做静态网页视觉复刻。**
   不复刻按钮点击、弹窗、表单提交、登录流程、页面状态切换等交互行为。

2. **第一版做命令行工具。**
   目标运行方式：

   ```bash
   python main.py --target workspace/target.png
   ```

3. **第一版使用 OpenAI API。**
   暂定通过 OpenAI Responses API 调用一个支持图片输入和代码生成的多模态模型。

   根据官方 OpenAI documentation，当前可选默认模型建议使用：

   ```text
   gpt-5.6-luna
   ```

   原因：官方模型页将它定位为复杂推理和编码的旗舰模型，并说明最新 OpenAI 模型支持文本和图片输入、文本输出、视觉能力，且可通过 Responses API 使用。

   第一版不做 multi-provider adapter，但模型调用必须隔离在一个小模块中，方便以后替换。

4. **截图中的图片资源先用占位色块。**
   对商品图、头像、插画、照片等内容，MVP 不追求真实图片复刻。优先复刻位置、尺寸、比例、圆角、背景色、布局关系。

5. **MVP 展示目标是一张图完整闭环。**
   第一阶段不追求 5-10 张 benchmark。先确保一张目标截图可以完整跑完：

   ```text
   generate -> render -> critique -> repair -> repeat
   ```

---

## 3. 输入与输出

### 输入

MVP 只接受一张目标截图：

```text
workspace/target.png
```

第一版参数可以写死：

```text
viewport = 1440x900
max_iterations = 3
```

后续再扩展为命令行参数：

```bash
python main.py --target workspace/target.png --iterations 3 --viewport 1440x900
```

### 输出

建议输出目录：

```text
output/
├── index.html
├── style.css
├── final.png
├── log.json
└── iterations/
    ├── iteration_0.png
    ├── iteration_0.html
    ├── iteration_0.css
    ├── iteration_0_critique.json
    ├── iteration_1.png
    ├── iteration_1.html
    ├── iteration_1.css
    └── iteration_1_critique.json
```

每一轮必须保存：

- iteration number
- rendered screenshot
- 当前 HTML
- 当前 CSS
- visual critique
- evaluation score，等 evaluator 加入后保存

---

## 4. MVP Scope

### 必须实现

- [ ] 读取 `target.png`
- [ ] 调用 OpenAI 多模态模型生成初版 HTML/CSS
- [ ] 写入 `output/index.html` 和 `output/style.css`
- [ ] 使用 Playwright 在固定 viewport 中渲染页面
- [ ] 自动截图并保存为 `iteration_0.png`
- [ ] 将目标截图和当前截图交给视觉模型生成结构化 critique
- [ ] 根据 critique 修改 HTML/CSS
- [ ] 重新渲染并截图
- [ ] 自动循环至少 3 轮
- [ ] 保存每轮截图、代码、critique、日志
- [ ] 生成最终 `final.png`
- [ ] 最终保留表现最好的一轮，而不是默认最后一轮
- [ ] 用户能清楚看到目标图、初版结果、修复后结果的变化

### 明确暂时不做

- React / Next.js
- 多页面网站
- 视频输入
- 真实交互行为复刻
- JavaScript 功能复刻
- Multi-Agent
- responsive design
- mobile / tablet / desktop 多 viewport
- Figma integration
- 浏览器自动探索
- DOM semantic matching
- 自己训练模型
- 大型 benchmark
- production deployment
- 用户账号系统
- 数据库
- 自动发布网站
- 复杂视觉指标体系
- 多供应商模型 adapter

如果一个功能不直接帮助完成下面链路，第一版就不加：

```text
target.png -> HTML/CSS -> render -> critique -> repair
```

---

## 5. 推荐技术栈

### Orchestration

**Python**

负责：

- 命令行入口
- 文件读写
- OpenAI API 调用
- Playwright 调用
- Agent loop
- 日志与状态管理

### Browser Automation

**Playwright**

负责：

- 打开本地 HTML
- 设置固定 viewport
- 等待页面稳定
- 截图

### Generated Frontend

第一版只生成：

```text
HTML + CSS
```

必要时允许极少量 JavaScript，但默认不需要。

### AI Model

第一版直接使用 OpenAI API，不做多模型抽象层。

但要把模型调用集中到一个小文件，例如：

```text
revision/model.py
```

建议接口：

```python
class OpenAIModel:
    def generate_page(self, target_image_path: str) -> GeneratedCode:
        ...

    def critique(self, target_image_path: str, current_image_path: str, code: GeneratedCode) -> Critique:
        ...

    def repair(self, code: GeneratedCode, critique: Critique) -> GeneratedCode:
        ...
```

这样以后如果要换模型供应商，只需要替换这个模块。

### Image Evaluation

MVP 初期可以先只做人工视觉观察。

后续最小 evaluator 可选：

- Pillow
- scikit-image SSIM
- 简单 pixel difference

指标只用于观察趋势，不直接等同于“视觉正确率”。

---

## 6. 分阶段开发

### Phase 0 - Hello Browser

目标：

```text
local index.html -> Playwright -> screenshot.png
```

完成标准：

运行：

```bash
python main.py
```

程序可以自动：

1. 打开本地 HTML
2. 设置 `1440x900` viewport
3. 截图
4. 保存文件

这是后续所有视觉反馈的基础环境。

### Phase 1 - Screenshot To Webpage

目标：

```text
target.png
-> OpenAI multimodal model
-> index.html + style.css
-> Playwright render
-> iteration_0.png
```

完成标准：

用户可以并排看到：

```text
Target screenshot vs Generated screenshot
```

做到这里，项目已经第一次跑起来。

### Phase 2 - Visual Critic

目标：

将下面两张图交给模型：

```text
target.png
iteration_0.png
```

输出结构化 critique：

```json
{
  "issues": [
    {
      "priority": 1,
      "area": "header",
      "problem": "Header is too tall compared with the target.",
      "suggestion": "Reduce top and bottom padding."
    }
  ]
}
```

完成标准：

肉眼检查 critique，大部分描述确实对应可见差异。

这一阶段只让模型说，不让模型改。

### Phase 3 - One-Shot Repair

目标：

```text
current code
-> critique
-> repair HTML/CSS
-> re-render
-> iteration_1.png
```

完成标准：

至少在一张测试截图上，能看到第二版发生合理变化。

不要求每次都改善。

### Phase 4 - Agent Loop

目标：

自动重复：

```text
Observe -> Critique -> Repair -> Render
```

默认 3 轮：

```text
iteration_0 -> iteration_1 -> iteration_2 -> iteration_3
```

完成标准：

整个过程不需要人工复制 prompt，不需要手动截图。

### Phase 5 - Simple Evaluation

目标：

开始记录 ReVision 是否真的改善。

第一版可以先保存分数位置，但允许 `score = null`。

后续再加入：

- SSIM
- simple image difference
- perceptual similarity

注意：如果指标和肉眼判断冲突，不要为了数字强行证明效果。

---

## 7. Agent Loop 设计

伪代码：

```python
target = load_image("workspace/target.png")

code = model.generate_page(target)
workspace.write_code(code)

best_result = None

for iteration in range(max_iterations + 1):
    screenshot = renderer.render_and_capture(code)

    score = evaluator.compare(target, screenshot)

    result = workspace.save_iteration(
        iteration=iteration,
        screenshot=screenshot,
        code=code,
        score=score,
    )

    if best_result is None or is_better(result, best_result):
        best_result = result

    if iteration == max_iterations:
        break

    critique = model.critique(
        target_image=target,
        current_image=screenshot,
        current_code=code,
    )

    workspace.save_critique(iteration, critique)

    code = model.repair(
        current_code=code,
        critique=critique,
    )

workspace.restore_best(best_result)
```

MVP 早期如果没有 evaluator，可以先用最后一轮作为 `final.png`，但文档和代码结构要为 best iteration 留位置。

---

## 8. 建议目录结构

```text
revision/
├── README.md
├── requirements.txt
├── .env.example
├── main.py
├── revision/
│   ├── agent.py
│   ├── model.py
│   ├── renderer.py
│   ├── workspace.py
│   └── prompts.py
├── workspace/
│   └── target.png
├── output/
│   └── iterations/
└── tests/
    ├── test_renderer.py
    └── test_workspace.py
```

不要为了“工程化”提前拆太多模块。第一版保持可读、可跑、可解释。

---

## 9. Prompt 目标

### Generate Prompt

目标：

- 根据截图生成静态 HTML/CSS
- 复刻布局、颜色、字体层级、间距、圆角、阴影
- 图片区域使用占位色块
- 不引入外部框架
- 不生成 React
- 不实现交互行为

### Critique Prompt

目标：

- 找最明显的 Top 3 差异
- 按影响程度排序
- 指出具体区域
- 给出可执行修改建议
- 避免模糊评价
- 不要求一次修完所有问题

### Repair Prompt

目标：

- 只根据 critique 修改 HTML/CSS
- 尽量小范围修改
- 不重写整个页面，除非当前代码明显不可修
- 保留已经接近目标的区域
- 输出完整可运行的 HTML/CSS

---

## 10. MVP Definition of Done

ReVision MVP 完成条件：

1. 用户放入 `workspace/target.png`
2. 运行一个命令启动流程
3. ReVision 自动生成 `index.html` 和 `style.css`
4. Playwright 自动渲染并截图
5. OpenAI 视觉模型比较 Target 和 Current
6. Agent 根据 critique 修改 HTML/CSS
7. 自动重复至少 3 轮
8. 每轮结果被保存
9. 最终生成 `final.png`
10. 用户可以清楚看到页面在迭代过程中发生变化

如果这些全部完成：

> **MVP Done.**

---

## 11. 后续扩展方向

MVP 完成之前暂不实现。

可根据真实失败模式选择：

- Regression-aware repair
- Element-level critique
- Responsive repair
- Behavioral verification
- Cost-aware iteration
- 多截图 benchmark
- README demo GIF
- 简历 bullet 和项目包装

---

## 12. README 展示建议

README 顶部先展示结果，不要先讲技术栈。

建议结构：

```text
# ReVision

A visual feedback agent that sees what it builds.

Target -> One-shot -> ReVision Iteration 3
[image]   [image]     [image]
```

然后再说明：

> Unlike one-shot screenshot-to-code generation, ReVision renders its own output in a real browser, visually compares the result against the reference, and iteratively repairs the generated HTML/CSS.

最后再讲：

- architecture
- setup
- usage
- examples
- evaluation
- limitations

---

## 13. 当前下一步

用户确认本需求文档后，进入实现阶段。

建议从 Phase 0 开始：

```text
local HTML -> Playwright -> screenshot
```

先把浏览器渲染和截图环境跑通，再接 OpenAI API。
