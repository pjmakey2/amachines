#!/usr/bin/env python3
"""
Script to properly format JavaScript within Django templates.
Adds line breaks in JavaScript blocks that were collapsed.
"""
import re
import os

files_to_fix = [
    'templates/Sifen/DocumentHeaderCreateUi.html',
    'templates/Sifen/DocumentHeaderHomeUi.html',
    'templates/Sifen/DocumentReciboHomeUi.html',
    'templates/Sifen/RetencionCreateUi.html',
    'templates/Sifen/RetencionHomeUi.html',
    'templates/Sifen/DocumentheaderSearchUi.html',
    'templates/OptsIO/PermissionGroupCreateUi.html',
]

def format_javascript_section(js_content):
    """Format JavaScript by adding proper line breaks."""

    # First, handle comments - put them on their own lines
    js_content = re.sub(r'(\w|\))(\s*)(//[^\n]*)', r'\1\2\n\3\n', js_content)  # Inline comments

    # Add newlines after common JavaScript patterns
    js_content = re.sub(r'\}(\s*)([a-zA-Z$_])', r'}\n\1\2', js_content)  # After closing braces
    js_content = re.sub(r';(\s*)([a-zA-Z$_]|\}|function)', r';\n\1\2', js_content)  # After semicolons before identifiers
    js_content = re.sub(r'\{(\s*)([a-zA-Z$_])', r'{\n\1\2', js_content)  # After opening braces
    js_content = re.sub(r'\)(\s*)\{', r')\1{\n', js_content)  # After ) before {
    js_content = re.sub(r'(\w+)\s*=>\s*\{', r'\1 => {\n', js_content)  # Arrow functions
    js_content = re.sub(r'\}\)(\s*)([a-zA-Z$_]|\})', r'})\n\1\2', js_content)  # After closing function calls

    # Handle specific JS patterns
    js_content = re.sub(r'\](\s*)([a-zA-Z$_])', r']\n\1\2', js_content)  # After array close
    js_content = re.sub(r'(\$\([^)]+\)\.on\([^)]+\))(\s*)', r'\1\n\2', js_content)  # After jQuery .on()

    # Clean up excessive newlines (but allow double newlines for spacing)
    js_content = re.sub(r'\n\s*\n\s*\n+', r'\n\n', js_content)

    # Remove newlines that were added inside template tags
    js_content = re.sub(r'\{%\s*\n', r'{% ', js_content)
    js_content = re.sub(r'\n\s*%\}', r' %}', js_content)

    return js_content

def fix_file(file_path):
    """Fix JavaScript formatting in a template file."""
    print(f"Processing {file_path}...")

    if not os.path.exists(file_path):
        print(f"  File not found, skipping")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all <script> blocks and format them
    def format_script_block(match):
        indent = match.group(1)
        script_content = match.group(2)

        # Format the JavaScript
        formatted = format_javascript_section(script_content)

        return f'{indent}<script type="text/javascript">\n{formatted}\n{indent}</script>'

    # Process script blocks
    content = re.sub(
        r'(\s*)<script type="text/javascript">\s*(.*?)\s*</script>',
        format_script_block,
        content,
        flags=re.DOTALL
    )

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Fixed {file_path}")

if __name__ == '__main__':
    for file_path in files_to_fix:
        fix_file(file_path)

    print("\nJavaScript formatting completed!")
