#!/usr/bin/env python3
"""
Cross-platform installation script for ImageViewer
Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def detect_platform():
    """Detect the current platform."""
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    elif sys.platform.startswith('linux'):
        return 'linux'
    else:
        return 'unknown'

def run_install_script(install_type="user", python_version="", venv=".venv", verbose=False):
    """Run the appropriate install script for the current platform."""
    platform = detect_platform()
    script_dir = Path(__file__).parent

    if platform == 'windows':
        script_path = script_dir / 'install.ps1'
        if not script_path.exists():
            print("Error: install.ps1 not found. Please ensure the Windows install script exists.")
            sys.exit(1)

        # Build PowerShell command
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]

        if install_type != "user":
            cmd.extend(['-InstallType', install_type])
        if python_version:
            cmd.extend(['-PythonVersion', python_version])
        if venv != ".venv":
            cmd.extend(['-VirtualEnv', venv])
        if verbose:
            cmd.append('-Verbose')

    else:  # Linux or macOS
        script_path = script_dir / 'install.sh'
        if not script_path.exists():
            print("Error: install.sh not found. Please ensure the install script exists.")
            sys.exit(1)

        # Build bash command
        cmd = ['bash', str(script_path)]

        if install_type != "user":
            cmd.extend(['--type', install_type])
        if python_version:
            cmd.extend(['--python', python_version])
        if venv != ".venv":
            cmd.extend(['--venv', venv])
        if verbose:
            cmd.append('--verbose')

    print(f"Running install script for {platform}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running install script: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Cross-platform installation script for ImageViewer")
    parser.add_argument('--type', choices=['user', 'dev', 'system'],
                       default='user', help='Installation type (default: user)')
    parser.add_argument('--python', default='',
                       help='Python version to use (default: auto-detect)')
    parser.add_argument('--venv', default='.venv',
                       help='Virtual environment name (default: .venv)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--help-platform', action='store_true',
                       help='Show platform-specific help')

    args = parser.parse_args()

    if args.help_platform:
        platform = detect_platform()
        print(f"Detected platform: {platform}")
        print("\nThis script will run the appropriate platform-specific install script:")
        print("- Windows: install.ps1")
        print("- Linux/macOS: install.sh")
        print("\nFor platform-specific options, run the appropriate script directly:")
        if platform == 'windows':
            print("  .\\install.ps1 -Help")
        else:
            print("  ./install.sh --help")
        return

    run_install_script(
        install_type=args.type,
        python_version=args.python,
        venv=args.venv,
        verbose=args.verbose
    )

if __name__ == '__main__':
    main()
