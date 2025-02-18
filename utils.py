import os
import fitz

def extract_blocks(pdf_path):
    blocks = []
    doc = fitz.open(pdf_path)
    for page_num, page in enumerate(doc):
        for block in page.get_text("blocks"):
            blocks.append({
                'page': page_num,
                'x0': block[0],
                'y0': block[1],
                'x1': block[2],
                'y1': block[3],
                'raw_block': block
            })
    doc.close()
    return blocks

def drop_to_file(block_text, block_type, block_page_number):
    if debug: print(type(block_text), type(block_type), type(block_page_number), sep='\n', end='\n')
    label_mapping = {"header": "h1", "body": "p", "footer": "footer", "quote": "blockquote", "exclude": "exclude"}
    if block_type == "exclude":
        entry = {
            "label": block_type,
            "page": block_page_number + 1,
            "text": ""}
        entry_unmapped = entry
    else:
        entry = {
            "label": label_mapping.get(block_type, "unknown"),
            "page": block_page_number + 1,
            "text": block_text}
        entry_unmapped = {
            "label": block_type,
            "page": block_page_number + 1,
            "text": block_text}
    with open("output.json", "a", encoding='utf-8') as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with open("ground_truth.json", "a", encoding='utf-8') as file:
        file.write(json.dumps(entry_unmapped, ensure_ascii=False) + "\n")
    if debug: print(entry)

def delete_if_exists(del_file):
    if os.path.exists(del_file):
        os.remove(del_file)

