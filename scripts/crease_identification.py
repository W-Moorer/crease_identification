#!/usr/bin/env python
"""
Main script for crease identification in 3D mesh models.
Detects sharp edges based on dihedral angle threshold, partitions smooth regions,
and generates visualizations and statistics.
"""

import argparse
import os
import sys
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import json
import csv

# 设置全局字体为Times
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

# Add project root to path to import packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from packages.topology.preprocessing import (
    compute_dihedral_angles,
    detect_sharp_edges,
    segment_smooth_regions,
    MeshPreprocessor
)

def load_mesh(obj_path):
    """Load a mesh from OBJ file."""
    mesh = trimesh.load(obj_path, force='mesh')
    # Mesh is assumed to be triangular (OBJ format)
    return mesh

def process_single_mesh(mesh, theta0_deg, output_dir, figures_dir, mesh_name):
    """Process a single mesh and generate outputs."""
    print(f"\n=== Processing {mesh_name} ===")
    
    # Create subdirectories for this mesh
    mesh_output_dir = os.path.join(output_dir, mesh_name)
    os.makedirs(mesh_output_dir, exist_ok=True)
    
    # Create subdirectory in figures directory
    mesh_figures_dir = os.path.join(figures_dir, mesh_name)
    os.makedirs(mesh_figures_dir, exist_ok=True)
    
    # 1. Compute dihedral angles for all interior edges
    print("Computing dihedral angles...")
    dihedral_angles = compute_dihedral_angles(mesh.vertices, mesh.faces)
    print(f"  Found {len(dihedral_angles)} interior edges.")
    
    # 2. Detect sharp edges using threshold
    print(f"Detecting sharp edges (threshold = {theta0_deg} deg)...")
    sharp_edges = detect_sharp_edges(mesh.vertices, mesh.faces, theta0_deg)
    print(f"  Found {len(sharp_edges)} sharp edges.")
    
    # 3. Partition smooth regions
    print("Partitioning smooth regions...")
    regions = segment_smooth_regions(mesh.faces, sharp_edges)
    print(f"  Partitioned into {len(regions)} smooth regions.")
    
    # 4. Generate dihedral angle heatmap visualization
    print("Generating dihedral angle heatmap...")
    heatmap_path = os.path.join(mesh_figures_dir, f"{mesh_name}_dihedral_heatmap.png")
    create_dihedral_heatmap(mesh, dihedral_angles, sharp_edges, heatmap_path, theta0_deg)
    
    # 4b. Generate dihedral angle heatmap 4-view visualization
    print("Generating dihedral angle heatmap 4-view...")
    heatmap_4view_path = os.path.join(mesh_figures_dir, f"{mesh_name}_dihedral_heatmap_4view.png")
    create_dihedral_heatmap_4view(mesh, dihedral_angles, sharp_edges, heatmap_4view_path, theta0_deg)
    
    # 5. Generate statistics and plots
    print("Generating statistics and plots...")
    stats_path = os.path.join(mesh_output_dir, f"{mesh_name}_statistics.json")
    plot_path = os.path.join(mesh_figures_dir, f"{mesh_name}_dihedral_histogram.png")
    generate_statistics(dihedral_angles, sharp_edges, regions, stats_path, plot_path, theta0_deg)
    
    # 6. Export sharp edges information
    print("Exporting sharp edges information...")
    sharp_edges_path = os.path.join(mesh_output_dir, f"{mesh_name}_sharp_edges.csv")
    export_sharp_edges(sharp_edges, dihedral_angles, sharp_edges_path)
    
    # 7. Export region information
    print("Exporting region information...")
    regions_path = os.path.join(mesh_output_dir, f"{mesh_name}_regions.csv")
    export_regions(regions, mesh.faces, regions_path)
    
    print(f"\nData outputs saved to: {mesh_output_dir}")
    print(f"Figure outputs saved to: {mesh_figures_dir}")
    return {
        'mesh_name': mesh_name,
        'num_vertices': len(mesh.vertices),
        'num_faces': len(mesh.faces),
        'num_interior_edges': len(dihedral_angles),
        'num_sharp_edges': len(sharp_edges),
        'num_regions': len(regions),
        'output_dir': mesh_output_dir,
        'figures_dir': mesh_figures_dir
    }

