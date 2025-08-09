#!/usr/bin/env python3
"""
Apply Chinese-to-English translations using the generated translation mapping
"""

import os
import re
import glob
from pathlib import Path

def load_translation_map():
    """Load translation mapping from file"""
    translation_map = {}
    
    try:
        with open('/root/Dev/mindnext/hooks/translation_map.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the translation mapping
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and '"' in line and ':' in line:
                try:
                    # Extract Chinese and English from format: "chinese": "english",
                    parts = line.split('": "')
                    if len(parts) == 2:
                        chinese = parts[0].strip().strip('"')
                        english = parts[1].strip().rstrip(',').strip('"')
                        if chinese and english:
                            translation_map[chinese] = english
                except:
                    continue
                    
    except FileNotFoundError:
        print("Translation mapping file not found!")
        return {}
    
    print(f"Loaded {len(translation_map)} translation mappings")
    return translation_map

def apply_translations_to_file(file_path, translation_map):
    """Apply translations to a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False, "Could not read file"
    
    original_content = content
    changes_made = 0
    
    # Sort translations by length (longest first) to avoid partial replacements
    sorted_translations = sorted(translation_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Apply each translation
    for chinese, english in sorted_translations:
        if chinese in content:
            # Use word boundary matching where appropriate
            # For Chinese characters, we need to be careful about context
            old_count = content.count(chinese)
            content = content.replace(chinese, english)
            new_count = content.count(chinese)
            
            replaced_count = old_count - new_count
            if replaced_count > 0:
                changes_made += replaced_count
                print(f"  Replaced '{chinese}' -> '{english}' ({replaced_count} times)")
    
    # Write back if changes were made
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Applied {changes_made} translations"
        except:
            return False, "Could not write file"
    else:
        return True, "No changes needed"

def apply_translations():
    """Apply translations to all Python files in the hooks directory"""
    translation_map = load_translation_map()
    
    if not translation_map:
        print("No translations to apply")
        return
    
    # Process all Python files (excluding cleanup directory)
    files_processed = 0
    files_changed = 0
    total_changes = 0
    
    print(f"\nStarting translation process...")
    print("=" * 50)
    
    for file_path in glob.glob('/root/Dev/mindnext/hooks/**/*.py', recursive=True):
        if 'cleanup' in file_path:
            continue
            
        if 'apply_translations.py' in file_path:
            continue  # Skip this script itself
            
        print(f"\nProcessing: {file_path}")
        success, message = apply_translations_to_file(file_path, translation_map)
        
        files_processed += 1
        
        if success:
            if "Applied" in message:
                files_changed += 1
                # Extract number of changes from message
                try:
                    changes = int(message.split("Applied ")[1].split(" translations")[0])
                    total_changes += changes
                except:
                    pass
            print(f"  ✓ {message}")
        else:
            print(f"  ✗ {message}")
    
    # Process other file types that might contain Chinese
    print(f"\nProcessing other file types...")
    
    for file_pattern in ['**/*.md', '**/*.txt', '**/*.json']:
        for file_path in glob.glob(f'/root/Dev/mindnext/hooks/{file_pattern}', recursive=True):
            if 'cleanup' in file_path:
                continue
            if 'translation_map.txt' in file_path or 'chinese_phrases.txt' in file_path:
                continue  # Skip our generated files
                
            print(f"\nProcessing: {file_path}")
            success, message = apply_translations_to_file(file_path, translation_map)
            
            files_processed += 1
            
            if success:
                if "Applied" in message:
                    files_changed += 1
                    try:
                        changes = int(message.split("Applied ")[1].split(" translations")[0])
                        total_changes += changes
                    except:
                        pass
                print(f"  ✓ {message}")
            else:
                print(f"  ✗ {message}")
    
    print("\n" + "=" * 50)
    print("Translation Summary:")
    print(f"Files processed: {files_processed}")
    print(f"Files changed: {files_changed}")
    print(f"Total translations applied: {total_changes}")
    print("=" * 50)

if __name__ == "__main__":
    apply_translations()