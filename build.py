#!/usr/bin/env python3
"""
Cross-platform build script for ImageViewer
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

def run_build_script(build_type="all", clean=False, verbose=False, dist_dir="dist", build_dir="build"):
    """Run the appropriate build script for the current platform."""
    platform = detect_platform()
    script_dir = Path(__file__).parent

    if platform == 'windows':
        script_path = script_dir / 'build.ps1'
        if not script_path.exists():
            print("Error: build.ps1 not found. Please ensure the Windows build script exists.")
            sys.exit(1)

        # Build PowerShell command
        cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]

        if build_type != "all":
            cmd.extend(['-BuildType', build_type])
        if clean:
            cmd.append('-Clean')
        if verbose:
            cmd.append('-Verbose')
        if dist_dir != "dist":
            cmd.extend(['-DistDir', dist_dir])
        if build_dir != "build":
            cmd.extend(['-BuildDir', build_dir])

    else:  # Linux or macOS
        script_path = script_dir / 'build.sh'
        if not script_path.exists():
            print("Error: build.sh not found. Please ensure the build script exists.")
            sys.exit(1)

        # Build bash command
        cmd = ['bash', str(script_path)]

        if build_type != "all":
            cmd.extend(['--type', build_type])
        if clean:
            cmd.append('--clean')
        if verbose:
            cmd.append('--verbose')
        if dist_dir != "dist":
            cmd.extend(['--dist', dist_dir])
        if build_dir != "build":
            cmd.extend(['--build', build_dir])

    print(f"Running build script for {platform}...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nBuild interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running build script: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Cross-platform build script for ImageViewer")
    parser.add_argument('--type', choices=['all', 'wheel', 'exe', 'app'],
                       default='all', help='Build type (default: all)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build directories before building')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--dist', default='dist',
                       help='Distribution directory (default: dist)')
    parser.add_argument('--build', default='build',
                       help='Build directory (default: build)')
    parser.add_argument('--help-platform', action='store_true',
                       help='Show platform-specific help')

    args = parser.parse_args()

    if args.help_platform:
        platform = detect_platform()
        print(f"Detected platform: {platform}")
        print("\nThis script will run the appropriate platform-specific build script:")
        print("- Windows: build.ps1")
        print("- Linux/macOS: build.sh")
        print("\nFor platform-specific options, run the appropriate script directly:")
        if platform == 'windows':
            print("  .\\build.ps1 -Help")
        else:
            print("  ./build.sh --help")
        return

    run_build_script(
        build_type=args.type,
        clean=args.clean,
        verbose=args.verbose,
        dist_dir=args.dist,
        build_dir=args.build
    )

if __name__ == '__main__':
    main()
