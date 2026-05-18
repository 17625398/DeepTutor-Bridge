#!/usr/bin/env python
"""
DeepTutor 前端生产环境打包脚本（Windows 内网部署专用）

功能：
1. 构建 Next.js 生产环境
2. 在 standalone 目录中安装 Windows 平台的 sharp 模块
3. 打包整个 web-prod 目录为 ZIP 压缩包，便于迁移到内网服务器
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
WEB_ROOT = PROJECT_ROOT / "web"
WEB_PROD_DIR = PROJECT_ROOT / "web-prod"
OUTPUT_DIR = PROJECT_ROOT / "dist"

MESSAGES = {
    "en": {
        "checking_node": "Checking Node.js and npm ...",
        "node_missing": "Node.js not found. Please install Node.js and add it to PATH.",
        "npm_missing": "npm not found. Please install npm.",
        "installing_deps": "Installing frontend dependencies ...",
        "building": "Building frontend production assets ...",
        "build_failed": "Frontend build failed with exit code {code}.",
        "build_complete": "Frontend production build completed.",
        "installing_sharp": "Installing Windows-specific sharp module ...",
        "sharp_failed": "Sharp installation failed with exit code {code}.",
        "sharp_complete": "Sharp module installed successfully.",
        "packaging": "Packaging production files ...",
        "package_complete": "Package created: {path}",
        "all_done": "All done! Package is ready for deployment.",
    },
    "zh": {
        "checking_node": "正在检查 Node.js 和 npm ...",
        "node_missing": "未找到 Node.js。请先安装 Node.js 并加入 PATH。",
        "npm_missing": "未找到 npm。请先安装 npm。",
        "installing_deps": "正在安装前端依赖 ...",
        "building": "正在构建前端生产资源 ...",
        "build_failed": "前端构建失败，退出码 {code}。",
        "build_complete": "前端生产构建已完成。",
        "installing_sharp": "正在安装 Windows 平台的 sharp 模块 ...",
        "sharp_failed": "Sharp 安装失败，退出码 {code}。",
        "sharp_complete": "Sharp 模块安装成功。",
        "packaging": "正在打包生产文件 ...",
        "package_complete": "压缩包已创建：{path}",
        "all_done": "全部完成！压缩包已准备好部署。",
    },
}


def _t(language: str, key: str, **kwargs) -> str:
    catalog = MESSAGES.get(language, MESSAGES["en"])
    template = catalog.get(key, MESSAGES["en"][key])
    return template.format(**kwargs)


def _check_prerequisites(language: str) -> tuple[str, str]:
    """检查 Node.js 和 npm 是否可用"""
    print(_t(language, "checking_node"))
    
    try:
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
        print(f"  Node.js: {node_result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  ERROR: {_t(language, 'node_missing')}")
        sys.exit(1)
    
    try:
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=True,
            shell=True,
        )
        print(f"  npm: {npm_result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  ERROR: {_t(language, 'npm_missing')}")
        sys.exit(1)
    
    return "node", "npm"


def _install_deps(npm: str, language: str) -> None:
    """安装前端依赖"""
    print(_t(language, "installing_deps"))
    
    lock_path = WEB_ROOT / "package-lock.json"
    cmd = [npm, "ci"] if lock_path.exists() else [npm, "install"]
    cmd += ["--no-fund", "--no-audit", "--legacy-peer-deps"]
    
    result = subprocess.run(cmd, cwd=str(WEB_ROOT), check=False, shell=True)
    if result.returncode != 0:
        print(f"  ERROR: Dependency installation failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def _build_frontend(npm: str, language: str) -> None:
    """构建前端生产环境"""
    print(_t(language, "building"))
    
    # 清理旧的构建产物
    next_dir = WEB_ROOT / ".next"
    if next_dir.exists():
        shutil.rmtree(next_dir)
    
    result = subprocess.run(
        [npm, "run", "build"],
        cwd=str(WEB_ROOT),
        check=False,
        shell=True,
    )
    
    if result.returncode != 0:
        print(f"  ERROR: {_t(language, 'build_failed', code=result.returncode)}")
        sys.exit(result.returncode or 1)
    
    print(f"  ✓ {_t(language, 'build_complete')}")


def _install_sharp_for_windows(language: str) -> None:
    """在 standalone 目录中安装 Windows 平台的 sharp 模块"""
    standalone_web_dir = WEB_ROOT / ".next" / "standalone" / "DeepTutor" / "web"
    
    if not standalone_web_dir.exists():
        print(f"  ERROR: Standalone directory not found: {standalone_web_dir}")
        sys.exit(1)
    
    print(_t(language, "installing_sharp"))
    
    # 安装 Windows 平台的 sharp
    cmd = [
        "npm", "install",
        "--os=win32",
        "--cpu=x64",
        "--no-save",
        "--no-fund",
        "--no-audit",
        "sharp",
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(standalone_web_dir),
        check=False,
        shell=True,
    )
    
    if result.returncode != 0:
        print(f"  ERROR: {_t(language, 'sharp_failed', code=result.returncode)}")
        sys.exit(result.returncode or 1)
    
    print(f"  ✓ {_t(language, 'sharp_complete')}")


def _prepare_standalone(language: str) -> Path:
    """准备 standalone 目录用于打包"""
    # 清理旧的 web-prod 目录
    if WEB_PROD_DIR.exists():
        shutil.rmtree(WEB_PROD_DIR)
    
    # 创建目标目录结构
    target_dir = WEB_PROD_DIR / "standalone" / "DeepTutor" / "web"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 standalone 内容
    source_dir = WEB_ROOT / ".next" / "standalone" / "DeepTutor" / "web"
    for item in source_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, target_dir / item.name)
        else:
            shutil.copy2(item, target_dir / item.name)
    
    # 复制 .next/static 目录（包含静态资源）
    static_source = WEB_ROOT / ".next" / "static"
    static_target = WEB_PROD_DIR / "standalone" / "DeepTutor" / "web" / ".next" / "static"
    if static_source.exists():
        shutil.copytree(static_source, static_target)
    
    # 复制 public 目录
    public_source = WEB_ROOT / "public"
    public_target = WEB_PROD_DIR / "standalone" / "DeepTutor" / "web" / "public"
    if public_source.exists():
        shutil.copytree(public_source, public_target)
    
    print(f"  ✓ Standalone 目录已准备就绪")
    return WEB_PROD_DIR


def _create_zip_archive(language: str, output_path: Path) -> None:
    """创建 ZIP 压缩包"""
    print(_t(language, "packaging"))
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(WEB_PROD_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(PROJECT_ROOT)
                zipf.write(file_path, arcname)
    
    print(f"  ✓ {_t(language, 'package_complete', path=output_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DeepTutor 前端生产环境打包脚本（Windows 内网部署专用）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 ZIP 文件路径（默认：dist/web-prod-<timestamp>.zip）",
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
        help="跳过依赖安装和 sharp 打包（仅打包构建产物）",
    )
    args = parser.parse_args()
    
    language = args.lang
    
    # 检查前置条件
    node, npm = _check_prerequisites(language)
    
    # 安装依赖
    if not args.skip_deps:
        _install_deps(npm, language)
    
    # 构建前端
    _build_frontend(npm, language)
    
    # 安装 Windows 平台的 sharp
    if not args.skip_deps:
        _install_sharp_for_windows(language)
    
    # 准备 standalone 目录用于打包
    _prepare_standalone(language)
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"web-prod-{timestamp}.zip"
    
    # 创建 ZIP 压缩包
    _create_zip_archive(language, output_path)
    
    print(f"\n✓ {_t(language, 'all_done')}")
    print(f"  压缩包路径: {output_path}")
    print(f"  压缩包大小: {output_path.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
