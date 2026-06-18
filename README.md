# 万花筒 (Kaleidoscope)

![MIT License](https://img.shields.io/badge/license-MIT-green)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/made%20with-Pygame-red)

这是一个使用 Python 和 Pygame 构建的交互式万花筒绘图应用。当前版本已经重构为自绘的现代化界面，并保留像素笔刷、矢量图形、图层管理、动态效果和导出能力，允许用户轻松创作复杂、对称的艺术作品。

---

![PNG](demokaleido_art_134947.png)
![GIF](kaleido_art_084822.gif)

---

## 功能列表

- **混合绘图系统**:

  - 支持在同一画布上同时使用 **像素笔刷** 和 **矢量形状** 进行创作。
  - 提供了统一的对称和图层管理。

- **高级笔刷系统**:

  - **多种笔刷类型**: 包括平滑的 `线条`、等间距的 `圆点` 和可调节流量的 `喷枪`。
  - **精细化控制**: 可调整笔刷大小、颜色渐变、颜色抖动、圆点间距、喷枪流量和粒子大小抖动。

- **矢量形状工具**:

  - **创建与编辑**: 可直接在画布上创建 `三角形`、`星形` 等矢量图形。
  - **选择与变换**: 使用选择工具可以方便地 `选中`、`移动`、`缩放` 和 `旋转` 单个矢量形状。
  - **属性面板**: 选中形状后，可在专属面板中精确调整其大小和旋转角度。

- **强大的对称引擎**:

  - **分片数量**: 自由调整对称轴的数量，实时预览效果。
  - **对称模式**: 提供 `万花筒` (旋转+镜像) 和 `仅旋转` 两种核心对称模式。
  - **辅助线**: 可开启辅助参考线，辅助线瓣数会跟随当前分片数量，并根据背景色自动切换为高反差互补色。

- **现代化界面与颜色控制**:

  - 使用轻量的自绘 Pygame UI，入口为 `modern_app.py`。
  - 颜色区提供 `A`、`B` 和 `BG` 三个色块，分别控制渐变起点、渐变终点和画布背景色。
  - PNG/GIF 导出会保留当前画布背景色。

- **完整的图层管理**:

  - **独立图层**: 可手动 `添加`、`删除` 和 `选择` 图层，每个图层包含独立的像素和矢量数据。
  - **可见性控制**: 可随时隐藏或显示任意图层。

- **动态动画效果**:

  - **全局旋转**: 让整个画布围绕中心旋转。
  - **对象旋转**: 让所有矢量形状独立于画布进行自转。
  - **脉冲缩放**: 让整个画布实现有节奏的呼吸缩放效果。
  - **运动轨迹**: 为动画添加优雅的拖影和模糊效果。

- **完整的历史记录**:

  - 支持对几乎所有操作进行 `撤销` (Undo) 和 `重做` (Redo)，包括绘图、形状变换、图层操作等。

- **导出功能**:
  - 支持将静态画面导出为高分辨率的 **PNG** 图片。
  - 支持将带有动态效果的画面录制并导出为 **GIF** 动画。

## 特别说明

本项目在开发过程中结合了 AI 辅助编程。

- **项目构想与功能需求**: 由人类开发者提出。
- **代码实现与迭代**: 主要由 Google Gemini 2.5 Pro 模型根据需求生成。
- **调试与重构**: 由人类开发者与 AI 协作完成。

## 安装与运行

### 1. 环境要求

- Python 3.8 或更高版本

### 2. 安装步骤

克隆本仓库到本地：

```bash
git clone https://github.com/flowingx/Kaleidoscope.git
```

进入项目目录，并安装依赖项：

```bash
cd Kaleidoscope-master
pip install -r requirements.txt
```

(如果 pip 命令指向了错误的环境，请使用 python -m pip install -r requirements.txt。)

### 3. 运行程序

```bash
python main.py
```

### 4. Conda 测试环境

推荐为本项目创建独立测试环境：

```bash
conda create -n kaleidoscope-test python=3.8 -y
conda activate kaleidoscope-test
python -m pip install -r requirements.txt
python main.py
```

### 5. 本地构建 exe

在 Windows 上可使用 PyInstaller 构建单文件可执行程序：

```bash
conda activate kaleidoscope-test
python -m PyInstaller --onefile --windowed --name Kaleidoscope main.py
```

构建完成后，可执行文件位于：

```text
dist/Kaleidoscope.exe
```

## 使用说明

程序界面分为三个区域：

- **左侧 - 绘图区**: 您的主画布，使用从工具箱中选择的工具在此处进行创作。
- **中间 - 控制面板**: 包含工具箱、当前工具设置、对称性控制、颜色控制、动态效果和导出选项。
- **右侧 - 图层面板**: 用于管理您的所有绘图图层。

## 参与贡献

如果您在使用中发现任何问题或有功能建议，欢迎通过提交 Issue 来告知我们。我们也欢迎您通过 Pull Request 来直接参与代码的改进。

## 开源协议

本项目基于 MIT License 发布。
