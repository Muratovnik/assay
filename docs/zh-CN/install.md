# 安装 assay

`route-subagents` 支持可选的路由建议：默认 `native-economy` 使用当前客户端中
合适的低成本模型；Jev 需要单独启用并同意向外部服务传输结构化数据。
v1 配置保留原有基准证据流程，v2 迁移创建新文件。原生模式不需要 Jev SDK 或密钥，
技能链接安装也不会更改 MCP 注册。配置、重新连接、历史记录和回滚见
[RoutingAdvisor 指南](../../skills/route-subagents/references/routing-advisor.md)。
本地契约测试不能证明模型质量或配额节省。

选择哪条安装路径，取决于你使用的客户端，以及你是否需要在技能之外再获得智能体
配置。它们安装的都是同一份源。

[English](../install.md) · [Русский](../ru/install.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

## 哪些已实测，哪些没有

Claude Code 路径与技能 CLI 路径已针对已发布的仓库实际执行，并对安装后的文件逐
字节比对。Codex、Cursor 与 Gemini CLI 的路径遵循各自客户端的文档，但未在此处
运行过。这一区分是刻意保留的：一个要求别人区分「已验证」与「有文档」的库，自己
更应当做到。

## 自动技能提醒

Codex 和 Claude Code 的完整插件包含由 `tools/assay.py render` 生成的
[`hooks/hooks.json`](../../hooks/hooks.json)。会话开始、恢复及上下文压缩后，
它提醒使用匹配的技能；启动子智能体时，提醒必须应用 `route-subagents`，
明确选择模型和 effort，并使用最小必要上下文。替换执行者和审查者同样适用。

客户端执行环境必须提供名为 `python` 的 Python 3.11+。处理器仅使用标准库，
不调用模型或网络，不读取会话记录，不修改设置。每个事件添加少于 1,000 个字符，
仍有少量上下文成本；超时为五秒。禁用或卸载插件会移除其提醒。

安装或更新后启动新会话。在 **Codex** 中，通过客户端的 hooks 信任流程审阅并
信任当前 Assay 定义；安装本身不代表信任。禁用 hooks 或仅允许托管 hooks 的策略
会阻止插件提醒。在 **Claude Code** 的 `/hooks` 中检查 Assay 的 `SessionStart`
和 `PreToolUse` 条目，执行失败时查看 hooks 诊断。参见
[Codex 文档](https://learn.chatgpt.com/docs/hooks) 和
[Claude Code 文档](https://code.claude.com/docs/en/hooks)。

**技能 CLI 和 `install-links` 不会安装插件 hooks。** 需要提醒时使用完整插件。
Assay 不修改个人 `AGENTS.md`。其他客户端保留普通技能发现；这些提醒事件仅针对
支持相应 hooks 的 Codex 和 Claude Code。

提醒不是强制门禁：pre-tool 上下文不会暂停已选择的调用让模型重新决策，部分工具
路径也可能绕过 hooks。处理器不授权委派、不修改参数，也不固定模型。离线测试验证
事件与命令，不证明客户端发现、技能遵守或配额节省。上面的安装验证早于这些 hooks。

在 checkout 中无需调用模型即可检查处理器：

```text
python -B -m unittest tools.test_skill_reminder
```

若没有条目，确认启用的是包含此改动的完整插件，而不只是技能链接。若执行失败，
检查客户端环境中的 `python --version` 和 hooks 诊断。处理器测试通过不等于插件
已在该客户端启用并获得信任。

## Claude Code

```text
claude plugin marketplace add Muratovnik/assay
claude plugin install assay@assay
```

对应的斜杠命令是 `/plugin marketplace add Muratovnik/assay` 与
`/plugin install assay@assay`。加上 `--scope project` 可只为某一个仓库安装，而
不是为整个账号；在市场名称后附加标签即可固定到某个发布版本，例如
`Muratovnik/assay@v0.2.0`。

安装后请新开一个会话。技能会以各自的名称出现，两个智能体配置也随插件一同到位。

## Codex

```text
codex plugin marketplace add Muratovnik/assay
```

随后在 CLI 中打开 `/plugins`，从该市场安装 assay，并重启 Codex。

Codex 从项目中的 `.agents/skills` 读取技能，并逐级向上直到仓库根目录，账号级则
读取 `$HOME/.agents/skills`。它的智能体定义位于 `~/.codex/agents/*.toml`，插件
路径不会写入该位置：若需要配置，请使用下方的符号链接安装器。

## 通过技能 CLI 安装到任意智能体

```text
npx skills add Muratovnik/assay
```

加上 `-a claude-code` 或 `-a codex` 可指定单一客户端，`-g` 表示全局安装而非项目
安装，`--skill <名称>` 则只取其中一个方法，而不是整个库。

有一点值得注意：对 Codex 而言，该 CLI 的全局安装会写入 `~/.codex/skills/`，而当前
Codex 文档并未把这个路径列为技能根目录。如果安装后 Codex 看不到这些技能，请改为
安装到项目中，或使用符号链接安装器。

## Gemini CLI

```text
gemini skills install https://github.com/Muratovnik/assay.git --consent
```

Gemini 把 `~/.agents/skills` 与 `.agents/skills` 视为自身技能根目录的别名，因此
符号链接安装器在这里同样适用。

## Cursor

```text
npx skills add Muratovnik/assay -a cursor
```

Cursor 把个人技能放在 `~/.cursor/skills/`，技能 CLI 知道这个路径。Cursor 自身的
仓库导入功能位于 Dashboard 中的团队市场，面向团队管理员，而不是个人安装。

## 符号链接安装器

当你需要智能体配置，或者你正在修改检出目录并希望改动立即生效时，使用这一方式。

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
python tools/assay.py plan
python tools/assay.py install-links
```

`plan` 不写入任何内容。它会逐个打印将要创建的目标，以及每个目标对应的精确回滚
目标；`--json` 以结构化形式输出同样的内容，`--home` 则把整个计划指向一个隔离
目录，用于试运行。

随后 `install-links` 会创建：

```text
~/.agents/skills/<名称>   -> <检出目录>/skills/<名称>
~/.claude/skills/<名称>   -> ~/.agents/skills/<名称>
~/.codex/agents/<配置>.toml   由 profiles/<配置>.json 渲染
~/.claude/agents/<配置>.md    由 profiles/<配置>.json 渲染
```

它会先对整个计划做预检。真实目录、外来链接、被修改过的适配器，或作为重解析点的
上级目录，都会在第一次写入之前中止本次运行。

**在 Windows 上**，创建目录符号链接需要相应权限，通常是开发者模式或提升权限的
终端。缺少该权限时安装器直接失败，不会退回到调用 shell。

## 卸载

```text
python tools/assay.py uninstall-links
```

只有链接目标或渲染字节仍与当前计划完全一致的条目才会被移除。你手工改动过的内容
会被保留并在输出中列出：卸载不会悄悄丢弃你的修改。

对于插件安装路径，请使用客户端自带的卸载方式：`claude plugin uninstall
assay@assay`，或你所用客户端的插件管理器。

## 升级

拉取新版本后重新运行安装器。如果两个版本之间配置适配器发生了变化，升级需要按
以下顺序分两步进行：

```text
# 在创建了当前适配器的那个版本上执行
python tools/assay.py uninstall-links
# 然后在新版本上执行
python tools/assay.py install-links
```

这一点很重要，因为卸载只会移除它能识别的字节。适配器变化之后再从新版本执行卸载，
旧的适配器会留在原处，只能手工清理。

在执行上述任一步骤之前，请把现有适配器字节与链接目标复制一份到受管目录之外。
那份外部快照才是回滚依据；安装目录旁边的状态文件不是。

同一次升级的逐步操作，包括事先要保存什么、出问题后如何回退，见
[升级符号链接安装](how-to/upgrade-linked-install.md)。