def create_dihedral_heatmap(mesh, dihedral_angles, sharp_edges, output_path, theta0_deg):
    """
    Create a heatmap visualization of dihedral angles on the mesh.
    Colors edges based on their dihedral angle value, with sharp edges highlighted.
    
    Args:
        mesh: Trimesh object
        dihedral_angles: Dictionary mapping edge (v1, v2) to angle in degrees
        sharp_edges: Set of edges that are considered sharp (angle >= threshold)
        output_path: Path to save the visualization
        theta0_deg: Threshold angle in degrees
    """
    # Debug flag
    debug = True
    
    if debug:
        angles_list = list(dihedral_angles.values())
        if angles_list:
            print(f"  Dihedral angles stats: min={np.min(angles_list):.2f}, max={np.max(angles_list):.2f}, mean={np.mean(angles_list):.2f}")
            # Count sharp edges in dihedral_angles
            sharp_in_dihedral = sum(1 for edge in sharp_edges if edge in dihedral_angles)
            print(f"  Sharp edges in dihedral_angles: {sharp_in_dihedral}/{len(sharp_edges)}")
        else:
            print("  Dihedral angles dictionary is empty")
    
    # Create a custom colormap: blue (small angle) -> green -> red (large angle)
    colors = [(0, 0, 1), (0, 1, 0), (1, 0, 0)]  # blue, green, red
    cmap = LinearSegmentedColormap.from_list('dihedral', colors, N=256)
    
    # Get edges from mesh (unique edges)
    edges = mesh.edges_unique
    
    # Create a mapping from edge tuple to index in edges array (normalized)
    edge_to_index = {tuple(sorted(edge)): i for i, edge in enumerate(edges)}
    
    # Assign angle values to each edge, default NaN for non-interior edges
    angle_values = np.full(len(edges), np.nan)
    for edge, angle in dihedral_angles.items():
        idx = edge_to_index.get(edge)
        if idx is not None:
            angle_values[idx] = angle
    
    if debug:
        # Edge mapping check
        found = 0
        not_found = 0
        for edge in sharp_edges:
            idx = edge_to_index.get(edge)
            if idx is None:
                not_found += 1
            else:
                found += 1
        print(f"  Edge mapping: {found} sharp edges found in mapping, {not_found} not found")
        
        # Check a few sharp edges after assignment
        print(f"  Checking first 5 sharp edges after assignment:")
        for i, edge in enumerate(list(sharp_edges)[:5]):
            idx = edge_to_index.get(edge)
            if idx is None:
                print(f"    Edge {edge} not found in edge_to_index")
            else:
                print(f"    Edge {edge}: angle={angle_values[idx]:.2f}")
    
    # Calculate equal aspect ratio for 3D axes
    vertices = mesh.vertices
    min_vals = vertices.min(axis=0)
    max_vals = vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    # Create visualization
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot mesh wireframe (light background)
    ax.plot_trisurf(vertices[:,0], vertices[:,1], vertices[:,2],
                    triangles=mesh.faces, color=(1, 1, 1, 0.05), 
                    edgecolor='lightgray', linewidth=0.2, shade=False)
    
    # Separate sharp and smooth edges
    sharp_edge_indices = []
    smooth_edge_indices = []
    
    for i, edge in enumerate(edges):
        edge_tuple = tuple(edge)
        if edge_tuple in sharp_edges:
            sharp_edge_indices.append(i)
        elif not np.isnan(angle_values[i]):
            smooth_edge_indices.append(i)
    
    # Plot smooth edges first (thinner lines)
    if smooth_edge_indices:
        smooth_edges = edges[smooth_edge_indices]
        smooth_angles = angle_values[smooth_edge_indices]
        norm_smooth = np.clip(smooth_angles / 360.0, 0, 1)
        smooth_colors = cmap(norm_smooth)
        
        for edge, color in zip(smooth_edges, smooth_colors):
            v0 = vertices[edge[0]]
            v1 = vertices[edge[1]]
            ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                    color=color, linewidth=1.5, alpha=0.7, zorder=1)
    
    # Plot sharp edges on top (thicker lines, more visible)
    if sharp_edge_indices:
        sharp_edges_array = edges[sharp_edge_indices]
        sharp_angles = angle_values[sharp_edge_indices]
        norm_sharp = np.clip(sharp_angles / 360.0, 0, 1)
        norm_sharp = np.nan_to_num(norm_sharp, nan=1.0)  # 将NaN替换为1.0（红色）
        sharp_colors = cmap(norm_sharp)
        
        if debug:
            print(f"  Sharp edges debugging: total {len(sharp_angles)} edges")
            print(f"  Sharp angles min: {np.nanmin(sharp_angles):.2f}, max: {np.nanmax(sharp_angles):.2f}")
            print(f"  Norm sharp min: {np.nanmin(norm_sharp):.3f}, max: {np.nanmax(norm_sharp):.3f}")
            # Print first few angles and corresponding colors
            for i in range(min(5, len(sharp_angles))):
                print(f"    Edge {i}: angle={sharp_angles[i]:.2f}, norm={norm_sharp[i]:.3f}, color={sharp_colors[i]}")
        
        for edge, color in zip(sharp_edges_array, sharp_colors):
            v0 = vertices[edge[0]]
            v1 = vertices[edge[1]]
            ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                    color=color, linewidth=3.0, alpha=1.0, zorder=2)
    
    # Set equal aspect ratio for all axes
    try:
        ax.set_box_aspect([1, 1, 1])
    except AttributeError:
        pass
    
    # Set axis limits to ensure equal scaling
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=360))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.8, pad=0.1)
    cbar.set_label('Dihedral Angle (degrees)', fontsize=12)
    
    # Mark threshold line on colorbar
    cbar.ax.axhline(theta0_deg / 360.0, color='black', linestyle='--', linewidth=2,
                    label=f'Threshold ({theta0_deg}°)')
    
    ax.set_title(f'Dihedral Angle Heatmap (Threshold = {theta0_deg}°)', fontsize=14)
    ax.set_xlabel('X', fontsize=11)
    ax.set_ylabel('Y', fontsize=11)
    ax.set_zlabel('Z', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved heatmap to {output_path}")


def create_dihedral_heatmap_4view(mesh, dihedral_angles, sharp_edges, output_path, theta0_deg):
    """
    创建热力图的四视图可视化（正视图、俯视图、侧视图、等轴测视图）。
    
    Args:
        mesh: Trimesh object
        dihedral_angles: Dictionary mapping edge (v1, v2) to angle in degrees
        sharp_edges: Set of edges that are considered sharp (angle >= threshold)
        output_path: Path to save the visualization
        theta0_deg: Threshold angle in degrees
    """
    # 创建自定义颜色映射：蓝色（小角度）-> 绿色 -> 红色（大角度）
    colors = [(0, 0, 1), (0, 1, 0), (1, 0, 0)]  # blue, green, red
    cmap = LinearSegmentedColormap.from_list('dihedral', colors, N=256)
    
    # 获取网格边
    edges = mesh.edges_unique
    
    # 创建边到索引的映射
    edge_to_index = {tuple(sorted(edge)): i for i, edge in enumerate(edges)}
    
    # 为每条边分配角度值
    angle_values = np.full(len(edges), np.nan)
    for edge, angle in dihedral_angles.items():
        idx = edge_to_index.get(edge)
        if idx is not None:
            angle_values[idx] = angle
    
    # 获取顶点
    vertices = mesh.vertices
    
    # 计算坐标范围
    min_vals = vertices.min(axis=0)
    max_vals = vertices.max(axis=0)
    mid = (min_vals + max_vals) / 2
    max_range = (max_vals - min_vals).max() / 2
    
    # 分离锐利边和平滑边
    sharp_edge_indices = []
    smooth_edge_indices = []
    
    for i, edge in enumerate(edges):
        edge_tuple = tuple(edge)
        if edge_tuple in sharp_edges:
            sharp_edge_indices.append(i)
        elif not np.isnan(angle_values[i]):
            smooth_edge_indices.append(i)
    
    # 创建四视图图形
    fig = plt.figure(figsize=(16, 12))
    
    # 定义四个视角
    views = [
        ('Front View (XY plane)', 0, -90),      # 正视图
        ('Top View (XZ plane)', 0, 0),          # 俯视图
        ('Side View (YZ plane)', 90, 0),        # 侧视图
        ('Isometric View', 30, 45),             # 等轴测视图
    ]
    
    for idx, (title, elev, azim) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, idx, projection='3d')
        
        # 绘制网格线框
        ax.plot_trisurf(vertices[:,0], vertices[:,1], vertices[:,2],
                        triangles=mesh.faces, color=(1, 1, 1, 0.05), 
                        edgecolor='lightgray', linewidth=0.2, shade=False)
        
        # 绘制平滑边
        if smooth_edge_indices:
            smooth_edges = edges[smooth_edge_indices]
            smooth_angles = angle_values[smooth_edge_indices]
            norm_smooth = np.clip(smooth_angles / 360.0, 0, 1)
            smooth_colors = cmap(norm_smooth)
            
            for edge, color in zip(smooth_edges, smooth_colors):
                v0 = vertices[edge[0]]
                v1 = vertices[edge[1]]
                ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                        color=color, linewidth=1.5, alpha=0.7, zorder=1)
        
        # 绘制锐利边
        if sharp_edge_indices:
            sharp_edges_array = edges[sharp_edge_indices]
            sharp_angles = angle_values[sharp_edge_indices]
            norm_sharp = np.clip(sharp_angles / 360.0, 0, 1)
            norm_sharp = np.nan_to_num(norm_sharp, nan=1.0)
            sharp_colors = cmap(norm_sharp)
            
            for edge, color in zip(sharp_edges_array, sharp_colors):
                v0 = vertices[edge[0]]
                v1 = vertices[edge[1]]
                ax.plot([v0[0], v1[0]], [v0[1], v1[1]], [v0[2], v1[2]],
                        color=color, linewidth=3.0, alpha=1.0, zorder=2)
        
        # 设置等比例
        try:
            ax.set_box_aspect([1, 1, 1])
        except AttributeError:
            pass
        
        # 设置坐标范围
        ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
        ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
        ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
        
        # 设置视角
        ax.view_init(elev=elev, azim=azim)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_zlabel('Z', fontsize=10)
    
    # 添加总标题
    fig.suptitle(f'Dihedral Angle Heatmap - 4 Views (Threshold = {theta0_deg}°)', 
                 fontsize=14, fontweight='bold')
    
    # 添加共享的颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=360))
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Dihedral Angle (degrees)', fontsize=11)
    cbar.ax.axhline(theta0_deg / 360.0, color='black', linestyle='--', linewidth=2,
                    label=f'Threshold ({theta0_deg}°)')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved 4-view heatmap to {output_path}")

