# 现代简约别墅 — 全套建筑图纸生成器

使用 Python 代码生成自建房 / 别墅的全套建筑图纸（DXF + PNG），包含平面图、立面图、剖面图、给排水、电气、3D 效果图。

**在线预览**: [GitHub Pages](https://narwal.github.io/house-floor-plan/)

![南立面透视效果图](docs/images/南立面透视效果图.png)

## 项目参数

| 参数 | 值 |
|------|-----|
| 占地尺寸 | 14m × 11m |
| 建筑面积 | 308 ㎡ |
| 建筑层数 | 2 层 |
| 卧室配置 | 3 主卧 + 2 次卧 |
| 建筑风格 | 现代简约 |

## 快速开始

```bash
pip install ezdxf matplotlib numpy Pillow

# 生成全套图纸（DXF → 图纸/，PNG → docs/images/）
python .cursor/skills/house-floor-plan/scripts/generate_all.py

# 生成 3D 透视效果图（PNG → docs/images/）
python .cursor/skills/house-floor-plan/scripts/generate_render_3d.py
```

## 输出文件

### DXF 源文件（AutoCAD 可编辑）

```
图纸/
├── 01-建筑设计/
│   ├── 平面图/        一层平面图.dxf, 二层平面图.dxf
│   ├── 立面图/        南/北/东/西立面图.dxf
│   ├── 剖面图/        1-1剖面图.dxf
│   └── 屋顶平面图/    屋顶平面图.dxf
├── 02-给排水设计/     一层/二层给排水平面图.dxf
└── 03-电气设计/       一层/二层电气平面图.dxf
```

### PNG 预览图（GitHub Pages 展示）

```
docs/images/          ← 脚本直接输出，GitHub Pages 直接读取
├── 一层平面图.png
├── 二层平面图.png
├── 南/北/东/西立面图.png
├── 1-1剖面图.png
├── 屋顶平面图.png
├── 一层/二层给排水平面图.png
├── 一层/二层电气平面图.png
├── 南立面渲染效果图.png
├── 南立面透视效果图.png
├── 东南角透视效果图.png
└── 一层/二层室内俯视效果图.png
```

## 图纸预览

### 平面图

| 一层平面图 | 二层平面图 |
|:---------:|:---------:|
| ![一层](docs/images/一层平面图.png) | ![二层](docs/images/二层平面图.png) |

### 立面图

| 南立面 | 北立面 |
|:------:|:------:|
| ![南](docs/images/南立面图.png) | ![北](docs/images/北立面图.png) |

| 东立面 | 西立面 |
|:------:|:------:|
| ![东](docs/images/东立面图.png) | ![西](docs/images/西立面图.png) |

### 效果图

| 南立面渲染 | 东南角透视 |
|:---------:|:---------:|
| ![渲染](docs/images/南立面渲染效果图.png) | ![透视](docs/images/东南角透视效果图.png) |

## 技术栈

- **ezdxf** — 生成 AutoCAD DXF 文件
- **matplotlib** — 生成 PNG 预览图（平面图、立面图、剖面图、给排水、电气）
- **Pillow + numpy** — 生成 3D 透视渲染效果图

## GitHub Pages

本项目使用 `docs/` 目录作为 GitHub Pages 源。脚本生成的 PNG 直接写入 `docs/images/`，与展示页面路径一致，无需手动同步。

配置方式：**Settings → Pages → Source: Deploy from branch → Branch: main → Folder: /docs**

## Cursor Skill

本项目包含一个 [Cursor Agent Skill](.cursor/skills/house-floor-plan/SKILL.md)，可在 Cursor IDE 中自动识别和使用，辅助设计自建房户型图。
