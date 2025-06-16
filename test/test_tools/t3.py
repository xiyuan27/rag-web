import os
import shutil
import math

# ========== 参数配置 ==========
# 输入目录（包含 src 文件夹的父目录）
INPUT_DIR = r"E:\myDev\project\ragflow\web"
# 输出目录（脚本会在此目录下保留原目录结构并拷贝文件）
OUTPUT_DIR = r"E:\myDev\project\ragflow\test\chat"
# 是否在拷贝后统计 Token 数量
COUNT_TOKENS = True
# 粗略估算：平均每 1 token 约等于 4 个字符
AVG_CHAR_PER_TOKEN = 4

# List of files to copy, relative to the "src" directory
RELATIVE_PATHS = [
    os.path.join('src', 'services', 'chat-service.ts'),
    os.path.join('src', 'utils', 'chat.ts'),
    os.path.join('src', 'utils', 'form.ts'),
    os.path.join('src', 'pages', 'search', 'hooks.ts'),
    os.path.join('src', 'pages', 'search', 'index.tsx'),
    os.path.join('src', 'pages', 'user-setting', 'setting-api', 'index.tsx'),
    os.path.join('src', 'pages', 'user-setting', 'setting-system', 'task-bar-chat.tsx'),
]


def copy_files(input_dir: str, output_dir: str) -> None:
    """
    Copy specified files from input_dir to output_dir, preserving directory structure.
    """
    for rel_path in RELATIVE_PATHS:
        src_path = os.path.join(input_dir, rel_path)
        dest_path = os.path.join(output_dir, rel_path)

        if not os.path.isfile(src_path):
            print(f"Warning: Source file not found: {src_path}")
            continue

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        print(f"Copied: {src_path} -> {dest_path}")


def approximate_token_count(text: str) -> int:
    """
    Rough token count: assume each token ~ AVG_CHAR_PER_TOKEN characters.
    """
    return math.ceil(len(text) / AVG_CHAR_PER_TOKEN)


def compute_token_counts(output_dir: str) -> None:
    """
    Compute and print approximate token counts for each copied file and total.
    """
    total_tokens = 0
    print(f"\nApproximate token counts (1 token ~ {AVG_CHAR_PER_TOKEN} chars)")
    for rel_path in RELATIVE_PATHS:
        file_path = os.path.join(output_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Skipped (not found): {file_path}")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tokens = approximate_token_count(content)
        print(f"{rel_path}: {tokens} tokens (approx)")
        total_tokens += tokens

    print(f"Total tokens across all files: {total_tokens} (approx)")


def main():
    input_dir = os.path.abspath(INPUT_DIR)
    output_dir = os.path.abspath(OUTPUT_DIR)

    # Validate input directory
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory does not exist: {input_dir}")
        return

    print(f"Starting to copy files from {input_dir} to {output_dir}...")
    copy_files(input_dir, output_dir)

    if COUNT_TOKENS:
        compute_token_counts(output_dir)
    else:
        print("\nCopy complete. Token counting is disabled.")


if __name__ == '__main__':
    main()
