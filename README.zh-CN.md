# ILC Output Guard Skill

这是一个可复用的 public skill，用于把反复出现的输出、格式、解释失败做成 ILC-style 闭环。

## 包含内容

- 可安装 skill：[`ilc-output-guard`](./ilc-output-guard)
- 默认 bucket 目录：[`ilc-output-guard/references/buckets.md`](./ilc-output-guard/references/buckets.md)
- 辅助脚本：[`ilc-output-guard/scripts/ilc_output_guard.py`](./ilc-output-guard/scripts/ilc_output_guard.py)

## 安装 / 使用

- `Codex App`：从本 repo 的 `ilc-output-guard` 路径安装
- GitHub 安装目标：
  - repo：`<owner>/ilc-output-guard-skill`
  - path：`ilc-output-guard`
- 安装后重启 `Codex App`，让 skill 被重新发现。

## 覆盖范围

- 将输出反馈归入稳定 buckets
- 草稿前根据历史 bucket 做 feedforward
- 发送前做确定性 draft check
- 对历史 replay 或重复反馈做 dedupe
- state 文件由调用方指定，public 包不携带私有 state

## 典型触发

- `Build an ILC-based guard for this output style.`
- `Remember this formatting failure and tighten future drafts.`
- `Run output guard preflight before sending this explanation.`
- `Replay old feedback without double-counting the same event.`

## 非触发

- `Rewrite this paragraph once.`
- `Check grammar only.`
- `Store private memory in a public repo.`

## 隐私边界

这个 public repo 只保留通用机制。

- 不包含私有 session logs、personal memory 或 live ILC state。
- state path 由调用方提供，默认只落在当前工作目录。
- bucket 名称是 generic 的，安装后可按具体 agent 规则扩展。

## 仓库结构

- `ilc-output-guard/`：可安装 skill
- `ilc-output-guard/references/`：public references
- `ilc-output-guard/scripts/`：helper scripts
- `CHANGELOG.md`：release history
- `LICENSE`：`MIT`
