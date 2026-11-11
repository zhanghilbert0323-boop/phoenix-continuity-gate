# Phoenix v0.2.1 预览：先跑一遍

需要 Windows 电脑安装 Python 3.11 或更新版本，以及 Git。当前只在 Windows 上验证；这两个程序都需要能从命令行调用。

1. 将 ZIP 解压到新文件夹。
2. 打开能看到 `README.md` 和 `phoenix_continuity_gate` 的那层文件夹。
3. 双击 `START_DEMO.cmd`。窗口会检查已安装的 Python 和 Git，再运行临时演示；结束后停留，按任意键才退出。

它不会安装软件、修改全局 PATH 或要求管理员权限。请只运行你从本项目可信来源下载的脚本；如果系统阻止运行，不要关闭杀毒或降低系统安全设置，保留提示文字反馈。

如果你愿意使用命令行：点资源管理器顶部地址栏，输入 `cmd`，按回车，然后运行：

```cmd
python -m phoenix_continuity_gate demo-record
```

如果找不到 `python`，可以尝试 `py -m phoenix_continuity_gate demo-record`。若仍有错误，保留窗口并发送报错文字；无输出不等于成功。

只检查环境、不运行演示：在同一个命令窗口运行 `START_DEMO.cmd --check`。输出“Prerequisites found”只表示找到了运行条件，不表示测试通过。自动化使用可追加 `--no-pause`。

启动器会列出已安装的 Python 并探测实际解释器，跳过 WindowsApps 商店快捷入口；不接受只有退出码 0、却没有实际 Python 探测输出的结果。特殊安装若未被找到，可用你已安装的 Python 完整路径运行 `start_demo.py`。

正常情况下会看到四步：

| 步骤 | 命令执行结果 | 记录与当前代码 | Gate |
| --- | --- | --- | --- |
| 实际测试正常代码 | SUCCEEDED：成功退出 | MATCH：一致 | PASS |
| 改坏代码后查看旧记录 | SUCCEEDED：旧执行曾成功 | CHANGED：已经变化 | BLOCK |
| 对改坏的代码重新测试 | FAILED：执行失败 | MATCH：对应当前代码 | BLOCK |
| 修复并重新测试 | SUCCEEDED：成功退出 | MATCH：一致 | PASS |

这是临时样例：程序会真的运行测试，然后自动清理样例文件。不会替你修改实际项目代码。

`record` 是显式运行一条命令并记录它；`inspect` 是读取记录、比较当前文件。完整用法见 README。`inspect` 不会执行记录里写的命令。

仍需知道的边界：成功退出不保证测试充分或代码正确；记录是可编辑的本地 JSON，不是防伪凭证。当前版本也不会观察所有外部依赖或执行期间的每一次文件变化。
