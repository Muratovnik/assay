# assay

面向编码智能体的可复用方法：八项技能与两个智能体配置，适用于 Claude Code、Codex、
Cursor 与 Gemini CLI。

[English](README.md) · [Русский](README.ru.md) · **简体中文**

[![checks](https://img.shields.io/github/actions/workflow/status/Muratovnik/assay/check.yml?branch=main&label=checks)](https://github.com/Muratovnik/assay/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/Muratovnik/assay)](https://github.com/Muratovnik/assay/releases)
[![license](https://img.shields.io/github/license/Muratovnik/assay)](LICENSE)

```text
/plugin marketplace add Muratovnik/assay
/plugin install assay@assay
```

assay 意为化验：检验某物究竟由什么构成。这些方法有共同的取向——说明检查了什么、
由此能得出什么结论，以及不能得出什么结论。

> [!NOTE]
> 技能是给智能体的指令，其中一些还附带智能体可以运行的脚本。无论来自本仓库还是
> 其他任何仓库，安装前请先阅读其内容。

英文版本为准。译文覆盖安装与内容说明；命令输出、规则名称与配置键不作翻译。

## 安装

| 客户端 | 命令 | 是否实测 |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay`，然后 `/plugin install assay@assay` | 已实测 |
| 任意受支持的智能体 | `npx skills add Muratovnik/assay` | 已实测 |
| Codex | `codex plugin marketplace add Muratovnik/assay`，然后从 `/plugins` 安装 | 依据文档 |
| Cursor | `npx skills add Muratovnik/assay -a cursor` | 依据文档 |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` | 依据文档 |

**已实测**指该安装路径已针对本已发布仓库实际执行，并对安装后的文件逐字节比对。
**依据文档**指该路径遵循客户端自身的文档，但未在此处运行过。安装后请新开一个
会话：客户端在启动时读取各自的技能目录。

技能 CLI 按其自述支持 Claude Code、Codex、Cursor、OpenCode「以及另外 75 个」。
对 Codex 而言，它的全局安装会写入 `~/.codex/skills/`，而该路径并未出现在当前
Codex 文档所列的技能根目录中：请改为安装到项目中，或使用下方的安装器。

各客户端的细节、卸载与升级说明见
[安装指南](docs/zh-CN/install.md)。

<details>
<summary><b>符号链接安装器</b> —— 获取智能体配置，并让改动即时生效</summary>

插件路径只安装技能。两个智能体配置，以及让你对检出目录的改动无需重装即可生效的
用法，来自仓库自带的安装器：

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` 不写入任何内容。它会打印将要创建的每个目标，以及每个目标对应的精确回滚
目标。随后 `install-links` 会把 `~/.agents/skills/<名称>` 链接到该检出目录并渲染
配置适配器，且会先对整个计划做预检：真实目录、外来链接或被修改过的适配器都会在
第一次写入之前中止本次运行。

在 Windows 上创建目录符号链接需要相应权限，通常是开发者模式或提升权限的终端。
缺少该权限时安装器直接失败，而不会退回到调用 shell。

</details>

## 内容一览

当任务与技能的描述相符时，技能会自行启用。下表每一行都链接到智能体实际会读取的
指令。

| 技能 | 适用场景 | 不适用场景 |
| --- | --- | --- |
| [code-maintenance](skills/code-maintenance/SKILL.md) | 改动涉及代码结构、共享逻辑或工具链 | 只改文字，或任务是只读审计 |
| [test-writing](skills/test-writing/SKILL.md) | 需要依据契约编写或修复测试 | 只需运行既有测试集，或讲解测试方法 |
| [test-audit](skills/test-audit/SKILL.md) | 有人声称某测试集能防止回归 | 你在编写测试，或只是执行它们 |
| [independent-audit](skills/independent-audit/SKILL.md) | 需要对照原始要求核查改动、发布或迁移 | 你想要的是把改动做完；此方法不做修复 |
| [evidence-research](skills/evidence-research/SKILL.md) | 重要结论需要定位并核对来源 | 答案只需一次查询即可得到 |
| [operations-ui-delivery](skills/operations-ui-delivery/SKILL.md) | 需要设计、修复或评审运维界面 | 工作仅涉及后端 |
| [route-subagents](skills/route-subagents/SKILL.md) | 已获授权的委派需要设定边界 | 无人授权委派；并行本身不构成许可 |
| [skill-design](skills/skill-design/SKILL.md) | 某个技能触发错位，或需要评估一个方法 | 只是修改元数据或撰写常规内容 |

两个智能体配置提供的是能力边界，而非人设。`evidence-reviewer` 通过只读的取证
手段审查冻结的材料包并给出结论；`official-docs-researcher` 依据一手文档回答一个
有界限的问题。二者都不绑定模型。

细节位于下一层。`SKILL.md` 保持简短，只在任务需要深入时才引导至 `references/`，
因此未被使用的方法几乎不占用上下文。

## 环境要求

技能本身是 Markdown，无需安装任何东西。Python 3.11 及以上版本与
`requirements-tools.txt` 中固定的 YAML 解析器，仅用于仓库自身的工具与校验。

`route-subagents` 可选择性地在选择模型时参考基准测试证据，方式是
`skills/route-subagents/scripts/` 中的本地 MCP 服务。它需要你自行注册，属于可选
项，没有它技能同样可用。

## 信任与安全

这里的脚本只接受显式路径，不会擅自向你的环境安装任何东西——但这是一项值得你自行
验证的声明，而不是应当直接采信的说法。

没有任何数据外传：没有遥测、没有账号，也没有网络调用，唯一的例外是需要你自行
注册的可选基准测试服务。

这些方法会读取仓库、文档，其中的研究方法还会读取网页。这类内容是数据而非指令，
方法本身也如此声明，但任何声明都不构成保证。当智能体读取过你无法控制的内容后，
请复核它提出的方案。安全问题请通过 [SECURITY.md](SECURITY.md) 私下报告。

## 校验方式

`python tools/check.py --all` 会运行全部校验：源码结构、单元测试集、兼容性夹具、
生成的清单、评测数据、渲染出的客户端清单，以及审计材料包测试集。持续集成在
Linux 与 Windows 上运行同一条命令，另外还会运行发布审计与 Claude 插件清单校验器。

持续集成中不运行任何模型，本仓库的技能也不带任何评分。`evals/` 目录能够以及
不能够证明什么，写在
[docs/evaluation.md](docs/evaluation.md)（英文）中。

## 参与贡献

欢迎提交 issue 与 pull request，回复以尽力而为为准。编写约定，包括明确列出校验
不会检查哪些方面，见 [AGENTS.md](AGENTS.md)；工作流程见
[CONTRIBUTING.md](CONTRIBUTING.md)。

[assay 的组成方式](docs/architecture.md) 说明了清单、发现拓扑与受保护的安装生命
周期。

## 许可证

MIT，见 [LICENSE](LICENSE)。
