# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>

"""Entry point for the image viewer application."""

import argparse
import os
import sys

from .image_viewer import ImageViewer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="A simple Tkinter image viewer.")
    parser.add_argument("--path", type=str, help="Path to the image to view")
    parser.add_argument("--internet", type=str, help="URL of the image to download and view")
    parser.add_argument("file_path", nargs="?", type=str, help="Path to the image to view (positional)")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check if --internet flag is used
    if args.internet:
        try:
            viewer = ImageViewer(args.internet, is_url=True)
            viewer.run()
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading image from URL: {str(e)}")
            sys.exit(1)
    else:
        # Use --path if provided, otherwise use positional file_path
        image_path = args.path if args.path is not None else args.file_path
        
        if image_path is None:
            parser = argparse.ArgumentParser(description="A simple Tkinter image viewer.")
            parser.print_help()
            print("\nError: Please provide an image path either as --path option, --internet URL, or as a positional argument.")
            sys.exit(1)
        
        if os.path.exists(image_path):
            viewer = ImageViewer(image_path, is_url=False)
            viewer.run()
        else:
            print(f"Error: The file {image_path} does not exist.")
            sys.exit(1)


if __name__ == "__main__":
    main()

