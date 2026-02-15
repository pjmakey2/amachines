#!/usr/bin/env python3
"""
Final comprehensive fix for JavaScript formatting in Django templates.
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

def format_javascript(js):
    """Comprehensive JavaScript formatting."""

    # Protect Django template tags from modification
    template_tags = []
    def protect_tag(match):
        tag = match.group(0)
        idx = len(template_tags)
        template_tags.append(tag)
        return f'__DJANGO_TAG_{idx}__'

    js = re.sub(r'\{%.*?%\}', protect_tag, js, flags=re.DOTALL)
    js = re.sub(r'\{\{.*?\}\}', protect_tag, js, flags=re.DOTALL)

    # Step 1: Handle comments - they should be on separate lines
    # Find // comments and ensure they end with newline
    js = re.sub(r'//([^\n]*?)(\s+)([a-zA-Z$_])', r'//\1\n\3', js)

    # Step 2: Add newlines after semicolons (but not in for loops)
    js = re.sub(r';(\s*)(?![\s\n]*(for|while|\)))([a-zA-Z$_\}\[])', r';\n\2', js)

    # Step 3: Add newlines after } when followed by identifier or another }
    js = re.sub(r'\}(\s*)(?=[a-zA-Z$_\}])', r'}\n', js)

    # Step 4: Add newlines after function calls that end with )
    js = re.sub(r'\)\s*(?=[a-zA-Z$_](?!\s*:))', r')\n', js)

    # Step 5: Arrow functions - keep => on same line as params, but newline after {
    js = re.sub(r'=>\s*{', r'=> {\n', js)

    # Step 6: Opening braces should have newline after them
    js = re.sub(r'\{\s*(?=[a-zA-Z$_])', r'{\n', js)

    # Step 7: jQuery event handlers
    js = re.sub(r'(\$\([^)]+\)\.on\([^)]+\))\s*(?=[a-zA-Z$_])', r'\1\n', js)

    # Step 8: Variable declarations
    js = re.sub(r'(var|let|const)\s+(\w+)\s*=\s*([^;]+);(\s*)([a-zA-Z$_])', r'\1 \2 = \3;\n\5', js)

    # Step 9: Clean up excessive blank lines (more than 2)
    js = re.sub(r'\n\s*\n\s*\n+', r'\n\n', js)

    # Step 10: Restore Django template tags
    for idx, tag in enumerate(template_tags):
        js = js.replace(f'__DJANGO_TAG_{idx}__', tag)

    return js

def fix_file(file_path):
    """Fix a single template file."""
    print(f"Processing {file_path}...")

    if not os.path.exists(file_path):
        print(f"  File not found, skipping")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and fix all <script> blocks
    def fix_script_block(match):
        indent = match.group(1) if match.group(1) else ''
        script_content = match.group(2)

        # Format the JavaScript
        formatted = format_javascript(script_content)

        # Add proper indentation to each line
        lines = formatted.split('\n')
        indented_lines = [lines[0]]  # First line
        for line in lines[1:]:
            if line.strip():
                indented_lines.append(line)
            else:
                indented_lines.append('')

        formatted = '\n'.join(indented_lines)

        return f'{indent}<script type="text/javascript">\n{formatted}\n{indent}</script>'

    # Process all script blocks
    content = re.sub(
        r'(\s*)<script type="text/javascript">\s*(.*?)\s*</script>',
        fix_script_block,
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

    print("\n✅ All files have been reformatted!")
    print("\nPlease test your Django application to ensure everything works correctly.")
