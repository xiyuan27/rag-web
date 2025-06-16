import os

root_dir = r'E:\myDev\project\ragflow\web'  # 修改为你的 web 目录实际路径
keywords = [
    'dialog/list',
    'Dialog',
    'getDialog',
    'listDialog',
    'conversation',
    'chat',
    'message'
]
exts = ('.ts', '.tsx', '.js', '.jsx', '.json')

matches = []

for dirpath, _, filenames in os.walk(root_dir):
    for fn in filenames:
        if not fn.endswith(exts):
            continue
        filepath = os.path.join(dirpath, fn)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                for kw in keywords:
                    if kw.lower() in line.lower():
                        start = max(0, idx - 2)
                        end = min(len(lines), idx + 3)
                        context = ''.join(lines[start:end])
                        print('='*60)
                        print(f'File: {filepath}')
                        print(f'Line: {idx + 1}')
                        print(f'Keyword: {kw}')
                        print('Context:')
                        print(context)
        except Exception as e:
            pass
