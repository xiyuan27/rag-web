import os
import shutil
import argparse
import sys

def is_chat_related_file(file_path, filename_keywords, content_keywords):
    print(f"[is_chat_related_file] checking: {file_path}")
    filename = os.path.basename(file_path).lower()
    # 快速 filename 检查
    for kw in filename_keywords:
        if kw in filename:
            print(f"[is_chat_related_file] filename match: {kw} in {filename}")
            return True
    # 再检查文件内容
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            for kw in content_keywords:
                if kw in content:
                    print(f"[is_chat_related_file] content match: {kw} in {file_path}")
                    return True
    except Exception as e:
        print(f"[is_chat_related_file] failed to read {file_path}: {e}")
    return False


def gather_chat_files(src_dir, dest_dir):
    print(f"[gather_chat_files] start walking {src_dir}")
    filename_keywords = ['chat', 'dialog', 'conversation']
    content_keywords = ['/v1/dialog', '/v1/conversation', 'chat-service', 'chat.ts', 'conversation']
    copied = []
    for root, _, files in os.walk(src_dir):
        # 排除根目录下及其子目录中的 node_modules
        for root, dirs, files in os.walk(src_dir):
            if 'node_modules' in dirs:
               dirs.remove('node_modules')
               print(f"[gather_chat_files] skipped node_modules in {root}")
               print(f"[gather_chat_files] in dir: {root} (total files: {len(files)})")


        print(f"[gather_chat_files] in dir: {root} (total files: {len(files)})")
        for file in files:
            src_path = os.path.join(root, file)
            print(f"[gather_chat_files]   file: {file}")
            if is_chat_related_file(src_path, filename_keywords, content_keywords):
                rel_path = os.path.relpath(src_path, src_dir)
                dest_path = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
                print(f"[gather_chat_files]   >> copied to {dest_path}")
                copied.append(rel_path)
    print(f"[gather_chat_files] done, total copied: {len(copied)}")
    return copied


def combine_files(dest_dir, output_file):
    print(f"[combine_files] start combining from {dest_dir}")
    with open(output_file, 'w', encoding='utf-8') as out:
        for root, _, files in os.walk(dest_dir):
            print(f"[combine_files] in dir: {root} (files: {len(files)})")
            for file in sorted(files):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, dest_dir)
                print(f"[combine_files]   writing {rel_path}")
                out.write(f"===== {rel_path} =====\n")
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        out.write(f.read())
                except Exception as e:
                    print(f"[combine_files]   failed to read {file_path}: {e}")
                    out.write("[Binary or unreadable file]\n")
                out.write("\n\n")
    print(f"[combine_files] done, output at {output_file}")


def main():
    print("[main] script start")
    # Use defaults if not provided
    src_dir = r'E:\myDev\project\ragflow\web'
    dest_dir = r'E:\myDev\project\ragflow\test\chat_related'
    output_file = r'E:\myDev\project\ragflow\test\chat_related\chat_code_combined.txt'

    print(f"[main] src_dir={src_dir}")
    print(f"[main] dest_dir={dest_dir}")
    print(f"[main] output_file={output_file}")

    # Step 1: Copy chat-related files
    if os.path.exists(dest_dir):
        print(f"[main] removing existing {dest_dir}")
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    copied = gather_chat_files(src_dir, dest_dir)
    print(f"[main] Copied {len(copied)} files to {dest_dir}")

    # Step 2: Combine into single text
    combine_files(dest_dir, output_file)
    print(f"[main] Combined files into {output_file}")
    print("[main] script end")


if __name__ == "__main__":
    main()
