#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OSGB到GLB转换功能

标准的pytest测试文件，遵循Python包测试最佳实践。
"""

import os
import sys
import pytest
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from osgb23dtiles import osgb_to_glb


class TestOSGBConversion:
    """OSGB转换功能测试类"""
    
    @pytest.fixture
    def test_data_dir(self):
        """测试数据目录fixture"""
        return project_root / "data" / "test"
    
    @pytest.fixture
    def input_file(self, test_data_dir):
        """输入文件fixture"""
        return test_data_dir / "test.osgb"
    
    @pytest.fixture
    def output_file(self, test_data_dir, tmp_path):
        """输出文件fixture，使用临时目录"""
        return tmp_path / "test_output.glb"
    
    def test_input_file_exists(self, input_file):
        """测试输入文件是否存在"""
        assert input_file.exists(), f"输入文件不存在: {input_file}"
        assert input_file.is_file(), f"输入路径不是文件: {input_file}"
        assert input_file.suffix.lower() == '.osgb', f"输入文件不是OSGB格式: {input_file}"
    
    def test_osgb_to_glb_conversion(self, input_file, output_file):
        """测试OSGB到GLB转换功能"""
        # 跳过测试如果输入文件不存在
        if not input_file.exists():
            pytest.skip(f"测试文件不存在: {input_file}")
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 执行转换
        try:
            osgb_to_glb(str(input_file), str(output_file))
        except Exception as e:
            pytest.fail(f"转换过程中发生错误: {e}")
        
        # 验证输出文件
        assert output_file.exists(), "转换后未生成输出文件"
        assert output_file.is_file(), "输出路径不是文件"
        assert output_file.stat().st_size > 0, "输出文件为空"
        assert output_file.suffix.lower() == '.glb', "输出文件不是GLB格式"
    
    def test_osgb_to_glb_with_nonexistent_input(self, tmp_path):
        """测试使用不存在的输入文件"""
        nonexistent_input = tmp_path / "nonexistent.osgb"
        output_file = tmp_path / "output.glb"
        
        with pytest.raises(Exception):
            osgb_to_glb(str(nonexistent_input), str(output_file))
    
    def test_osgb_to_glb_with_invalid_output_dir(self, input_file):
        """测试使用无效的输出目录"""
        if not input_file.exists():
            pytest.skip(f"测试文件不存在: {input_file}")
        
        # 使用一个不可写的路径（如果存在的话）
        invalid_output = Path("/invalid/path/output.glb")
        
        with pytest.raises(Exception):
            osgb_to_glb(str(input_file), str(invalid_output))


def test_package_import():
    """测试包导入功能"""
    try:
        import osgb23dtiles
        assert hasattr(osgb23dtiles, 'osgb_to_glb'), "osgb_to_glb函数不存在"
    except ImportError as e:
        pytest.fail(f"无法导入osgb23dtiles包: {e}")


if __name__ == "__main__":
    # 支持直接运行测试文件
    pytest.main([__file__, "-v"])