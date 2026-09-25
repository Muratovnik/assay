# assay

面向编码智能体的可复用方法：技能与智能体配置，适用于 Claude Code、Codex、Cursor
与 Gemini CLI。assay 意为化验：检验某物究竟由什么构成。这些方法取向一致——说明
检查了什么、由此能得出什么结论，以及不能得出什么结论。

[English](README.md) · [Русский](README.ru.md) · **简体中文**

[![checks](https://img.shields.io/github/actions/workflow/status/Muratovnik/assay/check.yml?branch=main&label=checks&style=flat-square)](https://github.com/Muratovnik/assay/actions/workflows/check.yml)
[![release](https://img.shields.io/github/v/release/Muratovnik/assay?style=flat-square)](https://github.com/Muratovnik/assay/releases)
[![license](https://img.shields.io/github/license/Muratovnik/assay?style=flat-square)](LICENSE)

英文版本为准。译文覆盖安装与内容说明；命令输出、规则名称与配置键不作翻译。

## 能做什么

当任务与技能的描述相符时，技能会自行启用。下表每一行都链接到智能体实际会读取的
指令。

| 技能 | 适用场景 | 不适用场景 |
| --- | --- | --- |
| [code-maintenance](skills/code-maintenance/SKILL.md) | 改动涉及代码结构、共享逻辑或工具链 | 只改文字，或任务是只读审计 |
| [implementation-planning](skills/implementation-planning/SKILL.md) | 需要为一次改动乃至分阶段路线图制定计划，或修订已有计划 | 只是在讨论想法、仅需调研，或改动显而易见 |
| [test-writing](skills/test-writing/SKILL.md) | 需要依据契约编写或修复测试 | 只需运行既有测试集，或讲解测试方法 |
| [test-audit](skills/test-audit/SKILL.md) | 有人声称某测试集能防止回归 | 你在编写测试，或只是执行它们 |
| [independent-audit](skills/independent-audit/SKILL.md) | 需要对照原始要求核查计划、改动、发布或迁移 | 你想要的是把改动做完；此方法不做修复 |
| [evidence-research](skills/evidence-research/SKILL.md) | 重要结论需要定位并核对来源 | 答案只需一次查询即可得到 |
| [operations-ui-delivery](skills/operations-ui-delivery/SKILL.md) | 需要设计、修复或评审运维界面 | 工作仅涉及后端 |
| [route-subagents](skills/route-subagents/SKILL.md) | 已获授权的委派需要设定边界 | 无人授权委派；并行本身不构成许可 |
| [skill-design](skills/skill-design/SKILL.md) | 某个技能触发错位，或需要评估一个方法 | 只是修改元数据或撰写常规内容 |
| [technical-writing](skills/technical-writing/SKILL.md) | 需要依据来源撰写、重构、翻译或评审产品文档 | 要写的是普通消息或文章，或改动的是代码 |
| [text-writing](skills/text-writing/SKILL.md) | 需要为某一位特定读者撰写或重构普通文本 | 要写的是产品文档、智能体指令或提交记录 |

两个智能体配置提供的是能力边界，而非人设。`evidence-reviewer` 通过只读的取证
手段审查冻结的材料包并给出结论；`official-docs-researcher` 依据一手文档回答一个
有界限的问题。二者都不绑定模型。

> [!NOTE]
> 技能是给智能体的指令，其中一些还附带智能体可以运行的脚本。无论来自本仓库还是
> 其他任何仓库，安装前请先阅读其内容。

## 安装

技能本身是 Markdown，客户端只需加载即可。Python 3.11 及以上版本与
`requirements-tools.txt` 中固定的依赖，仅用于下文的符号链接安装器和仓库自身的
工具。

| 客户端 | 命令 | 路径状态 |
| --- | --- | --- |
| Claude Code | `/plugin marketplace add Muratovnik/assay`，然后 `/plugin install assay@assay` | 已实测 |
| 任意受支持的智能体 | `npx skills add Muratovnik/assay` | 已实测 |
| Codex | `codex plugin marketplace add Muratovnik/assay`，然后从 `/plugins` 安装 | 依据文档 |
| Cursor | `npx skills add Muratovnik/assay -a cursor` | 依据文档 |
| Gemini CLI | `gemini skills install https://github.com/Muratovnik/assay.git --consent` | 依据文档 |

**已实测**指该安装路径已针对本已发布仓库实际执行，并对安装后的文件逐字节比对。
**依据文档**指该路径遵循客户端自身的文档，但未在此处运行过。

对 Codex 而言，该 CLI 的全局安装会写入 `~/.codex/skills/`，而该路径并未出现在
当前 Codex 文档所列的技能根目录中：请改为安装到项目中，或使用下方的符号链接
安装器。各客户端的细节、卸载与升级说明见[安装指南](docs/zh-CN/install.md)。

## 快速开始

安装后请新开一个会话：客户端在启动时读取各自的技能目录。技能随后会以各自的名称
出现——`test-writing`、`independent-audit` 等等。

给智能体一个与其中某个技能相符的任务：

```text
审查 tests/test_billing.py，告诉我它是真的能防止回归，还是仅仅能跑通。
```

`test-audit` 会自行启用，无需按名称调用：它寻找的是错误的预期、漏掉的缺陷与
脆弱的断言，而不是确认这个测试集能够运行。此外不需要再安装任何东西。

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

## 文档

- [安装 assay](docs/zh-CN/install.md) —— 各客户端细节、卸载与升级。
- [升级符号链接安装](docs/zh-CN/how-to/upgrade-linked-install.md) —— 如何把符号链接安装迁移到新版本，以及出问题时如何回退。
- [assay 的组成方式](docs/zh-CN/architecture.md) —— 清单、发现拓扑与受保护的安装生命周期。
- [为什么一份源能到达多个客户端](docs/zh-CN/explanation/discovery-topology.md) —— 技能为何用链接、配置为何用渲染，以及各自的代价。
- [评测能证明什么](docs/zh-CN/evaluation.md) —— 每个技能的 `evals/` 目录能够以及不能够证明什么。
- [技能索引](skills/README.md) —— 自动生成的技能列表，含启用方式与一句话用途（英文）。

## 限制

- 没有任何数据外传：没有遥测、没有账号，也没有网络调用，唯一的例外是
  `route-subagents` 可选用的基准测试服务，且需要你自行注册。
- 脚本只接受显式路径，不会擅自向你的环境安装任何东西——这是一项值得你自行验证的
  声明，而不是应当直接采信的说法。
- 这些方法会读取仓库、文档，其中的研究方法还会读取网页。这类内容对它们而言是
  数据而非指令，方法本身也如此声明，但任何声明都不构成保证。当智能体读取过你
  无法控制的内容后，请复核它提出的方案。
- 持续集成中不运行任何模型，本仓库的技能也不带任何评分；确切范围见
  [docs/zh-CN/evaluation.md](docs/zh-CN/evaluation.md)。
- 安全问题请通过 [SECURITY.zh-CN.md](SECURITY.zh-CN.md) 私下报告，而不要公开
  提交 issue。

## 参与贡献

欢迎提交 issue 与 pull request，回复以尽力而为为准。工作流程见
[CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。编写约定，包括明确列出校验不会
检查哪些方面，见 [AGENTS.md](AGENTS.md)：那是给在本仓库工作的智能体的指令，以
英文维护。

## 许可证

MIT，见 [LICENSE](LICENSE)。
