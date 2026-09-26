# assay 的组成方式

路由建议器是现有 `route-subagents` MCP/CLI 的组成部分。它复用原有基准数据，
构建有大小限制的快照，经 `native-economy` 或单独启用的 Jev 获取排序后应用策略。
目录和智能体配置不绑定固定的低成本模型。客户端负责权限、启动及实际配额；
Assay 负责契约、本地元数据和诊断重放，不引入新守护进程或强制付费评测。
详见 [RoutingAdvisor](../../skills/route-subagents/references/routing-advisor.md)。

[English](../architecture.md) · [Русский](../ru/architecture.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

每个技能是 `skills/` 下的一个目录，每个智能体配置是 `profiles/` 下的一个 JSON
文件，`catalog.toml` 则是完整清单。没有任何内容按客户端重复存放：安装器把这一份
源链接或渲染到各客户端实际读取的位置。

## 清单

下表的列标题不作翻译：该区块由 `catalog.toml` 生成，三种语言版本都受同一道校验
约束。

<!-- assay:catalog:start -->

<!-- Generated from catalog.toml by tools/catalog_docs.py; do not edit this block. -->
| Asset | Activation | Codex target | Claude target |
| --- | --- | --- | --- |
| `skill/route-subagents` | automatic | `~/.agents/skills/route-subagents` | `~/.claude/skills/route-subagents` |
| `skill/ui-delivery` | automatic | `~/.agents/skills/ui-delivery` | `~/.claude/skills/ui-delivery` |
| `skill/independent-audit` | automatic | `~/.agents/skills/independent-audit` | `~/.claude/skills/independent-audit` |
| `skill/skill-evaluation` | automatic | `~/.agents/skills/skill-evaluation` | `~/.claude/skills/skill-evaluation` |
| `skill/evidence-research` | automatic | `~/.agents/skills/evidence-research` | `~/.claude/skills/evidence-research` |
| `skill/test-writing` | automatic | `~/.agents/skills/test-writing` | `~/.claude/skills/test-writing` |
| `skill/test-audit` | automatic | `~/.agents/skills/test-audit` | `~/.claude/skills/test-audit` |
| `skill/software-architecture` | automatic | `~/.agents/skills/software-architecture` | `~/.claude/skills/software-architecture` |
| `skill/code-change` | automatic | `~/.agents/skills/code-change` | `~/.claude/skills/code-change` |
| `skill/implementation-planning` | automatic | `~/.agents/skills/implementation-planning` | `~/.claude/skills/implementation-planning` |
| `skill/technical-writing` | automatic | `~/.agents/skills/technical-writing` | `~/.claude/skills/technical-writing` |
| `skill/text-writing` | automatic | `~/.agents/skills/text-writing` | `~/.claude/skills/text-writing` |
| `profile/evidence-reviewer` | explicit | `~/.codex/agents/evidence-reviewer.toml` | `~/.claude/agents/evidence-reviewer.md` |
| `profile/official-docs-researcher` | explicit | `~/.codex/agents/official-docs-researcher.toml` | `~/.claude/agents/official-docs-researcher.md` |

<!-- assay:catalog:end -->

`catalog.toml` 记录归属、启用方式与确切的安装目标，不包含模型、投入档位、运行时
状态、软件包清单或任何本机路径。`VERSION` 标记源契约；安装器与客户端清单读取它，
而不是各自重复一份。

## 发现拓扑

技能安装一次，可从两处到达。原生技能根目录保存指向清单化源的链接，Claude 链接到
同一个原生入口，而不是第二份副本：

```text
~/.agents/skills/<name> -> <checkout>/skills/<name>
~/.claude/skills/<name> -> ~/.agents/skills/<name>
```

不存在指向 `~/.codex/skills` 的投射。Codex 读取项目中的 `.agents/skills`，以及
用户账号下的 `~/.agents/skills`，其 `.system` 目录归客户端所有。智能体配置在
不同客户端需要不同的文件格式，因此采用渲染而非链接；目标位置见上方清单。

本节说明布局是什么样的。
[为什么一份源能到达多个客户端](explanation/discovery-topology.md)
说明它为何如此安排——`~/.agents/skills` 是多个客户端都会读取的目录，而非某一个
客户端的私有目录——以及每项选择的代价。

技能自动启用并不等于获得委派或修改任何东西的许可。委派只有一层：只有主智能体
派生执行者，执行者不再创建下一个。这条策略由 `route-subagents` 统一持有，其他
技能不再重复。

配置是能力边界，而不是绑定了模型的角色。Codex 适配器请求只读沙箱，Claude 适配器
使用 plan 模式与按能力推导出的工具列表。只有 `evidence-reviewer` 获得 `Bash`，
因为它声明的取证手段必须可执行，而它的指令依然禁止任何修改性命令。适配器请求的
沙箱属于配置：请核实会话实际生效的策略，而不要假定父进程原样保留了它。

## 受保护的生命周期

`python tools/assay.py plan` 是只读的。对每个清单化目标，它报告预期的链接目标或
适配器哈希、当前状态以及确切的回滚目标。`install-links` 会先预检整个计划，只接受
缺失的目标或完全一致的既有投射：真实目录、外来链接、被修改的适配器，或作为重解析
点的上级目录，都会在第一次写入之前中止整次运行。

创建是幂等的。若写入失败，只会移除本次调用创建的条目，且在移除前重新核对其身份。
`uninstall-links` 以同样方式预检，只移除完全一致的链接或适配器字节：目标缺失无害，
而人为改动会被保留并报告，而不是被覆盖。

在 Windows 上使用系统原生的目录符号链接 API，进程缺少该权限时直接失败。这里没有
任何退回 shell 的路径，也就不存在把路径重新解释为语法的可能。

该生命周期没有归档、没有软件包哈希、没有安装状态数据库、没有变更锁也没有日志。
它的依据是当前的清单与源版本——正因如此，旧版本安装的适配器必须由该版本移除，
新版本才能安装自己的那一份。

## 升级与回滚

升级涉及两个版本：先在创建了当前适配器的版本上运行 `uninstall-links`，再在新版本
上运行 `install-links`。在实际安装或移除之前，把受影响的源字节与观察到的目标向量
保存到受管目录之外，其中包括已有的人为改动，并保留该快照，直到两个客户端都验证
过为止。

回滚从该快照恢复确切记录的目标。它绝不会把旧的源与新的注册混在一起，也会保留无关
的人为改动，而不是为了让预检通过而将其抹平。安装目录旁边的状态文件不是它的备份。

[升级符号链接安装](how-to/upgrade-linked-install.md)把同一套顺序写成了操作步骤，
第一步是保存快照，最后一步是恢复。

## 校验

```text
python -B tools/check.py --all
```

这一条命令运行全部校验并逐项报告，而不是在第一个失败处停下：源码结构、`tools/`
单元测试集、兼容性夹具、生成的清单文档、评测数据、渲染出的客户端文件、审计材料包
测试集，以及保全性夹具。`make check` 是同一条命令，并会创建审计材料包测试集所需的
临时目录。要单独运行某一项校验，清单在 `tools/check.py` 中。

它们能证明源码结构、计划的确定性、受保护安装与卸载的语义，以及适配器的能力。
它们无法证明某个客户端确实发现了技能，也无法证明沙箱确实生效：那需要在全新客户端
中的一次实际运行，而这样一次运行能证明与不能证明什么，写在[评测说明](evaluation.md)里。
