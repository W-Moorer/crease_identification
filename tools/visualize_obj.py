#!/usr/bin/env python
"""
OBJ模型可视化工具
用于可视化3D网格模型，支持多种显示模式
"""

import argparse
import os
import sys
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 设置全局字体为Times
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

# Add project root to path to import packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def load_mesh(obj_path):
    """加载OBJ文件"""
    mesh = trimesh.load(obj_path, force='mesh')
    return mesh


def visualize_mesh_simple(mesh, output_path=None, title=None):
    """
    简单可视化网格模型（仅显示线框）
    
    Args:
        mesh: Trimesh对象
        output_path: 输出图片路径（可选）
        title: 图表标题（可选）
    """
    vertices = mesh.vertices
    
    # 计算等比例范围
    min_vals = vertices.min(axis=0)
    max_vals = vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制网格表面
    ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                    triangles=mesh.faces, color='lightgray', 
                    edgecolor='darkblue', linewidth=0.5, alpha=0.8)
    
    # 设置等比例
    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass
    
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
    
    if title:
        ax.set_title(title, fontsize=14)
    else:
        ax.set_title('Mesh Visualization', fontsize=14)
    
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_zlabel('Z', fontsize=11)
    
    if output_path:
        plt.savefig(output_path, dpi=600, bbox_inches='tight')
        print(f"Saved visualization to {output_path}")
    else:
        plt.show()
    
    plt.close()


def visualize_mesh_4view(mesh, output_path=None, title=None):
    """
    四视图可视化网格模型（正视图、俯视图、侧视图、等轴测视图）
    
    Args:
        mesh: Trimesh对象
        output_path: 输出图片路径（可选）
        title: 图表标题（可选）
    """
    vertices = mesh.vertices
    
    # 计算等比例范围
    min_vals = vertices.min(axis=0)
    max_vals = vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
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
        
        # 绘制网格表面
        ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                        triangles=mesh.faces, color='lightgray', 
                        edgecolor='darkblue', linewidth=0.5, alpha=0.8)
        
        # 设置等比例
        try:
            ax.set_box_aspect([1, 1, 1])
        except AttributeError:
            pass
        
        ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
        ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
        ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
        
        # 设置视角
        ax.view_init(elev=elev, azim=azim)
        
        ax.set_title(view_title, fontsize=12)
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z', fontsize=10)
    
    # 添加总标题
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    else:
        fig.suptitle('Mesh Visualization - 4 Views', fontsize=14, fontweight='bold')
    
    if output_path:
        plt.savefig(output_path, dpi=600, bbox_inches='tight')
        print(f"Saved 4-view visualization to {output_path}")
    else:
        plt.show()
    
    plt.close()


def visualize_mesh_with_edges(mesh, output_path=None, title=None, edge_color='red', edge_width=2.0):
    """
    可视化网格模型并高亮显示边
    
    Args:
        mesh: Trimesh对象
        output_path: 输出图片路径（可选）
        title: 图表标题（可选）
        edge_color: 边的颜色
        edge_width: 边的线宽
    """
    vertices = mesh.vertices
    edges = mesh.edges_unique
    
    # 计算等比例范围
    min_vals = vertices.min(axis=0)
    max_vals = vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制网格表面（浅色背景）
    ax.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2],
                    triangles=mesh.faces, color=(1, 1, 1, 0.1), 
                    edgecolor='lightgray', linewidth=0.2, shade=False)
    
    # 绘制所有边
    for edge in edges:
        v0 = vertices[edge[0]]
        v1 = vertices[edge[1]]
        ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                color=edge_color, linewidth=edge_width, alpha=0.8)
    
    # 设置等比例
    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass
    
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
    
    if title:
        ax.set_title(title, fontsize=14)
    else:
        ax.set_title(f'Mesh with Edges ({len(edges)} edges)', fontsize=14)
    
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_zlabel('Z', fontsize=11)
    
    if output_path:
        plt.savefig(output_path, dpi=600, bbox_inches='tight')
        print(f"Saved visualization to {output_path}")
    else:
        plt.show()
    
    plt.close()


def print_mesh_info(mesh, mesh_name="Mesh"):
    """打印网格信息"""
    print(f"\n=== {mesh_name} Information ===")
    print(f"  Vertices: {len(mesh.vertices)}")
    print(f"  Faces: {len(mesh.faces)}")
    print(f"  Edges: {len(mesh.edges_unique)}")
    
    # 计算包围盒
    min_vals = mesh.vertices.min(axis=0)
    max_vals = mesh.vertices.max(axis=0)
    print(f"  Bounding Box:")
    print(f"    Min: ({min_vals[0]:.2f}, {min_vals[1]:.2f}, {min_vals[2]:.2f})")
    print(f"    Max: ({max_vals[0]:.2f}, {max_vals[1]:.2f}, {max_vals[2]:.2f})")
    
    # 检查是否为封闭网格
    is_watertight = mesh.is_watertight
    print(f"  Watertight: {is_watertight}")
    
    # 计算表面积和体积（如果是封闭网格）
    print(f"  Surface Area: {mesh.area:.2f}")
    if is_watertight:
        print(f"  Volume: {mesh.volume:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize 3D mesh models from OBJ files.'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input OBJ file path')
    parser.add_argument('--output', '-o',
                        help='Output image path (optional, if not provided will display interactively)')
    parser.add_argument('--mode', '-m', default='simple',
                        choices=['simple', '4view', 'edges'],
                        help='Visualization mode: simple (default), 4view, or edges')
    parser.add_argument('--title', '-t',
                        help='Custom title for the visualization')
    parser.add_argument('--info', action='store_true',
                        help='Print mesh information')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.isfile(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        sys.exit(1)
    
    if not args.input.lower().endswith('.obj'):
        print(f"Error: Input file must be an OBJ file.")
        sys.exit(1)
    
    # 加载网格
    print(f"Loading mesh from {args.input}...")
    mesh = load_mesh(args.input)
    mesh_name = os.path.splitext(os.path.basename(args.input))[0]
    
    # 打印网格信息
    if args.info:
        print_mesh_info(mesh, mesh_name)
    
    # 设置标题
    title = args.title if args.title else f'{mesh_name} Visualization'
    
    # 根据模式进行可视化
    print(f"Generating {args.mode} visualization...")
    
    if args.mode == 'simple':
        visualize_mesh_simple(mesh, output_path=args.output, title=title)
    elif args.mode == '4view':
        visualize_mesh_4view(mesh, output_path=args.output, title=title)
    elif args.mode == 'edges':
        visualize_mesh_with_edges(mesh, output_path=args.output, title=title)
    
    print("Done!")


if __name__ == '__main__':
    main()
