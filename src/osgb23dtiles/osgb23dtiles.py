import ctypes
import os
import sysconfig
import platform
import numpy as np
import pyproj
import xml.etree.ElementTree as ET
import math
import json

def _get_library_path():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    lib_dir = os.path.join(os.path.dirname(__file__), 'libs')
    
    if system == 'darwin':  # macOS
        # 检查实际系统架构
        import subprocess
        arch_result = subprocess.check_output(['arch'], text=True).strip()
        if arch_result == 'arm64' or 'arm' in machine or 'aarch64' in machine:
            return os.path.join(lib_dir, 'libthreedtiles_lib_arm64.dylib')
        else:
            return os.path.join(lib_dir, 'libthreedtiles_lib_x86_64.dylib')

    elif system == 'linux':
        return os.path.join(lib_dir, 'libthreedtiles_lib.so')
    elif system == 'windows':
        lib_path = os.path.join(lib_dir, 'windows_lib', 'lib3dtiles_cpp.dll')
        dll_dir = os.path.join(lib_dir, 'windows_lib')
        if dll_dir not in os.environ.get('PATH', ''):
            os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')
        return lib_path
    else:
        raise OSError(f"Unsupported platform: {system}")

def _get_run_func():
    lib_path = _get_library_path()
    try:
        if platform.system().lower() == 'windows':
            lib = ctypes.WinDLL(lib_path)
        else:
            lib = ctypes.CDLL(lib_path)
        print(f"成功加载库文件: {lib_path}")
    except OSError as e:
        print(f"错误: 无法加载库文件 '{lib_path}'.")
        raise

    # 定义函数原型
    lib.run_conversion.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, 
        ctypes.c_char_p, ctypes.c_char_p
    ]
    lib.run_conversion.restype = ctypes.c_int
    return lib.run_conversion


def _get_enu_to_ecef_transform(lon_deg, lat_deg, height_m, ecef_x, ecef_y, ecef_z):
    """
    在给定的经纬高和ECEF坐标处，计算一个ENU到ECEF的变换矩阵。
    这个矩阵可以将一个在ENU坐标系下的物体，正确地放置和定向到全局ECEF坐标系中。
    """
    lon_rad = math.radians(lon_deg)
    lat_rad = math.radians(lat_deg)

    # 计算ENU坐标系的三个正交基向量在ECEF坐标系中的表示
    # East vector
    east = np.array([-math.sin(lon_rad), math.cos(lon_rad), 0])
    
    # Up vector (normal to the ellipsoid)
    up = np.array([
        math.cos(lon_rad) * math.cos(lat_rad),
        math.sin(lon_rad) * math.cos(lat_rad),
        math.sin(lat_rad)
    ])
    
    # North vector (cross product of up and east)
    north = np.cross(up, east)

    # 创建4x4变换矩阵（列主元）
    # 旋转部分由East, North, Up向量组成
    # 平移部分是ECEF坐标
    transform = np.identity(4)
    transform[0, 0] = east[0]
    transform[1, 0] = east[1]
    transform[2, 0] = east[2]

    transform[0, 1] = north[0]
    transform[1, 1] = north[1]
    transform[2, 1] = north[2]

    transform[0, 2] = up[0]
    transform[1, 2] = up[1]
    transform[2, 2] = up[2]

    transform[0, 3] = ecef_x
    transform[1, 3] = ecef_y
    transform[2, 3] = ecef_z
    
    # 注意：在numpy中，我们通常按行思考，但3D Tiles是列主元。
    # 上面的填充方式是直接按列填充 (e.g., transform[:, 0] = east)。
    # 为了清晰，我们转置一下，按行填充，最后再转置回来。
    
    enu_matrix = np.identity(4)
    enu_matrix[0, :3] = east
    enu_matrix[1, :3] = north
    enu_matrix[2, :3] = up
    enu_matrix = enu_matrix.T # 转置得到旋转矩阵
    enu_matrix[3, :3] = [ecef_x, ecef_y, ecef_z]
    
    # 3D Tiles矩阵是列主元，Numpy默认是行主元。
    # 我们需要将平移放在第4行，然后转置。
    # 或者直接构建行主元矩阵，在最后输出时使用 flatten('F')
    
    final_enu_transform = np.identity(4)
    final_enu_transform[:3, 0] = east
    final_enu_transform[:3, 1] = north
    final_enu_transform[:3, 2] = up
    final_enu_transform[:3, 3] = [ecef_x, ecef_y, ecef_z]
    
    return final_enu_transform


def _calculate_correct_transform_v2(xml_data: str, original_model_transform: list) -> list:
    """
    根据XML和原始模型变换，计算正确的3D Tiles transform矩阵(V2)。
    这次会构建ENU矩阵来确保正确的朝向。
    """
    # 1. 解析XML
    root = ET.fromstring(xml_data)
    srs_code = root.find('SRS').text
    srs_origin_str = root.find('SRSOrigin').text
    srs_origin = [float(val) for val in srs_origin_str.split(',')]

    # 2. 创建坐标转换器
    source_crs = pyproj.CRS(srs_code)
    # 目标1: 地理坐标 (纬度/经度/高程)
    geodetic_crs = pyproj.CRS("EPSG:4979")
    # 目标2: 地心坐标 (ECEF)
    ecef_crs = pyproj.CRS("EPSG:4978")

    geo_transformer = pyproj.Transformer.from_crs(source_crs, geodetic_crs, always_xy=True)
    ecef_transformer = pyproj.Transformer.from_crs(source_crs, ecef_crs, always_xy=True)

    # 3. 进行坐标转换
    lon, lat, height = geo_transformer.transform(srs_origin[0], srs_origin[1], srs_origin[2])
    ecef_x, ecef_y, ecef_z = ecef_transformer.transform(srs_origin[0], srs_origin[1], srs_origin[2])

    # 4. 构建 ENU -> ECEF 变换矩阵
    enu_to_ecef_matrix = _get_enu_to_ecef_transform(lon, lat, height, ecef_x, ecef_y, ecef_z)

    # 7. 将最终的Numpy矩阵转回3D Tiles所需的列主元列表
    return enu_to_ecef_matrix.flatten(order='F').tolist()

