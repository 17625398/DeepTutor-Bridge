#!/usr/bin/env python
"""
DeepTutor 后端生产环境打包脚本（Windows 内网部署专用）

功能：
1. 导出所有 Python 依赖
2. 打包后端源码和依赖列表
3. 生成启动脚本
4. 打包为 ZIP 压缩包，便于迁移到内网服务器
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "dist"
BACKEND_PROD_DIR = PROJECT_ROOT / "backend-prod"

MESSAGES = {
    "en": {
        "checking_python": "Checking Python environment ...",
        "python_missing": "Python not found. Please install Python 3.11+ and add it to PATH.",
        "exporting_deps": "Exporting Python dependencies ...",
        "export_failed": "Dependency export failed with exit code {code}.",
        "export_complete": "Dependencies exported successfully.",
        "copying_packages": "Copying Python packages from virtual environment ...",
        "copy_failed": "Package copy failed with exit code {code}.",
        "copy_complete": "Packages copied successfully.",
        "preparing_source": "Preparing backend source code ...",
        "creating_startup_scripts": "Creating startup scripts ...",
        "packaging": "Packaging backend files ...",
        "package_complete": "Package created: {path}",
        "all_done": "All done! Package is ready for deployment.",
    },
    "zh": {
        "checking_python": "正在检查 Python 环境 ...",
        "python_missing": "未找到 Python。请先安装 Python 3.11+ 并加入 PATH。",
        "exporting_deps": "正在导出 Python 依赖 ...",
        "export_failed": "依赖导出失败，退出码 {code}。",
        "export_complete": "依赖导出成功。",
        "copying_packages": "正在从虚拟环境复制 Python 依赖包 ...",
        "copy_failed": "依赖包复制失败，退出码 {code}。",
        "copy_complete": "依赖包复制成功。",
        "preparing_source": "正在准备后端源码 ...",
        "creating_startup_scripts": "正在创建启动脚本 ...",
        "packaging": "正在打包后端文件 ...",
        "package_complete": "压缩包已创建：{path}",
        "all_done": "全部完成！压缩包已准备好部署。",
    },
}


def _t(language: str, key: str, **kwargs) -> str:
    catalog = MESSAGES.get(language, MESSAGES["en"])
    template = catalog.get(key, MESSAGES["en"][key])
    return template.format(**kwargs)


def _check_python(language: str) -> str:
    """检查 Python 是否可用"""
    print(_t(language, "checking_python"))
    
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
        print(f"  {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  ERROR: {_t(language, 'python_missing')}")
        sys.exit(1)
    
    return sys.executable


def _export_dependencies(language: str) -> None:
    """导出 Python 依赖列表"""
    print(_t(language, "exporting_deps"))
    
    # 确保目录存在
    BACKEND_PROD_DIR.mkdir(parents=True, exist_ok=True)
    
    requirements_file = BACKEND_PROD_DIR / "requirements.txt"
    
    # 使用 pip freeze 导出当前环境的依赖
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
        shell=True,
    )
    
    if result.returncode != 0:
        print(f"  ERROR: {_t(language, 'export_failed', code=result.returncode)}")
        print(f"  stderr: {result.stderr}")
        sys.exit(result.returncode or 1)
    
    # 过滤掉本地开发路径的包
    lines = result.stdout.strip().split('\n')
    filtered_lines = [
        line for line in lines 
        if not line.startswith('-e') and 'deeptutor' not in line.lower()
    ]
    
    requirements_file.write_text('\n'.join(filtered_lines) + '\n', encoding='utf-8')
    print(f"  ✓ {_t(language, 'export_complete')}")
    print(f"    依赖文件：{requirements_file}")


def _copy_packages(language: str) -> None:
    """从虚拟环境复制所有依赖包到本地目录"""
    print(_t(language, "copying_packages"))
    
    packages_dir = BACKEND_PROD_DIR / "packages"
    
    # 获取 site-packages 目录列表
    result = subprocess.run(
        [sys.executable, "-c", "import site; print(';'.join(site.getsitepackages()))"],
        capture_output=True,
        text=True,
        check=True,
        shell=True,
    )
    
    # 查找包含 site-packages 的路径
    paths = result.stdout.strip().split(';')
    site_packages = None
    for p in paths:
        if 'site-packages' in p:
            site_packages = Path(p)
            break
    
    if not site_packages or not site_packages.exists():
        print(f"  ERROR: 找不到 site-packages 目录")
        print(f"  可用路径：{paths}")
        sys.exit(1)
    
    print(f"  site-packages 路径：{site_packages}")
    
    # 直接复制整个 site-packages 目录
    if packages_dir.exists():
        shutil.rmtree(packages_dir)
    shutil.copytree(site_packages, packages_dir)
    
    # 统计包数量
    package_count = len([d for d in packages_dir.iterdir() if d.is_dir() and not d.name.startswith('_')])
    print(f"  ✓ {_t(language, 'copy_complete')}")
    print(f"    复制了 {package_count} 个依赖包")
    print(f"    存储位置：{packages_dir}")


def _prepare_source(language: str) -> None:
    """准备后端源码"""
    print(_t(language, "preparing_source"))
    
    # 确保目录存在
    BACKEND_PROD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存 requirements.txt（如果存在）
    requirements_file = BACKEND_PROD_DIR / "requirements.txt"
    requirements_content = None
    if requirements_file.exists():
        requirements_content = requirements_file.read_text(encoding='utf-8')
    
    # 清理旧的源码目录（保留 requirements.txt 和 packages）
    for item in BACKEND_PROD_DIR.iterdir():
        if item.name not in ["requirements.txt", "packages"]:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    
    # 恢复 requirements.txt
    if requirements_content:
        requirements_file.write_text(requirements_content, encoding='utf-8')
    
    # 创建目录结构
    deeptutor_src = BACKEND_PROD_DIR / "deeptutor"
    deeptutor_cli_src = BACKEND_PROD_DIR / "deeptutor_cli"
    scripts_src = BACKEND_PROD_DIR / "scripts"
    
    deeptutor_src.mkdir(parents=True, exist_ok=True)
    deeptutor_cli_src.mkdir(parents=True, exist_ok=True)
    scripts_src.mkdir(parents=True, exist_ok=True)
    
    # 复制 deeptutor 核心代码
    source_deeptutor = PROJECT_ROOT / "deeptutor"
    if source_deeptutor.exists():
        shutil.copytree(source_deeptutor, deeptutor_src, dirs_exist_ok=True)
    
    # 复制 deeptutor_cli 代码
    source_cli = PROJECT_ROOT / "deeptutor_cli"
    if source_cli.exists():
        shutil.copytree(source_cli, deeptutor_cli_src, dirs_exist_ok=True)
    
    # 复制必要的脚本
    source_scripts = PROJECT_ROOT / "scripts"
    for script in ["start_web_prod.py", "stop_web_prod.py", "start_web.py"]:
        src = source_scripts / script
        if src.exists():
            shutil.copy2(src, scripts_src / script)
    
    # 复制配置文件
    for config_file in [".env.example", "pyproject.toml"]:
        src = PROJECT_ROOT / config_file
        if src.exists():
            shutil.copy2(src, BACKEND_PROD_DIR / config_file)
    
    print(f"  ✓ 源码准备完成")


def _create_startup_scripts(language: str, include_deps: bool = True) -> None:
    """创建启动脚本"""
    print(_t(language, "creating_startup_scripts"))
    
    if include_deps:
        install_step = (
            'echo Installing dependencies from local packages ...\n'
            'pip install --no-index --find-links=packages -r requirements.txt\n'
            'echo.\n'
        )
        install_step_sh = (
            'echo "Installing dependencies from local packages ..."\n'
            'pip install --no-index --find-links=packages -r requirements.txt\n'
            'echo ""\n'
        )
        install_md = (
            '2. Install dependencies (offline, no internet required):\n'
            '   ```bash\n'
            '   pip install --no-index --find-links=packages -r requirements.txt\n'
            '   ```\n\n'
        )
    else:
        install_step = 'echo Skipping dependency installation (no packages included).\n'
        install_step_sh = 'echo "Skipping dependency installation (no packages included)."\n'
        install_md = (
            '2. Install dependencies manually (requires internet or local packages):\n'
            '   ```bash\n'
            '   pip install -r requirements.txt\n'
            '   ```\n\n'
        )
    
    # 创建 Windows 启动脚本
    start_script = BACKEND_PROD_DIR / "start_backend.bat"
    start_script.write_text(
        '@echo off\n'
        'echo Starting DeepTutor Backend ...\n'
        'echo.\n'
        + install_step +
        'echo Starting backend server ...\n'
        'python -m uvicorn deeptutor.api.main:app --host 0.0.0.0 --port 8001 --log-level info\n',
        encoding='utf-8',
    )
    
    # 创建 Linux 启动脚本
    start_sh = BACKEND_PROD_DIR / "start_backend.sh"
    start_sh.write_text(
        '#!/bin/bash\n'
        'echo "Starting DeepTutor Backend ..."\n'
        'echo ""\n'
        + install_step_sh +
        'echo "Starting backend server ..."\n'
        'python -m uvicorn deeptutor.api.main:app --host 0.0.0.0 --port 8001 --log-level info\n',
        encoding='utf-8',
    )
    start_sh.chmod(0o755)
    
    # 创建安装说明
    install_md = BACKEND_PROD_DIR / "INSTALL.md"
    install_md.write_text(
        '# DeepTutor Backend Installation Guide\n\n'
        '## Prerequisites\n\n'
        '- Python 3.11 or higher\n'
        '- pip package manager\n\n'
        '## Installation Steps\n\n'
        '1. Extract the package to your desired location\n\n'
        + install_md +
        '3. Configure environment:\n'
        '   ```bash\n'
        '   cp .env.example .env\n'
        '   # Edit .env with your configuration\n'
        '   ```\n\n'
        '4. Start the backend:\n'
        '   ```bash\n'
        '   # Windows\n'
        '   start_backend.bat\n\n'
        '   # Linux/Mac\n'
        '   ./start_backend.sh\n'
        '   ```\n\n'
        '5. Access the API at http://localhost:8001\n',
        encoding='utf-8',
    )
    
    print(f"  ✓ 启动脚本创建完成")


def _create_zip_archive(language: str, output_path: Path) -> None:
    """创建 ZIP 压缩包"""
    print(_t(language, "packaging"))
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BACKEND_PROD_DIR):
            # 跳过 __pycache__ 目录
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                # 跳过 .pyc 文件
                if file.endswith('.pyc'):
                    continue
                    
                file_path = Path(root) / file
                arcname = file_path.relative_to(PROJECT_ROOT)
                zipf.write(file_path, arcname)
    
    print(f"  ✓ {_t(language, 'package_complete', path=output_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeepTutor 后端生产环境打包脚本（Windows 内网部署专用）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 ZIP 文件路径（默认：dist/backend-prod-<timestamp>.zip）",
    )
    parser.add_argument(
        "--lang",
        choices=("en", "zh"),
        default="zh",
        help="输出语言（默认：zh）",
    )
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖包的导出和打包（仅打包源码）",
    )
    args = parser.parse_args()
    
    language = args.lang
    
    # 检查 Python 环境
    _check_python(language)
    
    # 导出依赖
    if not args.skip_deps:
        _export_dependencies(language)
    
    # 准备源码
    _prepare_source(language)
    
    # 复制虚拟环境中的依赖包
    if not args.skip_deps:
        _copy_packages(language)
    
    # 创建启动脚本
    _create_startup_scripts(language, include_deps=not args.skip_deps)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"backend-prod-{timestamp}.zip"
    
    # 创建 ZIP 压缩包
    _create_zip_archive(language, output_path)
    
    print(f"\n✓ {_t(language, 'all_done')}")
    print(f"  压缩包路径: {output_path}")
    print(f"  压缩包大小: {output_path.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
