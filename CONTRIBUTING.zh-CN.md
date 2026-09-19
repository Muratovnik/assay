# 参与贡献

[English](CONTRIBUTING.md) · [Русский](CONTRIBUTING.ru.md) · **简体中文**

英文版本为准。命令输出、规则名称与配置键不作翻译。

感谢你来看。这是一个人维护的一组方法，之所以公开，是因为它们或许对你的智能体也
有用。欢迎提交 issue 与 pull request；回复以尽力而为为准，不保证当天回复。

## 动手之前

**新增技能请先开 issue。**门槛是「有一个以上已证实的使用方的能力」；在动手前听到
「这个方法已被现有技能覆盖」，比在评审时才发现要省事得多。把两个技能合并为一个，
在这里是正常结果。

**小修不必讲究流程。**指令写错、链接失效、描述在不该触发的任务上触发——直接提交
pull request。

## 环境准备

```text
git clone https://github.com/Muratovnik/assay.git
cd assay
python -m pip install -r requirements-tools.txt
```

请使用隔离环境。本仓库中的任何东西都不会装进全局环境，也不应该开始这么做。

## 校验

提交改动前先跑一遍，只需几秒。

```text
python -B tools/check.py --all
```

这条命令运行全部校验并逐项报告，不会在第一个失败处停下。`make check` 是同一条
命令，并会创建审计材料包测试集所需的临时目录，因此无需事先准备任何东西。

要单独运行某一项校验，清单在 `tools/check.py` 中。持续集成在 Linux 与 Windows 上
运行 `check --all`，随后运行带历史检查的发布审计，并在 Linux 上用
`claude plugin validate .` 校验 Claude 插件清单。

校验**不会**检查哪些方面，写在 [AGENTS.md](AGENTS.md)（英文）里；在信任一次绿色
运行之前，请先读它。

## 如何新增技能

1. 创建 `skills/<name>/SKILL.md`，在 frontmatter 中写明 `name`（与目录同名）、
   `description` 与 `license: MIT`。
2. `description` 要成对地写：何时使用该方法，以及何时跳过它。后半句才是让它不在
   无关工作上触发的关键。
3. 保持 `SKILL.md` 简短。有条件才需要的深度放进 `references/`，仅在任务需要时
   加载。
4. 添加 `agents/openai.yaml`，其中的 Codex 界面字符串使用英文。
5. 添加 `evals/`，包含用例与单独的评分标准。输入与评分标准分开存放，并且在技能
   执行用户任务期间都不会被读取。
6. 在 `catalog.toml` 中登记该资产，然后运行
   `python -B tools/catalog_docs.py --write` 与 `python -B tools/assay.py render`，
   刷新生成的清单、客户端清单与技能索引。校验会比对这些字节，漏掉 render 会让
   构建失败。

技能如果需要脚本，脚本放在该技能目录内，并带上自己的依赖文件。它们接受显式路径，
绝不写死你本机的路径，并在退出码中区分成功、被证否的条件与证据缺失。

## 提交信息

采用 Conventional Commits，类型限定为 `build`、`chore`、`ci`、`docs`、`feat`、
`fix`、`perf`、`refactor`、`revert`、`style`、`test`。scope 可选且小写；`!` 表示
破坏性变更。

写清楚改了什么，以及为什么值得改。只复述 diff 的提交信息，会让读者花掉你省下的
那些时间。

`CHANGELOG.md` 遵循 Conventional Commits 的 Angular 预设：`feat` 与 `fix` 的标题
成为条目，可选的 scope 成为加粗前缀，`BREAKING CHANGE` 脚注自成一节。你的标题就是
条目，所以请为读发布说明的人写，而不是为读 diff 的人写。

**不要在提交、pull request、发布说明或受版本管理的文件中，把 AI 工具列为作者、
共同作者、评审者或生成者。**请使用你自己的身份。

## 如何报告问题

一份好的技能问题报告会说明：你提了什么要求、哪个技能启用了或本该启用却没有，以及
它产出了什么。请附上客户端及其版本：各客户端的启用行为并不相同，在某一个客户端上
触发错位的方法，在另一个上可能是正确的。

任何与安全相关的问题，请通过 [SECURITY.zh-CN.md](SECURITY.zh-CN.md) 反馈，而不要
公开提交 issue。