def _update_transform(input_dir: str, output_dir: str):
    """
    自动处理指定目录，更新tileset.json的transform。

    参数:
        input_dir (str): 包含源数据和XML文件的目录路径。
        output_dir (str): 包含待更新的tileset.json的目录路径。
    """

    # 1. 在输入目录中查找XML文件
    xml_file_path = None
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.xml'):
            xml_file_path = os.path.join(input_dir, filename)
            #print(f"找到XML文件: {xml_file_path}")
            break
    
    if not xml_file_path:
        print(f"错误: 在目录 '{input_dir}' 中未找到XML文件。")
        return

    # 2. 确定并检查tileset.json文件路径
    tileset_path = os.path.join(output_dir, 'tileset.json')
    if not os.path.exists(tileset_path):
        print(f"错误: 在目录 '{output_dir}' 中未找到 'tileset.json' 文件。")
        return
    #print(f"找到tileset.json文件: {tileset_path}")

    try:
        # 3. 读取文件内容
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        with open(tileset_path, 'r', encoding='utf-8') as f:
            tileset_data = json.load(f)

        # 4. 提取旧的transform
        # 通常transform在根节点的'root'对象里
        if 'root' in tileset_data and 'transform' in tileset_data['root']:
            old_transform = tileset_data['root']['transform']
        else:
            print("错误: 'tileset.json' 文件中找不到 'root.transform'。请检查文件结构。")
            return

        # 5. 调用核心函数计算新的transform
        #print("正在根据XML信息计算新的变换矩阵...")
        new_transform = _calculate_correct_transform_v2(xml_content, old_transform)
        
        if not new_transform:
            print("错误: 计算新矩阵失败。")
            return
            
        #print("新矩阵计算成功！")
        # np.set_printoptions(suppress=True, precision=8)
        # print(np.array(new_transform))


        # 6. 更新json数据并写回文件
        tileset_data['root']['transform'] = new_transform
        
        with open(tileset_path, 'w', encoding='utf-8') as f:
            # indent=4 保持json文件格式美观
            # ensure_ascii=False 确保路径或内容中的中文等非ASCII字符能正确写入
            json.dump(tileset_data, f, indent=4, ensure_ascii=False)
        
        #print(f"\n成功！'{tileset_path}' 文件中的transform已更新。")

    except FileNotFoundError as e:
        print(f"文件未找到错误: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}。请检查 'tileset.json' 文件格式是否正确。")
    except Exception as e:
        print(f"发生未知错误: {e}")



def osgb_to_glb(input_osgb: str, output_glb: str, json_config: str  = None):
    """
    使用编译好的 Rust 动态库将单个 osgb 文件转换为 glb 文件。此功能目前仅支持macos

    Args:
        input_osgb (str): 输入的 .osgb 文件的路径。
        output_glb (str): 输出的 .glb 文件的路径。
        json_config (str | None, optional): 可选的 JSON 配置字符串。

    Returns:
        None: 此函数不返回任何值。但会在输出路径下生成glb文件
    """
    run_conversion_func = _get_run_func()
    # 3. 准备要传递给 C 函数的参数
    # 格式为 'gltf'，用于 osgb -> glb 的转换
    format_b = b"gltf"
    
    # 将 Python 的字符串路径编码为 C 语言可以理解的 bytes
    input_b = input_osgb.encode('utf-8')
    output_b = output_glb.encode('utf-8')

    # 如果提供了 JSON 配置，则编码；否则为 None (空指针)
    config_b = json_config.encode('utf-8') if json_config else None
    run_conversion_func(format_b, input_b, output_b, None, config_b)

def osgb_to_b3dm_3dtiles(input_dir: str, output_dir: str, json_config: str  = None):
    """
    使用动态库将 OSGB 数据集目录转换为 3D Tiles。此功能目前仅支持macos

    Args:
        lib (ctypes.CDLL): 已加载的库对象。
        input_dir (str): 输入的 OSGB 数据集根目录。
        output_dir (str): 输出 3D Tiles 的目录。
        json_config (str | None, optional): 可选的 JSON 配置字符串。

    Returns:
        None: 此函数不返回任何值。但会在输出目录下生成3dtiles
    """
    run_conversion_func = _get_run_func()
    format_b = b"osgb"
    input_b = input_dir.encode('utf-8')
    output_b = output_dir.encode('utf-8')
    
    # 如果提供了 JSON 配置，则编码；否则为 None (空指针)
    config_b = json_config.encode('utf-8') if json_config else None

    run_conversion_func(format_b, input_b, output_b, None, config_b)

    # 更新变换矩阵
    _update_transform(input_dir, output_dir)