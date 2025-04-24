DISCORD_MESSAGE_LIMIT = 1900  # stays under 2000 safely

def chunk_logs(log_block, limit=DISCORD_MESSAGE_LIMIT):
    chunks = []
    current_chunk = ""
    for line in log_block.split("\n"):
        if len(current_chunk) + len(line) + 1 > limit:
            chunks.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks
