#!/usr/bin/env python
"""
Regions 可视化工具
用于可视化 3D 网格模型的各个 region，每个区域生成一个 PNG 图片
"""

import argparse
import os
import sys
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import csv

# 设置全局字体为Times
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

# Add project root to path to import packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def load_regions_from_csv(csv_path):
    """
    从 CSV 文件加载 region 信息
    
    Returns:
        regions: dict, key 为 region_id, value 为 face_index 列表
    """
    regions = {}
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            region_id = int(row['region_id'])
            face_idx = int(row['face_index'])
            if region_id not in regions:
                regions[region_id] = []
            regions[region_id].append(face_idx)
    return regions


def visualize_region(mesh, face_indices, region_id, output_path=None, 
                     highlight_edges=True, edge_color='red', edge_width=2.0):
    """
    可视化单个 region
    
    Args:
        mesh: Trimesh 对象（原始完整网格）
        face_indices: 该 region 包含的面片索引列表
        region_id: region 的 ID
        output_path: 输出图片路径
        highlight_edges: 是否高亮显示 region 的边界边
        edge_color: 边界边颜色
        edge_width: 边界边线宽
    """
    vertices = mesh.vertices
    faces = mesh.faces
    
    # 获取 region 的面片
    region_faces = faces[face_indices]
    
    # 计算 region 的顶点（用于设置视角范围）
    region_vertex_indices = np.unique(region_faces.flatten())
    region_vertices = vertices[region_vertex_indices]
    
    # 计算 region 的包围盒
    min_vals = region_vertices.min(axis=0)
    max_vals = region_vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    # 如果没有有效范围，使用整个网格的范围
    if max_range < 1e-6:
        min_vals = vertices.min(axis=0)
        max_vals = vertices.max(axis=0)
        mid = (min_vals + max_vals) / 2
        max_range = (max_vals - min_vals).max() / 2
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制整个网格的浅色线框作为背景
    ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                    triangles=faces, color=(0.9, 0.9, 0.9, 0.3), 
                    edgecolor='lightgray', linewidth=0.2, alpha=0.3, shade=False)
    
    # 绘制 region 的面片（使用醒目的颜色）
    # 使用 tab20 颜色映射来区分不同的 region
    color_map = plt.cm.tab20
    region_color = color_map(region_id % 20)
    
    ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                    triangles=region_faces, color=region_color, 
                    edgecolor='darkblue', linewidth=0.8, alpha=0.9, shade=True)
    
    # 如果需要，高亮显示 region 的边界边
    if highlight_edges:
        # 找到 region 的边界边
        boundary_edges = get_region_boundary_edges(mesh, face_indices)
        
        for edge in boundary_edges:
            v0 = vertices[edge[0]]
            v1 = vertices[edge[1]]
            ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                    color=edge_color, linewidth=edge_width, alpha=1.0)
    
    # 设置等比例
    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass
    
    # 设置视角范围（以 region 为中心）
    margin = max_range * 0.2  # 添加 20% 边距
    ax.set_xlim(mid[0] - max_range - margin, mid[0] + max_range + margin)
    ax.set_ylim(mid[1] - max_range - margin, mid[1] + max_range + margin)
    ax.set_zlim(mid[2] - max_range - margin, mid[2] + max_range + margin)
    
    # 设置标题
    ax.set_title(f'Region {region_id} ({len(face_indices)} faces)', fontsize=14, fontweight='bold')
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_zlabel('Z', fontsize=11)
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  Saved region {region_id} visualization to {output_path}")
    
    plt.close()


