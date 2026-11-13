# Installable development preview / 可安装开发预览

Version: `0.2.3.dev0`. This is an experimental developer release. It includes
the `phoenix-gate` console entry point, `inspect --json`, UTF-8 BOM reading
compatibility, and a task-resume example. It has not been published to PyPI.

Release page:
https://github.com/zhanghilbert0323-boop/phoenix-continuity-gate/releases/tag/v0.2.3-dev0

## Which download? / 下载哪个？

- `phoenix_continuity_gate-0.2.3.dev0-py3-none-any.whl`: installable Python
  package. It does not bundle Python or Git. No runtime dependencies or source
  build are needed when installing this wheel.
- `phoenix-continuity-gate-0.2.3.dev0.zip`: source, tests, Windows demo launcher,
  documentation and `examples/resume_task.py`. Extract the entire folder.
- `SHA256SUMS.txt`: checksums of these two artifacts, useful for checking
  download consistency. A checksum file does not independently establish trust.

中文：想用安装后的短命令，下载 wheel；想看源码、跑测试或运行接入示例，也下载源码 ZIP。
wheel 仍需要电脑已有 Python 3.11+ 和 Git，不是免安装 Python 的独立应用。

## Windows CMD

Open a working folder in Command Prompt. Create a fresh environment, then replace
the wheel path below with the file you downloaded:

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-index --no-deps "C:\path\to\phoenix_continuity_gate-0.2.3.dev0-py3-none-any.whl"
.venv\Scripts\phoenix-gate.exe --version
.venv\Scripts\phoenix-gate.exe demo-record
```

中文：上面的命令使用独立环境，不需要激活 PowerShell 脚本。将 wheel 路径换成真实下载位置。
如果提示找不到 Python 或 Git，请先解决运行环境问题；没有输出不能算成功。

## Linux / macOS terminal

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps /path/to/phoenix_continuity_gate-0.2.3.dev0-py3-none-any.whl
.venv/bin/phoenix-gate --version
.venv/bin/phoenix-gate demo-record
```

Windows and Ubuntu are covered by our hosted installation checks. macOS remains
unverified; these terminal commands are instructions, not a macOS test result.

## Use the interface / 使用接口

After installation, use the environment's executable from any directory:

```text
phoenix-gate inspect --repo "your project path" --record "your record path" --json
```

The short command requires that environment's scripts directory on PATH (for
example, after environment activation). You can always use the full executable
path as in the commands above instead. Keep records outside the checked project.

`inspect` reads evidence; it does not run the command stored in a record. To
create a record with `record`, choose a project test command you understand.
Full arguments and limitations are in README.md. Git and Python still need to
be available when a chosen test command requires them.

## Try the resume example / 运行接入示例

Use the environment's Python and the example from the extracted source ZIP:

```cmd
.venv\Scripts\python.exe "C:\path\to\extracted\examples\resume_task.py" --repo "your project path" --record "your record path"
```

On Linux, use `.venv/bin/python` and your extracted example path. The example
prints an evidence-handling suggestion. It does not start an agent or authorize
merge, deployment or any other external operation. See examples/README.md.

## Feedback / 反馈

Report the actual version, operating system, whether installation worked, and a
redacted error or one concrete workflow observation. Do not share private source,
credentials or complete execution JSON. A successful demo is not evidence of
customer value; “my existing tools already cover this” is useful feedback too.
