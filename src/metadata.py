"""Module for extracting and formatting image metadata."""

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import ExifTags, Image, ImageCms


def parse_xmp_metadata(xmp_data: str) -> list[str]:
    """Parse XMP/XML metadata and return readable format."""
    lines = []
    try:
        # Handle bytes
        if isinstance(xmp_data, bytes):
            xmp_data = xmp_data.decode('utf-8', errors='ignore')
        
        # Remove BOM if present
        if xmp_data.startswith('\ufeff'):
            xmp_data = xmp_data[1:]
        
        # Parse XML
        root = ET.fromstring(xmp_data)
        
        # Define namespaces commonly used in XMP
        namespaces = {
            'x': 'adobe:ns:meta/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'xmpRights': 'http://ns.adobe.com/xap/1.0/rights/',
            'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
            'tiff': 'http://ns.adobe.com/tiff/1.0/',
            'exif': 'http://ns.adobe.com/exif/1.0/',
            'crs': 'http://ns.adobe.com/camera-raw-settings/1.0/',
            'xmpMM': 'http://ns.adobe.com/xap/1.0/mm/',
            'stEvt': 'http://ns.adobe.com/xap/1.0/sType/ResourceEvent#',
        }
        
        # Extract common XMP fields
        xmp_fields = {
            'dc:title': 'Title',
            'dc:description': 'Description',
            'dc:creator': 'Creator',
            'dc:subject': 'Subject',
            'dc:rights': 'Rights',
            'xmp:CreateDate': 'Create Date',
            'xmp:ModifyDate': 'Modify Date',
            'xmp:MetadataDate': 'Metadata Date',
            'xmp:CreatorTool': 'Creator Tool',
            'xmp:Rating': 'Rating',
            'xmpRights:Marked': 'Copyrighted',
            'xmpRights:WebStatement': 'Copyright URL',
            'photoshop:AuthorsPosition': 'Author Position',
            'photoshop:CaptionWriter': 'Caption Writer',
            'photoshop:Category': 'Category',
            'photoshop:City': 'City',
            'photoshop:Country': 'Country',
            'photoshop:Credit': 'Credit',
            'photoshop:DateCreated': 'Date Created',
            'photoshop:Headline': 'Headline',
            'photoshop:Instructions': 'Instructions',
            'photoshop:Source': 'Source',
            'photoshop:State': 'State',
            'photoshop:TransmissionReference': 'Transmission Reference',
            'tiff:Make': 'Camera Make',
            'tiff:Model': 'Camera Model',
            'tiff:Software': 'Software',
            'exif:DateTimeOriginal': 'Date Time Original',
            'exif:ExposureTime': 'Exposure Time',
            'exif:FNumber': 'F-Number',
            'exif:ISOSpeedRatings': 'ISO Speed',
            'exif:FocalLength': 'Focal Length',
        }
        
        # Helper to get text from elements
        def get_text(elem, path, ns_map):
            parts = path.split('/')
            current = elem
            for part in parts:
                if ':' in part:
                    prefix, local = part.split(':', 1)
                    ns = ns_map.get(prefix)
                    if ns:
                        current = current.find(f'.//{{{ns}}}{local}')
                    else:
                        current = current.find(f'.//{part}')
                else:
                    current = current.find(f'.//{part}')
                if current is None:
                    return None
            return current.text if current is not None else None
        
        # Helper to get all matching elements
        def get_all_text(elem, path, ns_map):
            results = []
            parts = path.split('/')
            if len(parts) == 1:
                if ':' in parts[0]:
                    prefix, local = parts[0].split(':', 1)
                    ns = ns_map.get(prefix)
                    if ns:
                        elements = elem.findall(f'.//{{{ns}}}{local}', namespaces)
                    else:
                        elements = elem.findall(f'.//{parts[0]}', namespaces)
                else:
                    elements = elem.findall(f'.//{parts[0]}', namespaces)
                
                for el in elements:
                    if el.text:
                        results.append(el.text)
            return results
        
        # Extract RDF descriptions
        rdf_ns = namespaces.get('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        descriptions = root.findall(f'.//{{{rdf_ns}}}Description')
        
        if descriptions:
            for desc in descriptions:
                # Extract attributes and elements
                for key, label in xmp_fields.items():
                    if ':' in key:
                        prefix, local = key.split(':', 1)
                        ns = namespaces.get(prefix)
                        if ns:
                            # Try as attribute first
                            attr_name = f'{{{ns}}}{local}'
                            value = desc.get(attr_name)
                            if value:
                                lines.append(f"  {label}: {value}")
                            else:
                                # Try as element
                                elem = desc.find(f'{{{ns}}}{local}')
                                if elem is not None and elem.text:
                                    lines.append(f"  {label}: {elem.text}")
        
        # If no structured data found, show raw XML structure
        if not lines:
            # Extract all attributes from Description elements
            for desc in descriptions:
                for attr, value in desc.attrib.items():
                    if value and len(value) < 100:
                        # Extract namespace prefix if possible
                        if '}' in attr:
                            local_name = attr.split('}')[1]
                        else:
                            local_name = attr
                        lines.append(f"  {local_name}: {value}")
        
        # If still nothing, show a summary
        if not lines:
            lines.append("  XMP data present but structure unclear")
            lines.append(f"  Total XML size: {len(xmp_data)} characters")
    
    except ET.ParseError as e:
        lines.append(f"  XML Parse Error: {str(e)}")
        lines.append("  Showing raw data (truncated)")
        if isinstance(xmp_data, str) and len(xmp_data) > 200:
            lines.append(f"  {xmp_data[:200]}...")
        else:
            lines.append(f"  {str(xmp_data)[:200]}")
    except Exception as e:
        lines.append(f"  Error parsing XMP: {str(e)}")
    
    return lines


def format_metadata(
    original_image: Image.Image,
    resolved_path: Path,
    image_url: str | None = None,
    url_image_size: int | None = None,
    url_image_hash: str | None = None,
) -> str:
    """
    Extract and format all comprehensive image metadata.
    
    Args:
        original_image: The PIL Image object
        resolved_path: Path to the image file (or display path for URLs)
        image_url: URL if image was loaded from internet
        url_image_size: Size in bytes if loaded from URL
        url_image_hash: MD5 hash if loaded from URL
        
    Returns:
        Formatted metadata string
    """
    lines = []
    is_url_flag = image_url is not None
    
    # === 1. Basic Image Information ===
    lines.append("=== Basic Image Info ===")
    lines.append(f"Format: {original_image.format or 'Unknown'}")
    lines.append(f"Mode: {original_image.mode}")
    lines.append(f"Size: {original_image.width}x{original_image.height}")
    
    # Bit depth
    if hasattr(original_image, 'bits'):
        lines.append(f"Bit Depth: {original_image.bits}")
    
    # File info
    file_path = resolved_path
    if hasattr(original_image, 'filename') and original_image.filename:
        file_path = Path(original_image.filename)
    
    lines.append(f"File: {file_path.name}")
    
    # File system metadata (only for local files)
    if not is_url_flag:
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            lines.append(f"File Size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
            lines.append(f"Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            pass
    else:
        lines.append(f"Source: Internet URL")
        if url_image_size is not None:
            lines.append(f"Downloaded Size: {url_image_size:,} bytes ({url_image_size / 1024:.2f} KB)")
    
    # === 2. Image Structure ===
    lines.append("\n=== Image Structure ===")
    info = original_image.info or {}
    
    # DPI/Resolution
    dpi = info.get('dpi', (72, 72))
    if isinstance(dpi, tuple) and len(dpi) == 2:
        lines.append(f"DPI: {dpi[0]}x{dpi[1]}")
    
    # Compression
    compression = info.get('compression', 'Unknown')
    lines.append(f"Compression: {compression}")
    
    # Quality (for JPEG)
    if 'quality' in info:
        lines.append(f"Quality: {info['quality']}")
    
    # Progressive (JPEG)
    if 'progressive' in info:
        lines.append(f"Progressive: {info['progressive']}")
    
    # === 3. Color Profile ===
    lines.append("\n=== Color Profile ===")
    if 'icc_profile' in info:
        try:
            profile_bytes = info['icc_profile']
            if isinstance(profile_bytes, bytes):
                profile = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
                desc = ImageCms.getProfileDescription(profile)
                lines.append(f"Profile: {desc}")
            else:
                lines.append("Profile: Embedded (unreadable)")
        except Exception:
            lines.append("Profile: Embedded (unreadable)")
    else:
        lines.append("No color profile embedded")
    
    # Color space
    if 'colorspace' in info:
        lines.append(f"Color Space: {info['colorspace']}")
    
    # === 4. EXIF Data ===
    try:
        exif = original_image.getexif()
        if exif:
            lines.append("\n=== EXIF Data ===")
            
            # Camera Information
            camera_make = exif.get(271)  # Make tag
            camera_model = exif.get(272)  # Model tag
            if camera_make or camera_model:
                lines.append(f"Camera: {camera_make or ''} {camera_model or ''}".strip())
            
            # Date/Time
            date_time = exif.get(306)  # DateTime tag
            if date_time:
                lines.append(f"Date/Time: {date_time}")
            
            # GPS Coordinates
            try:
                gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_info:
                    lines.append("\n--- GPS Info ---")
                    for tag_id, value in gps_info.items():
                        tag_name = ExifTags.GPSTAGS.get(tag_id, f"GPS{tag_id}")
                        lines.append(f"  {tag_name}: {value}")
            except Exception:
                pass
            
            # Exposure Settings
            lines.append("\n--- Camera Settings ---")
            exposure_settings = {
                33434: "ExposureTime",
                33437: "FNumber",
                34855: "ISOSpeedRatings",
                37377: "ShutterSpeedValue",
                37378: "ApertureValue",
                37386: "FocalLength",
                37396: "SubjectDistance",
                41986: "ExposureMode",
                41987: "WhiteBalance",
            }
            
            for tag_id, tag_name in exposure_settings.items():
                value = exif.get(tag_id)
                if value is not None:
                    lines.append(f"  {tag_name}: {value}")
            
            # Orientation
            orientation = exif.get(274)  # Orientation tag
            if orientation:
                orientations = {
                    1: "Normal",
                    2: "Mirrored horizontal",
                    3: "Rotated 180°",
                    4: "Mirrored vertical",
                    5: "Mirrored horizontal, rotated 270°",
                    6: "Rotated 90°",
                    7: "Mirrored horizontal, rotated 90°",
                    8: "Rotated 270°",
                }
                lines.append(f"  Orientation: {orientations.get(orientation, orientation)}")
            
            # Software
            software = exif.get(305)  # Software tag
            if software:
                lines.append(f"Software: {software}")
            
            # All other EXIF tags
            other_tags = []
            for tag_id, value in exif.items():
                if tag_id not in [271, 272, 306, 274, 305] and tag_id not in exposure_settings.keys():
                    tag_name = ExifTags.TAGS.get(tag_id, f"Tag{tag_id}")
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:47] + "..."
                    other_tags.append(f"  {tag_name}: {str_value}")
            
            if other_tags:
                lines.append("\n--- Other EXIF Tags ---")
                lines.extend(other_tags[:20])  # Limit to first 20
                if len(other_tags) > 20:
                    lines.append(f"  ... and {len(other_tags) - 20} more tags")
    except Exception as e:
        lines.append(f"\n=== EXIF Data ===")
        lines.append(f"Error reading EXIF: {str(e)}")
    
    # === 5. XMP Metadata ===
    lines.append("\n=== XMP Metadata ===")
    xmp_found = False
    xmp_keys = []
    for key in info.keys():
        if 'xmp' in key.lower() or ('xml' in key.lower() and 'adobe' in str(info[key]).lower()):
            xmp_found = True
            xmp_keys.append(key)
    
    if xmp_found:
        for key in xmp_keys:
            xmp_data = info[key]
            parsed_lines = parse_xmp_metadata(xmp_data)
            if parsed_lines:
                lines.extend(parsed_lines)
            else:
                str_value = str(xmp_data)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                lines.append(f"  {key}: {str_value}")
    else:
        lines.append("No XMP metadata found")
    
    # === 6. IPTC Metadata ===
    lines.append("\n=== IPTC Metadata ===")
    iptc_found = False
    for key in info.keys():
        if 'iptc' in key.lower() or 'photoshop' in key.lower():
            iptc_found = True
            str_value = str(info[key])
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            lines.append(f"{key}: {str_value}")
    if not iptc_found:
        lines.append("No IPTC metadata found")
    
    # === 7. Embedded Thumbnails ===
    lines.append("\n=== Embedded Thumbnails ===")
    if 'thumbnail' in info:
        thumb = info['thumbnail']
        if isinstance(thumb, bytes):
            lines.append(f"Thumbnail: {len(thumb)} bytes")
        else:
            lines.append(f"Thumbnail: Present")
    else:
        lines.append("No embedded thumbnail")
    
    # === 8. All Other Metadata ===
    lines.append("\n=== All Other Metadata ===")
    other_metadata = []
    skip_keys = ['dpi', 'compression', 'quality', 'progressive', 'icc_profile', 
                 'colorspace', 'thumbnail', 'exif']
    # Also skip XMP keys we already parsed (defined in XMP section above)
    if xmp_found:
        skip_keys.extend(xmp_keys)
    
    for key, value in sorted(info.items()):
        # Skip already displayed keys
        if key.lower() not in [k.lower() for k in skip_keys]:
            str_value = str(value)
            if len(str_value) > 80:
                str_value = str_value[:77] + "..."
            other_metadata.append(f"{key}: {str_value}")
    
    if other_metadata:
        lines.extend(other_metadata[:30])  # Limit to first 30
        if len(other_metadata) > 30:
            lines.append(f"... and {len(other_metadata) - 30} more entries")
    else:
        lines.append("No additional metadata")
    
    # === 9. File Hash (MD5) ===
    if not is_url_flag:
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            lines.append(f"\n=== File Hash ===")
            lines.append(f"MD5: {file_hash}")
        except Exception:
            pass
    else:
        if url_image_hash is not None:
            lines.append(f"\n=== Image Hash ===")
            lines.append(f"MD5: {url_image_hash}")
    
    return "\n".join(lines)


def detect_watermark(original_image: Image.Image) -> str:
    """
    Detect watermark information from image metadata.
    
    Args:
        original_image: The PIL Image object
        
    Returns:
        Watermark information string
    """
    watermark_info = []
    info = original_image.info or {}
    
    # Check EXIF for copyright/watermark info
    try:
        exif = original_image.getexif()
        if exif:
            # Copyright tag (33432)
            copyright_info = exif.get(33432)
            if copyright_info:
                watermark_info.append(f"Copyright: {copyright_info}")
            
            # Artist tag (315)
            artist = exif.get(315)
            if artist:
                watermark_info.append(f"Artist: {artist}")
    except Exception:
        pass
    
    # Check XMP for watermark/copyright
    for key in info.keys():
        if 'xmp' in key.lower() or ('xml' in key.lower() and 'adobe' in str(info[key]).lower()):
            try:
                xmp_data = info[key]
                if isinstance(xmp_data, bytes):
                    xmp_data = xmp_data.decode('utf-8', errors='ignore')
                
                # Look for copyright/watermark keywords in XMP
                if 'copyright' in xmp_data.lower() or 'watermark' in xmp_data.lower():
                    # Try to extract copyright info
                    if 'xmpRights:Marked' in xmp_data or 'dc:rights' in xmp_data:
                        watermark_info.append("Copyright marked in XMP")
            except Exception:
                pass
    
    # Check IPTC for copyright
    for key in info.keys():
        if 'iptc' in key.lower() or 'photoshop' in key.lower():
            watermark_info.append("IPTC metadata present")
            break
    
    # Check for watermark in image info
    if 'watermark' in str(info).lower():
        watermark_info.append("Watermark metadata detected")
    
    if watermark_info:
        return " | ".join(watermark_info[:2])  # Limit to 2 items
    else:
        return "None detected"

