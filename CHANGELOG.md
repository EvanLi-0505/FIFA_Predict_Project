# 更新日志

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本 SemVer](https://semver.org/lang/zh-CN/)：

- 只有修复：修订号 +1（2.0.0 → 2.0.1）
- 有新功能（不论是否同时有修复）：次版本 +1，修订号归零（2.0.1 → 2.1.0）
- 有不兼容变化、功能移除或大改版：主版本 +1，其余归零（2.1.0 → 3.0.0）

## [2.0.1] - 2026-10-23

### 修复
- 从网上下载的压缩包用 Windows 资源管理器解压后，双击无法启动，报错「Failed to resolve Python.Runtime.Loader.Initialize」。原因是解压出的文件带有"来自互联网"标记，.NET Framework 拒绝加载其中的 DLL；现在 exe 旁附带 `FIFA-Prediction.exe.config` 允许加载

### 变更
- 压缩包根目录新增 `FIFA-Prediction.exe.config`（必须与 exe 放在一起）
- 后端与前端版本号更新为 2.0.1

## [2.0.0] - 2026-10-21

### 新增
- 桌面版启动时窗口立即显示加载画面，后端在后台并行启动，窗口约 1 秒出现（原先约 5 秒内无任何窗口）
- 后端端口被占用时自动改用其他空闲端口（优先 17872）
- 新增 `LICENSE`（保留所有权利）与本更新日志

### 变更
- Release 压缩包不再多套一层文件夹，解压后直接是 `FIFA-Prediction.exe`、`_internal\`、`LICENSE`
- 后端启动等待上限从 30 秒放宽到 120 秒；后端异常退出时立即报错，不再空等
- WebView2 浏览器缓存保留在 `data\webview2\`，不再每次关闭时删除、启动时重建
- 关闭软件从约 5.7 秒缩短到约 2.3 秒
- 后端与前端版本号统一为 2.0.0

### 修复
- 解压后首次启动时，Windows Defender 扫描耗时超过 30 秒导致误报「后端无法启动」
- 17872 端口被其他程序占用时后端无法启动
- 桌面版的 API 文档（`/docs`、`/openapi.json`）返回 500 错误

### 移除
- 手机端适配（移动端 viewport 设置与窄屏布局），网页版与桌面版不受影响
- 仓库中不再包含课程参考资料、原始 Notebook 与图标源文件

### 兼容性
- 数据格式不变。从 1.x 升级：解压新版本后，把旧版本文件夹里的 `data\` 整个复制到新的 `FIFA-Prediction.exe` 旁边即可

## [1.0.1] - 2026-09-13

### 修复
- 桌面版点击「Download Markdown / Download PDF」没有任何反应（WebView2 默认拦截下载）

## [1.0.0] - 2026-09-13

### 新增
- 首个版本：网页版（Vue 3 + FastAPI + MySQL）与 Windows 桌面版（pywebview + WebView2，便携免安装）共用同一套机器学习核心
- 比赛结果预测（主胜 / 平局 / 主负）、球队对比、预测历史、数据集与模型管理
- 预测报告导出为 Markdown 与 PDF
