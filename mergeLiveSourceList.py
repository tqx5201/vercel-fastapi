import re

def mergeLiveSourceList(txtContent: str) -> str:
    # 1. 删除 /* */ 多行块注释
    txtContent = re.sub(r'/\*[\s\S]*?\*/', '', txtContent)
    # 2. 删除 // 单行注释
    txtContent = re.sub(r'^\s*//.*', '', txtContent, flags=re.MULTILINE)
    # 3. 删除 # 开头整行（允许前置空白）
    txtContent = re.sub(r'^\s*#.*', '', txtContent, flags=re.MULTILINE)

    lines = [line.strip() for line in txtContent.strip().splitlines()]
    lines = [line for line in lines if line]

    globalUsedUrl = set()
    output = []

    for line in lines:
        parts = [p.strip() for p in line.split(',', 1)]
        if len(parts) < 2:
            part1, part2 = parts[0], ""
        else:
            part1, part2 = parts

        # 分组标题直接加入
        if part2 == "#genre#":
            output.append(line)
            continue

        channelName = part1
        url = part2

        if url in globalUsedUrl:
            continue
        globalUsedUrl.add(url)

        # 检查最后一条是否同频道、非分组，做#拼接
        if output:
            lastItem = output[-1]
            if "#genre#" not in lastItem and lastItem.startswith(f"{channelName},"):
                _, existUrls = lastItem.split(",", 1)
                output[-1] = f"{channelName},{existUrls}#{url}"
                continue
        output.append(f"{channelName},{url}")

    return "\n".join(output)
