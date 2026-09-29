# 评测能证明什么

[English](../evaluation.md) · [Русский](../ru/evaluation.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

每个技能都带有一个 `evals/` 目录。有必要说清楚这些文件到底能证明什么，因为诚实的
答案比「这个技能有效」要窄得多。

## 评测目录里有什么

评测数据是把输入与评分标准分开存放的：`cases.json`（或另行命名的用例集合）保存
任务提示及其上下文，`rubric.json` 保存一个好的回答必须包含与不得包含的内容。部分
技能还有 `trigger-cases.json`，用于「这个技能是否应当启用」这个单独的问题；
`evaluation.md` 则说明一次运行如何设置。

`independent-audit` 把用例放在自己的夹具布局中，而不是成对的 JSON 文件里。
`skill-evaluation` 现在有成对的决策用例与发现用例、单独的仅供评测者使用的元数据
和运行协议。它的人工 `research-and-transfer.md` 规格仍然保留，用于有来源依据的迁移
场景；这些规格不是已执行的结果。

它们是评测数据，不是运行时指令。技能自身的文本也这样写明：在执行用户任务时，技能
不得读取自己的用例与评分标准。读评分标准，正是一个方法开始拿高分却并没有变好的
方式。

## 校验检查了什么

`python tools/eval_assets.py check` 校验结构：每个声明的用例都有 id，每条评分标准
都指向确实存在的用例，每个被引用的输入路径都能解析，且没有任何用例把评分字段夹带
到输入一侧。它不执行夹具，也不运行模型。

工具测试集确实会执行，且都不运行模型。审计材料包测试集
（`skills/independent-audit/evals/test_prepare_case.py`）构建只含输入的冻结材料包，
并验证准备过程排除了评分标准、其他用例与既往回答，且材料包清单的摘要与实际写入的
内容一致。保全性测试集（`skills/technical-writing/evals/test_text_check.py`）以夹具
文件对运行该技能随附的 `text_check.py`，并按其文档约定核对：每种模式比较哪些区域、
每种结果给出哪个退出码，以及该检查不会改动两个输入文件。

`tools/test_eval_assets.py` 还会检查内联材料包的准备与元数据校验，包括拒绝无效输入
以及排除评测者答案键。这些检查确立的是结构一致性，以及测试所断言的具体工具行为；
它们不能确立用例的语义独立性、评分预期的正确性、实际生效的访问隔离或回答质量。

## 有意不去证明的事

持续集成中不运行任何模型。本仓库没有评分、没有排行榜，也不声称某个技能能把结果
提升多少个百分点。要测量那些，需要针对冻结基线、经授权的可比运行，而结果只属于测量当时的
客户端、模型与日期，而不属于技能本身。

静态文件同样无法证明「已被发现」。技能被装到客户端文档所述的技能根目录，并不证明
客户端加载了它；模型声称自己用了某个技能，也不是它确实用了的证据。
`tools/native_smoke.py` 正是为这个缺口而存在：它检查一次已记录的客户端运行，报告
加载器事件是否真的发生过。它的结论有意收窄，对 Codex 则返回 `unverified`，因为从
它的事件到技能启用之间不存在够格的映射。

对沙箱也要同样谨慎。智能体配置的适配器请求只读沙箱；会话是否遵守了它，是那次运行
的属性，而不是文件的属性。请核实实际生效的策略，而不是读适配器了事。

## 如果你想自己评测某个技能

使用冻结材料包的准备工具，让被测方法只看到输入：

```text
python tools/eval_assets.py prepare --cases skills/<skill>/evals/cases.json --case <id> --output-parent <your evidence directory>
```

把返回的清单摘要保存到材料包之外，然后在运行前后用
`skills/independent-audit/evals/verify_packet.py` 校验该材料包。把一个方法与基线
比较，意味着使用基线自身版本中的冻结目录，而不是今天这份技能副本。

## 小规模配对比较

方法修改的初步比较使用现有[配对流程](../../skills/skill-evaluation/references/paired-pilot.md)。
分别观察加载、决策、合法行为是否保留以及总成本。小规模诊断不等于整个技能库的
评分，也不能证明普遍节省。

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

新建或实质修改用例集合或评测者时，使用
[评测设计](../../skills/skill-evaluation/references/eval-design.md)。当请求需要多个
候选修改时，使用
[有界迭代改进](../../skills/skill-evaluation/references/iterative-improvement.md)。
两者都不新增运行器、模型评测活动或发布结果的要求。