def visualize_region_4view(mesh, face_indices, region_id, output_path=None,
                           highlight_edges=True, edge_color='red', edge_width=2.0):
    """
    四视图可视化单个 region（正视图、俯视图、侧视图、等轴测视图）
    
    Args:
        mesh: Trimesh 对象（原始完整网格）
        face_indices: 该 region 包含的面片索引列表
        region_id: region 的 ID
        output_path: 输出图片路径
        highlight_edges: 是否高亮显示 region 的边界边
        edge_color: 边界边颜色
        edge_width: 边界边线宽
    """
    vertices = mesh.vertices
    faces = mesh.faces
    
    # 获取 region 的面片
    region_faces = faces[face_indices]
    
    # 计算 region 的顶点（用于设置视角范围）
    region_vertex_indices = np.unique(region_faces.flatten())
    region_vertices = vertices[region_vertex_indices]
    
    # 计算 region 的包围盒
    min_vals = region_vertices.min(axis=0)
    max_vals = region_vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    # 如果没有有效范围，使用整个网格的范围
    if max_range < 1e-6:
        min_vals = vertices.min(axis=0)
        max_vals = vertices.max(axis=0)
        mid = (min_vals + max_vals) / 2
        max_range = (max_vals - min_vals).max() / 2
    
    # 获取边界边
    boundary_edges = get_region_boundary_edges(mesh, face_indices) if highlight_edges else []
    
    # 创建颜色
    color_map = plt.cm.tab20
    region_color = color_map(region_id % 20)
    
    fig = plt.figure(figsize=(16, 12))
    
    # 定义四个视角
    views = [
        ('Front View (XY plane)', 0, -90),      # 正视图
        ('Top View (XZ plane)', 0, 0),          # 俯视图
        ('Side View (YZ plane)', 90, 0),        # 侧视图
        ('Isometric View', 30, 45),             # 等轴测视图
    ]
    
    for idx, (view_title, elev, azim) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, idx, projection='3d')
        
        # 绘制整个网格的浅色线框作为背景
        ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                        triangles=faces, color=(0.9, 0.9, 0.9, 0.3), 
                        edgecolor='lightgray', linewidth=0.15, alpha=0.25, shade=False)
        
        # 绘制 region 的面片
        ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                        triangles=region_faces, color=region_color, 
                        edgecolor='darkblue', linewidth=0.6, alpha=0.9, shade=True)
        
        # 高亮边界边
        if highlight_edges:
            for edge in boundary_edges:
                v0 = vertices[edge[0]]
                v1 = vertices[edge[1]]
                ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                        color=edge_color, linewidth=edge_width, alpha=1.0)
        
        # 设置等比例
        try:
            ax.set_box_aspect([1, 1, 1])
        except AttributeError:
            pass
        
        # 设置视角范围
        margin = max_range * 0.2
        ax.set_xlim(mid[0] - max_range - margin, mid[0] + max_range + margin)
        ax.set_ylim(mid[1] - max_range - margin, mid[1] + max_range + margin)
        ax.set_zlim(mid[2] - max_range - margin, mid[2] + max_range + margin)
        
        # 设置视角
        ax.view_init(elev=elev, azim=azim)
        
        ax.set_title(view_title, fontsize=12)
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z', fontsize=10)
    
    # 添加总标题
    fig.suptitle(f'Region {region_id} - 4 Views ({len(face_indices)} faces)', 
                 fontsize=14, fontweight='bold')
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  Saved region {region_id} 4-view visualization to {output_path}")
    
    plt.close()


def get_region_boundary_edges(mesh, face_indices):
    """
    获取 region 的边界边
    
    Args:
        mesh: Trimesh 对象
        face_indices: region 包含的面片索引列表
    
    Returns:
        boundary_edges: list of tuples，每个 tuple 是两个顶点索引
    """
    faces = mesh.faces
    
    # 构建边到面的映射
    edge_to_faces = {}
    
    for face_idx in face_indices:
        face = faces[face_idx]
        # 面片的三条边
        edges = [
            tuple(sorted([face[0], face[1]])),
            tuple(sorted([face[1], face[2]])),
            tuple(sorted([face[2], face[0]]))
        ]
        
        for edge in edges:
            if edge not in edge_to_faces:
                edge_to_faces[edge] = []
            edge_to_faces[edge].append(face_idx)
    
    # 边界边是只被一个 region 面片共享的边
    boundary_edges = [edge for edge, face_list in edge_to_faces.items() if len(face_list) == 1]
    
    return boundary_edges


