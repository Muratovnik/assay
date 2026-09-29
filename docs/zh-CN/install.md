# 安装 assay

`route-subagents` 支持可选的路由建议：默认 `native-economy` 使用当前客户端中
合适的低成本模型；Jev 需要单独启用并同意向外部服务传输结构化数据。
v1 配置保留原有基准证据流程，v2 文件保留建议器设置；迁移创建新的 schema 3 文件，
默认为 evidence-only 模式。强制路由是 Claude Code 的独立模式，须由所有者显式启用，
见[契约](../../skills/route-subagents/references/required-routing.md)。原生模式不需要 Jev SDK 或密钥，
技能链接安装也不会更改 MCP 注册。配置、重新连接、历史记录和回滚见
[RoutingAdvisor 指南](../../skills/route-subagents/references/routing-advisor.md)。
本地契约测试不能证明模型质量或配额节省。

选择哪条安装路径，取决于你使用的客户端，以及你是否需要在技能之外再获得智能体
配置。它们安装的都是同一份源。

[English](../install.md) · [Русский](../ru/install.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

## 当前交付边界

Claude Code/Codex 插件提醒需要可通过 `python` 调用的 Python 3.11+。
skills CLI 与 `install-links` 不安装钩子；Claude 插件已包含两个配置。
单个技能保留核心约定，但不包含全部可选方法。`assay-optional-skills`
是 Assay 的检查元数据，不会自动安装依赖。历史文件检查不证明当前版本的
加载或行为。参见[交付矩阵](../install.md#installation-surfaces)。

## 自动技能提醒

完整插件为 Claude Code 和 Codex 分别生成 `hooks/hooks.json` 与
`hooks/codex.json`。`UserPromptSubmit` 根据英文或俄文请求提供简短的技能建议，
技能名称来自现有目录。会话和委派提醒仍然保留；建议不授权修改或委派，也不证明遵守。

客户端需提供 Python 3.11+ 的 `python` 命令。请求分类还需要在该解释器的隔离环境中
安装 `hooks/requirements.txt`；插件不会自动安装依赖或调用模型、网络。
Claude 强制路由守卫不依赖 Markdown 解析器，优先于建议。

更新后通过客户端界面检查插件启用和 hooks 信任。技能 CLI 与 `install-links`
不安装 hooks，也不修改个人 AGENTS.md。强制路由协议仍仅适用于 Claude；在 Codex
中明确选择 required 会阻止受保护操作，不会静默退化为建议。

详见[配置、doctor、客户端限制及离线 replay](../how-to/hooks.md)。该指南区分文件存在、
配置和运行观察，说明可选状态、回滚、重复 hooks 与 custom effort 限制。

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

使用 `-a claude-code` 或 `-a codex` 选择客户端，`-g` 选择全局范围。
`--skill '*'` 选择完整集合；`--skill <名称>` 只安装一个技能，不会递归安装
关联方法。

根据客户端当前文档核对该 CLI 版本报告的目标路径。发现遗漏时使用受支持的
项目级安装或下方明确的链接布局，不要猜测并创建额外别名。

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

如果 Claude Code 已安装插件，插件本身就提供这些技能和两个配置，Claude 条目会让每个
技能出现两次。给 `plan`、`install-links` 和 `uninstall-links` 加上
`--client codex` 只处理 Codex 条目，加上 `--client claude` 则只处理 Claude 条目。
Claude 的技能链接经由 Codex 链接解析，因此单独安装 Claude 需要 Codex 链接已就位；
只要 Claude 链接仍在，单独移除 Codex 就会被拒绝。要从现有安装中去掉 Claude 条目，
运行 `python tools/assay.py uninstall-links --client claude`。

## 卸载

```text
python tools/assay.py uninstall-links
```

只有链接目标或渲染字节仍与当前计划完全一致的条目才会被移除。你手工改动过的内容
会被保留并在输出中列出：卸载不会悄悄丢弃你的修改。

对于插件安装路径，请使用客户端自带的卸载方式：`claude plugin uninstall
assay@assay`，或你所用客户端的插件管理器。

## 升级

拉取新版本后重新运行安装器，每一步都保持相同的 `--client` 选择。如果两个版本之间
配置适配器发生了变化，升级需要按
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
