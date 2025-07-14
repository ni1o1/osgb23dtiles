from setuptools import setup, find_packages, Distribution
import os
import platform

# 尝试导入wheel相关模块
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
    
    class bdist_wheel(_bdist_wheel):
        """
        自定义bdist_wheel类，强制创建平台特定的wheel
        """
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            # 强制创建平台特定的wheel（非pure Python）
            self.root_is_pure = False
            
        def get_tag(self):
            # 获取平台特定的标签
            python, abi, plat = _bdist_wheel.get_tag(self)
            # 确保使用当前平台的标签
            return python, abi, plat
            
except ImportError:
    # 如果wheel未安装，使用默认的None
    bdist_wheel = None


class BinaryDistribution(Distribution):
    """
    自定义Distribution类，强制setuptools认为这是一个二进制分发包
    """
    def has_ext_modules(self):
        # 返回True使setuptools认为这个包包含扩展模块
        return True


def get_package_data():
    """
    根据当前系统架构动态确定要打包的库文件
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    package_data = {'osgb23dtiles': []}
    
    if system == 'darwin':  # macOS
        # 检查实际系统架构
        import subprocess
        try:
            arch_result = subprocess.check_output(['arch'], text=True).strip()
        except:
            arch_result = machine
            
        if arch_result == 'arm64' or 'arm' in machine or 'aarch64' in machine:
            # ARM64 架构
            package_data['osgb23dtiles'] = ['libs/libthreedtiles_lib_arm64.dylib']
        else:
            # x86_64 架构
            package_data['osgb23dtiles'] = ['libs/libthreedtiles_lib_x86_64.dylib']
    elif system == 'linux':
        # Linux 系统
        package_data['osgb23dtiles'] = ['libs/libthreedtiles_lib.so']
    elif system == 'windows':
        # Windows 系统，包含所有 Windows 库文件
        package_data['osgb23dtiles'] = ['libs/windows_lib/*']
    else:
        # 默认包含所有库文件
        package_data['osgb23dtiles'] = ['libs/*', 'libs/windows_lib/*']
    
    return package_data


def get_cmdclass():
    """
    获取命令类字典
    """
    cmdclass = {}
    if bdist_wheel is not None:
        cmdclass['bdist_wheel'] = bdist_wheel
    return cmdclass

setup(
    name='osgb23dtiles',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=False,  # 使用 package_data 而不是 include_package_data
    package_data=get_package_data(),
    install_requires=[
        'numpy',
        'pyproj',
    ],
    extras_require={
        'test': [
            'pytest>=6.0',
            'pytest-cov',
        ],
        'dev': [
            'pytest>=6.0',
            'pytest-cov',
            'twine',
            'build',
            'wheel',
        ],
    },
    author='ni1o1',
    author_email='714727644@qq.com',
    description='A package to convert OSGB to 3D Tiles',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/ni1o1/osgb23dtiles',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    # 添加自定义类以支持平台特定的wheel构建
    distclass=BinaryDistribution,
    cmdclass=get_cmdclass(),
)