import zipfile, re, os

docs_dir = r"C:\Users\ARYAN SHAW\Desktop\Project\trustmatch-ai\Version6+7"
out_lines = []
for f in sorted(os.listdir(docs_dir)):
    if not f.endswith(".docx"):
        continue
    out_lines.append("=" * 80)
    out_lines.append("FILE: " + f)
    out_lines.append("=" * 80)
    z = zipfile.ZipFile(os.path.join(docs_dir, f))
    xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", "", xml)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"\n{3,}", "\n\n", text)
    out_lines.append(text)
    out_lines.append("")

print("\n".join(out_lines))