def visualize_all_regions(mesh, regions, output_dir, mesh_name, mode='simple'):
    """
    可视化所有 regions，每个 region 生成一个 PNG 文件
    
    Args:
        mesh: Trimesh 对象
        regions: dict，key 为 region_id，value 为 face_index 列表
        output_dir: 输出目录
        mesh_name: 模型名称
        mode: 可视化模式，'simple' 或 '4view'
    """
    print(f"\nGenerating region visualizations for {mesh_name}...")
    print(f"  Total regions: {len(regions)}")
    print(f"  Output directory: {output_dir}")
    print(f"  Mode: {mode}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 为每个 region 生成可视化
    for region_id, face_indices in sorted(regions.items()):
        if mode == 'simple':
            output_path = os.path.join(output_dir, f"{mesh_name}_region_{region_id:03d}.png")
            visualize_region(mesh, face_indices, region_id, output_path, 
                           highlight_edges=True, edge_color='red', edge_width=2.5)
        elif mode == '4view':
            output_path = os.path.join(output_dir, f"{mesh_name}_region_{region_id:03d}_4view.png")
            visualize_region_4view(mesh, face_indices, region_id, output_path,
                                  highlight_edges=True, edge_color='red', edge_width=2.0)
    
    print(f"  Generated {len(regions)} region visualizations in {output_dir}")


def load_mesh(obj_path):
    """加载 OBJ 文件"""
    mesh = trimesh.load(obj_path, force='mesh')
    return mesh


def find_regions_csv(obj_path, regions_path=None, output_dir='output'):
    """
    自动查找 regions CSV 文件
    
    优先级：
    1. 如果提供了 regions_path，直接使用
    2. 尝试从 output/{模型名}/{模型名}_regions.csv 自动查找
    
    Args:
        obj_path: OBJ 文件路径
        regions_path: 手动指定的 regions CSV 路径（可选）
        output_dir: 默认的输出目录
    
    Returns:
        regions_csv_path: 找到的 CSV 文件路径
    """
    # 如果提供了路径，直接使用
    if regions_path and os.path.isfile(regions_path):
        return regions_path
    
    # 自动推导路径
    mesh_name = os.path.splitext(os.path.basename(obj_path))[0]
    auto_path = os.path.join(output_dir, mesh_name, f"{mesh_name}_regions.csv")
    
    if os.path.isfile(auto_path):
        return auto_path
    
    # 如果没找到，返回 None
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Visualize regions of 3D mesh models. Each region is saved as a separate PNG file.'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input OBJ file path')
    parser.add_argument('--regions', '-r', default=None,
                        help='Path to regions CSV file (optional, will auto-detect from output/{model}/)')
    parser.add_argument('--output-dir', '-d', default='output',
                        help='Output directory containing processed results (default: output)')
    parser.add_argument('--figures', '-f', default='figures',
                        help='Figures output directory (default: figures)')
    parser.add_argument('--mode', '-m', default='simple',
                        choices=['simple', '4view'],
                        help='Visualization mode: simple (default) or 4view')
    parser.add_argument('--no-edges', action='store_true',
                        help='Do not highlight boundary edges')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        sys.exit(1)
    
    mesh_name = os.path.splitext(os.path.basename(args.input))[0]
    
    # 查找 regions CSV 文件
    regions_csv = find_regions_csv(args.input, args.regions, args.output_dir)
    
    if not regions_csv:
        print(f"Error: Could not find regions CSV file.")
        print(f"  Tried: {os.path.join(args.output_dir, mesh_name, f'{mesh_name}_regions.csv')}")
        print(f"  Please run crease_identification.py first or specify --regions manually.")
        sys.exit(1)
    
    # 加载网格
    print(f"Loading mesh from {args.input}...")
    mesh = load_mesh(args.input)
    print(f"  Loaded mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    
    # 加载 regions
    print(f"\nLoading regions from {regions_csv}...")
    regions = load_regions_from_csv(regions_csv)
    print(f"  Loaded {len(regions)} regions")
    
    # 打印 region 统计信息
    for region_id, face_indices in sorted(regions.items()):
        print(f"    Region {region_id}: {len(face_indices)} faces")
    
    # 创建输出目录（figures/{mesh_name}/regions/）
    mesh_figures_dir = os.path.join(args.figures, mesh_name)
    regions_output_dir = os.path.join(mesh_figures_dir, 'regions')
    
    # 生成可视化
    highlight_edges = not args.no_edges
    if highlight_edges:
        print("\nBoundary edges will be highlighted in red")
    
    visualize_all_regions(mesh, regions, regions_output_dir, mesh_name, mode=args.mode)
    
    print(f"\nAll region visualizations saved to: {regions_output_dir}")
    print("Done!")


if __name__ == '__main__':
    main()
