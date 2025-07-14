# GitHub Actions 工作流说明

本目录包含用于自动构建多平台wheel包的GitHub Actions工作流文件。

## 工作流文件

### 1. `build-wheels.yml` - 完整版构建工作流

**功能特性：**
- ✅ 多平台构建（macOS x86_64/ARM64、Linux、Windows）
- ✅ 自动发布到PyPI（标签推送时）
- ✅ 创建GitHub Release
- ✅ 完整的测试和验证
- ✅ 可信发布支持

**触发条件：**
- 推送到 `main` 或 `develop` 分支
- 创建以 `v` 开头的标签（如 `v1.0.0`）
- Pull Request 到 `main` 分支
- 手动触发

**适用场景：**
- 正式发布版本
- 需要自动发布到PyPI
- 生产环境使用

### 2. `build-wheels-simple.yml` - 简化版构建工作流

**功能特性：**
- ✅ 多平台构建（macOS x86_64/ARM64、Linux、Windows）
- ✅ 构建结果汇总
- ✅ 基本测试验证
- ❌ 不包含发布功能
- ❌ 更简洁的配置

**触发条件：**
- 推送到 `main` 或 `develop` 分支
- Pull Request 到 `main` 分支
- 手动触发

**适用场景：**
- 开发和测试阶段
- 快速验证多平台兼容性
- 不需要自动发布

## 使用方法

### 手动触发构建

1. 进入GitHub仓库页面
2. 点击 "Actions" 标签
3. 选择要运行的工作流
4. 点击 "Run workflow" 按钮
5. 选择分支并点击 "Run workflow"

### 自动触发构建

**推送代码触发：**
```bash
# 推送到main分支触发构建
git push origin main

# 推送到develop分支触发构建
git push origin develop
```

**创建标签触发发布：**
```bash
# 创建并推送标签（仅完整版工作流会发布）
git tag v1.0.0
git push origin v1.0.0
```

## 构建产物

### Artifacts（构建产物）

每次构建完成后，可以在Actions页面下载以下产物：

**简化版工作流：**
- `wheels-macOS-x86_64` - macOS Intel版本
- `wheels-macOS-arm64` - macOS Apple Silicon版本
- `wheels-Linux-x86_64` - Linux版本
- `wheels-Windows-x64` - Windows版本
- `release-ready-all-platforms` - 所有平台的汇总包

**完整版工作流：**
- 各平台单独的wheel包
- `source-distribution` - 源分发包
- 自动发布到PyPI（标签推送时）
- GitHub Release（标签推送时）

### 平台特定的wheel包

每个平台的wheel包只包含对应平台的库文件：

- **macOS x86_64**: `libthreedtiles_lib_x86_64.dylib`
- **macOS ARM64**: `libthreedtiles_lib_arm64.dylib`
- **Linux**: `libthreedtiles_lib.so`
- **Windows**: `windows_lib/` 目录下的所有DLL文件

## 配置说明

### PyPI发布配置

如果要启用自动发布到PyPI，需要配置以下之一：

**方法1：可信发布（推荐）**
1. 在PyPI项目设置中配置可信发布
2. 添加GitHub Actions作为可信发布者
3. 无需API token

**方法2：API Token**
1. 在PyPI生成API token
2. 在GitHub仓库设置中添加 `PYPI_API_TOKEN` 密钥
3. 取消注释工作流中的 `password` 行

### 环境要求

- Python 3.8+
- 所有必要的库文件已存在于 `src/osgb23dtiles/libs/` 目录
- 正确配置的 `setup.py` 和 `build_wheels.py`

## 故障排除

### 常见问题

**1. macOS架构检测错误**
```yaml
# 在工作流中强制指定架构
arch_cmd: "arch -arm64"  # 或 "arch -x86_64"
```

**2. 库文件未包含**
- 检查 `setup.py` 中的 `get_package_data()` 函数
- 验证 `MANIFEST.in` 文件配置
- 确认库文件路径正确

**3. wheel包标记为universal**
- 确保 `BinaryDistribution` 类正确实现
- 检查 `bdist_wheel` 类的 `root_is_pure` 设置

**4. 构建失败**
- 查看Actions日志中的详细错误信息
- 检查依赖是否正确安装
- 验证Python版本兼容性

### 调试技巧

**查看构建日志：**
1. 进入Actions页面
2. 点击失败的工作流运行
3. 展开相应的步骤查看详细日志

**本地测试：**
```bash
# 在本地运行构建脚本
python build_wheels.py

# 检查生成的wheel内容
unzip -l dist/*.whl
```

## 最佳实践

1. **版本管理**：使用语义化版本号（如 v1.0.0）
2. **测试**：在推送标签前先测试构建
3. **文档**：更新版本说明和变更日志
4. **验证**：下载构建产物进行本地测试
5. **监控**：关注构建状态和错误通知

## 示例工作流程

### 开发阶段
```bash
# 1. 开发新功能
git checkout -b feature/new-feature

# 2. 提交代码
git add .
git commit -m "Add new feature"

# 3. 推送并创建PR
git push origin feature/new-feature
# 创建PR到main分支，自动触发构建测试
```

### 发布阶段
```bash
# 1. 合并到main分支
git checkout main
git merge feature/new-feature

# 2. 更新版本号（在setup.py中）
# 3. 创建标签并推送
git tag v1.1.0
git push origin main
git push origin v1.1.0

# 4. 自动触发完整构建和发布流程
```

这样就可以实现完全自动化的多平台wheel包构建和发布流程！