def generate_statistics(dihedral_angles, sharp_edges, regions, stats_path, plot_path, theta0_deg):
    """
    Generate statistics and histogram of dihedral angles.
    """
    # Collect angles
    angles = list(dihedral_angles.values())
    
    # Basic statistics
    stats = {
        'theta0_threshold_deg': theta0_deg,
        'num_interior_edges': len(dihedral_angles),
        'num_sharp_edges': len(sharp_edges),
        'num_smooth_regions': len(regions),
        'region_sizes': [len(r) for r in regions],
        'dihedral_angle_min': float(np.min(angles)) if angles else 0.0,
        'dihedral_angle_max': float(np.max(angles)) if angles else 0.0,
        'dihedral_angle_mean': float(np.mean(angles)) if angles else 0.0,
        'dihedral_angle_median': float(np.median(angles)) if angles else 0.0,
        'dihedral_angle_std': float(np.std(angles)) if angles else 0.0,
        'sharp_edge_percentage': (len(sharp_edges) / len(dihedral_angles) * 100) if dihedral_angles else 0.0
    }
    
    # Save statistics as JSON
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"  Saved statistics to {stats_path}")
    
    # Generate histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if angles:
        ax.hist(angles, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
        ax.axvline(theta0_deg, color='red', linestyle='--', linewidth=2, label=f'Threshold ({theta0_deg}°)')
        
        # Add vertical line at 360 degrees (maximum possible)
        ax.axvline(360, color='gray', linestyle=':', linewidth=1)
        
        # Annotate statistics
        text = f"""Total edges: {stats['num_interior_edges']}
Sharp edges: {stats['num_sharp_edges']}
Sharp percentage: {stats['sharp_edge_percentage']:.1f}%
Mean angle: {stats['dihedral_angle_mean']:.1f}°
Median angle: {stats['dihedral_angle_median']:.1f}°"""
        
        ax.text(0.98, 0.98, text, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.set_xlabel('Dihedral Angle (degrees)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Distribution of Dihedral Angles', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"  Saved histogram to {plot_path}")

def export_sharp_edges(sharp_edges, dihedral_angles, output_path):
    """Export sharp edges information to CSV file."""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['vertex1', 'vertex2', 'dihedral_angle_deg', 'is_sharp'])
        
        # Write all interior edges
        for edge, angle in dihedral_angles.items():
            is_sharp = edge in sharp_edges
            writer.writerow([edge[0], edge[1], angle, is_sharp])
    
    print(f"  Saved sharp edges to {output_path}")

def export_regions(regions, faces, output_path):
    """Export region information to CSV file."""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['region_id', 'face_index', 'vertex1', 'vertex2', 'vertex3'])
        
        for region_id, face_indices in enumerate(regions):
            for face_idx in face_indices:
                face = faces[face_idx]
                writer.writerow([region_id, face_idx, face[0], face[1], face[2]])
    
    print(f"  Saved region information to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Identify creases in 3D mesh models based on dihedral angle threshold.'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input OBJ file or directory containing OBJ files')
    parser.add_argument('--threshold', '-t', type=float, default=45.0,
                        help='Dihedral angle threshold in degrees (default: 45.0)')
    parser.add_argument('--output', '-o', default='output',
                        help='Output directory (default: output)')
    parser.add_argument('--figures', '-f', default='figures',
                        help='Directory for figure outputs (default: figures)')
    
    args = parser.parse_args()
    
    # Create output directories
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.figures, exist_ok=True)
    
    # Collect all OBJ files to process
    obj_files = []
    
    if os.path.isfile(args.input) and args.input.lower().endswith('.obj'):
        obj_files.append(args.input)
    elif os.path.isdir(args.input):
        for root, dirs, files in os.walk(args.input):
            for file in files:
                if file.lower().endswith('.obj'):
                    obj_files.append(os.path.join(root, file))
    else:
        print(f"Error: Input path '{args.input}' is not a valid file or directory.")
        sys.exit(1)
    
    if not obj_files:
        print(f"No OBJ files found in '{args.input}'.")
        sys.exit(1)
    
    print(f"Found {len(obj_files)} OBJ file(s) to process.")
    print(f"Dihedral angle threshold: {args.threshold} degrees")
    
    # Process each mesh
    summary = []
    for obj_file in obj_files:
        mesh_name = os.path.splitext(os.path.basename(obj_file))[0]
        mesh = load_mesh(obj_file)
        
        # Process mesh
        result = process_single_mesh(
            mesh, args.threshold, args.output, args.figures, mesh_name
        )
        summary.append(result)
    
    # Generate overall summary
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    for res in summary:
        print(f"\n{res['mesh_name']}:")
        print(f"  Vertices: {res['num_vertices']}")
        print(f"  Faces: {res['num_faces']}")
        print(f"  Interior edges: {res['num_interior_edges']}")
        print(f"  Sharp edges: {res['num_sharp_edges']} ({res['num_sharp_edges']/res['num_interior_edges']*100:.1f}%)")
        print(f"  Smooth regions: {res['num_regions']}")
        print(f"  Output directory: {res['output_dir']}")
    
    # Save overall summary as JSON
    summary_path = os.path.join(args.output, 'processing_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nOverall summary saved to {summary_path}")
    
    print("\nAll processing completed successfully!")

if __name__ == '__main__':
    main()