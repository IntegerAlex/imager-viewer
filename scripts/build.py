# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""
Build script for creating standalone executable with PyInstaller.
"""

import os
import shutil
import subprocess
import sys


def clean_build_dirs():
    """Clean build and dist directories."""
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)
    
    # Clean .spec file artifacts
    for file in os.listdir('.'):
        if file.endswith('.spec') and file != 'imageviewer.spec':
            os.remove(file)
            print(f"Removed {file}")


def build_executable(clean=False):
    """Build the executable using PyInstaller."""
    if clean:
        clean_build_dirs()
    
    print("Building executable with PyInstaller...")
    print("=" * 50)
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--workpath', 'build',
        '--distpath', 'dist',
        'imageviewer.spec'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print(f"Executable location: dist/imageviewer{'.exe' if sys.platform == 'win32' else ''}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it:")
        print("  pip install pyinstaller")
        return False


def main():
    """Main build function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build imageviewer executable')
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build directories before building'
    )
    args = parser.parse_args()
    
    if not os.path.exists('imageviewer.spec'):
        print("Error: imageviewer.spec not found!")
        sys.exit(1)
    
    success = build_executable(clean=args.clean)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

