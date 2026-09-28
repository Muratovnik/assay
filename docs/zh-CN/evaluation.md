# 评测能证明什么

[English](../evaluation.md) · [Русский](../ru/evaluation.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

每个技能都有 `evals/` 目录；目录存在本身并不能证明技能改善了模型的工作。

## 评测目录里有什么

`cases.json`（或另行命名的集合）保存任务与上下文，`rubric.json` 单独保存评分标准。
部分技能还有用于启用边界的 `trigger-cases.json` 和说明运行方式的 `evaluation.md`。

`independent-audit` 采用自己的夹具布局，而非成对 JSON。`skill-evaluation` 现在
具有决策与发现用例、独立的评测者元数据和运行协议。原有 `research-and-transfer.md`
仍保留为需要准备来源材料的人工迁移场景规格；这些规格不是已执行的评测结果。

这些是评测者数据，不是执行者指令。技能执行任务时不得读取自己的评分标准、其他
用例或既往回答。获得答案键可能提高分数，却不代表行为得到改善。

## 校验检查了什么

`python tools/eval_assets.py check` 校验用例标识、评分条目对应关系、支持的夹具
输入路径，以及输入侧没有评分字段。它不运行模型，也不完成这些任务。

工具测试会实际执行，但不调用模型。`skills/independent-audit/evals/test_prepare_case.py`
检查冻结材料包的构建与摘要；`skills/technical-writing/evals/test_text_check.py`
检查文件区域比较、退出码与输入保全。`tools/test_eval_assets.py` 检查内联用例材料包、
元数据、无效输入拒绝以及评测者答案键不会进入材料包。

这些测试证明结构一致性及断言覆盖的具体工具行为，不证明任务的语义独立性、评分
标准的正确性、实际访问隔离或模型回答质量。

## 有意不去证明的事

CI 不运行模型。本仓库没有技能排行榜或百分比改进声明。此类结论需要获准的、针对
冻结基线的可比运行；结论属于所测任务、客户端、模型和日期，并不自动推广到所有场景。

静态文件也不能证明发现。安装位置符合文档，或模型声称已使用技能，都不够。
`tools/native_smoke.py` 检查捕获的客户端事件；对 Codex 返回 `unverified`，因为
尚无经验证的事件到技能启用映射。

适配器请求只读沙箱，也不证明具体会话遵守了限制；应验证实际生效的访问策略。

## 自行评测技能

使用现有工具准备只含输入的冻结材料包：

```text
python tools/eval_assets.py prepare --cases skills/<skill>/evals/cases.json --case <id> --output-parent <your evidence directory>
```

把返回的清单摘要保存在材料包之外，运行前后用
`skills/independent-audit/evals/verify_packet.py` 校验。与旧版本比较时，应使用
旧版本自身的冻结技能目录，而不是候选版本的另一份副本。

## 小规模配对比较

初步比较使用[配对流程](../../skills/skill-evaluation/references/paired-pilot.md)。
分别观察加载、决策、合法行为保留情况以及总成本。小规模诊断不能证明整个技能库
的质量或普遍节省。

## 仅供评测者使用的用例元数据

可选的 `case-metadata.json` 位于 `cases.json` 旁；辅助集合 `<prefix>-cases.json`
对应 `<prefix>-case-metadata.json`。没有元数据的旧文件对仍受支持。元数据包含
`schema_version: 1`、相同的 `skill_name`、完全相同的集合和用例 ID。每条记录的
字段必须是非空且无首尾空白的字符串：

| 字段 | 含义 |
| --- | --- |
| `id` | 集合内匹配的用例 ID。 |
| `group` | 相关事件、模板、项目或答案族。 |
| `purpose` | `routine`、`regression`、`challenge` 或 `should-not-fire`。 |
| `source` | 来源，明确标注合成示例。 |
| `rationale` | 纳入目标任务范围的理由。 |
| `split` | `working`、`selection` 或 `final`。 |
| `exposure` | `public`、`development` 或 `sealed`。 |

校验拒绝多余或缺失字段、未知分类、不匹配 ID、没有对应集合的元数据文件，以及同一
技能的主集合与辅助集合中已声明的关联组跨越不同划分。`final` 必须声明为 `sealed`。

这种声明不是访问控制：公开文件不会因改标签而保密。校验器不能发现未声明的语义
关联，也不能证明代表性。随附的所有 `skill-evaluation` 用例都是公开的工作材料，
不是秘密的最终测试集。

`prepare` 不读取或复制评分标准、元数据；输入字段仍仅限 `id`、`prompt`、`context`
和 `files`。这只是打包边界，不会阻止执行者从别处访问源仓库。源摘要标识输入，而非
测量版本；评分标准、评测者配置、元数据及暴露历史应另存于现有实验记录。

## 从配对试验到迭代改进

新建或实质修改任务集合、评测者时，使用
[评测设计](../../skills/skill-evaluation/references/eval-design.md)。它把标准与用户
需要的结果对应起来，校准错误接受与错误拒绝，并区分评测者和执行者的波动。仍适用的
校准可以复用，小改动不必启动新研究。

多个候选版本的比较采用
[有界迭代改进](../../skills/skill-evaluation/references/iterative-improvement.md)。
先固定目标、基线、获准修改范围、预算、硬性约束与停止规则。区分工作案例、候选选择
证据和未使用的最终组；反复查看汇总分数也会影响选择，不能算独立最终证据。极小试验
保持诊断性质，不应人为划成三个似乎严格的微型样本。

删除重复规则、缩小触发条件、移动指令和保留现有方法都是合法候选。应保留相邻合法
场景，并在实际启用的技能集合中检查自动选择。平台期需要因果诊断，而非加强措辞或
删掉不便的失败。修正评测者意味着新的测量版本：两种方法必须按相同的新标准比较，
旧证据仍须保留。

这些流程复用现有执行、检查和 Git 工具，不新增运行器、付费评测活动或自主改写服务。
已编写、结构已检查、模型行为已运行和比较证据已支持，是不同的证据状态。
