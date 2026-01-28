# 3D Mesh Crease Identification (折痕识别)

一个用于检测3D网格模型中尖锐边（折痕）的Python工具，基于二面角阈值进行识别，并对光滑区域进行划分。

## 功能特性

- ✅ **自动加载OBJ格式网格**：支持单个文件或目录批量处理
- ✅ **二面角计算**：计算所有内部边的二面角（单位：度）
- ✅ **尖锐边检测**：基于用户可配置的二面角阈值识别尖锐边
- ✅ **光滑区域划分**：使用广度优先搜索（BFS）算法划分连接的光滑面区域
- ✅ **丰富的可视化输出**：
  - 二面角热力图（3D彩色编码）
  - 二面角热力图四视图（正视图、俯视图、侧视图、等轴测视图）
  - 二面角分布直方图
- ✅ **Times New Roman字体**：所有图表使用Times New Roman字体
- ✅ **结构化数据导出**：
  - 尖锐边信息（CSV）
  - 区域划分信息（CSV）
  - 统计信息（JSON）
  - 处理摘要（JSON）

## 安装

### 依赖项
```bash
pip install numpy trimesh matplotlib networkx
```

或使用项目中的 `requirements.txt`：
```bash
pip install -r requirements.txt
```

### 快速开始
```bash
git clone <repository-url>
cd crease_identification
pip install -r requirements.txt
```

## 使用方法

### 基本命令
```bash
python scripts/crease_identification.py --input <OBJ文件或目录> [选项]
```

### 命令行参数
| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | `-i` | **必需** | 输入OBJ文件或包含OBJ文件的目录 |
| `--threshold` | `-t` | `45.0` | 二面角阈值（度），大于等于此值的边被视为尖锐边 |
| `--output` | `-o` | `output` | 输出数据目录 |
| `--figures` | `-f` | `figures` | 输出图片目录 |

### 示例

1. **处理单个OBJ文件**：
   ```bash
   python scripts/crease_identification.py --input assets/nonsmooth_geometry/Cube.obj --threshold 30.0
   ```

2. **批量处理目录中的所有OBJ文件**：
   ```bash
   python scripts/crease_identification.py --input assets/ --threshold 45.0 --output my_results --figures my_figures
   ```

3. **使用自定义阈值**：
   ```bash
   python scripts/crease_identification.py --input assets/complex_geometry/Gear.obj --threshold 60.0
   ```

## 项目结构
```
crease_identification/
├── assets/                    # 示例OBJ网格文件
│   ├── smooth_geometry/       # 光滑几何体（球体、环面等）
│   ├── nonsmooth_geometry/    # 非光滑几何体（立方体、圆锥等）
│   ├── complex_geometry/      # 复杂几何体（齿轮、凸轮等）
│   └── combinatorial_geometry/# 组合几何体
├── packages/                  # 核心算法模块
│   └── preprocessing.py       # 网格预处理、尖锐边检测、区域划分
├── scripts/                   # 应用脚本
│   └── crease_identification.py  # 主程序
├── output/                    # 数据输出目录（自动生成）
├── figures/                   # 图片输出目录（自动生成）
├── temps/                     # 参考代码（区域划分算法来源）
├── requirements.txt           # Python依赖包列表
├── LICENSE                    # 许可证文件
└── README.md                  # 本文件
```

## 算法原理

### 1. 二面角计算
对于每条边，计算其二面角：
- **内部边**（两个相邻面）：计算两个面法向量之间的夹角，范围为 0°~180°
- **边界边**（一个相邻面）：计算外角，固定为 270°（代表如立方体边缘的90°拐角）
- 计算每个面的法向量（叉积归一化）
- 计算点积并反余弦得到弧度值
- 转换为角度（0°~360°）

### 2. 尖锐边检测
- **内部边**：如果二面角 ≥ 阈值，标记为尖锐边
- **边界边**（只属于一个面的边）：自动标记为尖锐边
- **非流形边**（属于三个或以上面的边）：自动标记为尖锐边

### 3. 光滑区域划分
1. 构建面邻接图，排除尖锐边
2. 使用广度优先搜索（BFS）查找连通分量
3. 每个连通分量构成一个光滑区域

## 输出文件说明

### 1. 数据文件 (`output/<mesh_name>/`)
- `<mesh_name>_sharp_edges.csv`：尖锐边详细信息
  - 列：`vertex1`, `vertex2`, `dihedral_angle_deg`, `is_sharp`
- `<mesh_name>_regions.csv`：区域划分信息
  - 列：`region_id`, `face_index`, `vertex1`, `vertex2`, `vertex3`
- `<mesh_name>_statistics.json`：统计信息
  - 包含顶点数、面数、内部边数、尖锐边数、区域数、二面角统计量等
- `processing_summary.json`：所有网格的处理摘要（根目录）

### 2. 可视化文件 (`figures/<mesh_name>/`)
- `<mesh_name>_dihedral_heatmap.png`：二面角热力图
  - 蓝色→绿色→红色表示角度由小到大（0°~360°）
  - 尖锐边以粗线高亮显示
  - 保持等轴比例，准确呈现几何形状
  - 使用Times New Roman字体
- `<mesh_name>_dihedral_heatmap_4view.png`：二面角热力图四视图
  - 包含正视图、俯视图、侧视图、等轴测视图
  - 统一的颜色条和比例
  - 使用Times New Roman字体
- `<mesh_name>_dihedral_histogram.png`：二面角分布直方图
  - 显示所有内部边的角度分布
  - 红色虚线标记阈值
  - 使用Times New Roman字体

## 示例输出

### 热力图特点：
- **尖锐边清晰可见**：使用粗线（3.0px）和完全透明度突出显示
- **等轴显示**：保持模型真实比例，无扭曲
- **颜色编码**（0°~360°）：
  - 蓝色（0°）：完全共面的相邻面
  - 绿色（~180°）：垂直的相邻面
  - 橙色（270°）：立方体等90°拐角边界边
  - 红色（360°）：最大角度
- **Times New Roman字体**：所有标签和标题使用Times New Roman字体

### 立方体示例（阈值=45°）：
```
=== Processing Cube ===
Computing dihedral angles...
  Found 18 interior edges.
Detecting sharp edges (threshold = 45.0 deg)...
  Found 12 sharp edges.
Partitioning smooth regions...
  Partitioned into 6 smooth regions.
...
```

## 扩展与定制

### 修改阈值
调整 `--threshold` 参数可控制检测灵敏度：
- **较小阈值**（如20°）：检测更多细微特征
- **较大阈值**（如60°）：仅检测明显折痕

### 添加新算法
1. 在 `packages/` 中添加新模块
2. 在 `preprocessing.py` 中集成新函数
3. 在 `crease_identification.py` 中调用

### 支持其他网格格式
项目使用 `trimesh` 库，天然支持多种格式（PLY、STL、OFF等），修改文件扩展名检测即可。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交Issue和Pull Request：
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/awesome-feature`)
3. 提交更改 (`git commit -m 'Add awesome feature'`)
4. 推送到分支 (`git push origin feature/awesome-feature`)
5. 开启 Pull Request

## 致谢

- 使用 [trimesh](https://github.com/mikedh/trimesh) 进行网格处理
- 使用 [Matplotlib](https://matplotlib.org/) 进行可视化

---

**提示**：首次运行时，请确保已安装所有依赖包，并具有对输入文件的读取权限。