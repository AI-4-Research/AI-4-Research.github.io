import json
import bibtexparser
from bibtexparser.bparser import BibTexParser
from extract_tool import extract_cite_from_paragraph, extract_cite_from_subsections, extract_cite_from_subsubsections
import os

def format_title(title, remove_content=False):
    """
    格式化标题，删除左右括号及其内容（可选）。
    
    :param title: 原始标题字符串
    :param remove_content: 是否删除括号内的内容（默认为 False，仅删除括号）
    :return: 格式化后的标题字符串
    """
    remove_content=False
    if remove_content:
        # 删除括号及其内部的内容
        import re
        return re.sub(r'\(.*?\)', '', title).strip()
    else:
        # 仅删除括号，保留括号内的内容
        return title.replace('{', '').replace('}', '')

def format_author(authors):
    """
    将完整的作者列表转换为 "第一作者姓氏 + et al." 的形式。
    :param authors: 原始作者字符串（如 'Pang, Bo and Dong, Hanze and ...' 或 'Pang Bo and Dong Hanze and ...'）
    :return: 格式化后的作者字符串（如 'Pang et al.'）
    """
    # 检查是否有逗号
    if "," in authors:
        # 如果有逗号，按逗号分隔并提取第一个作者的姓氏
        first_author = authors.split(",")[0].strip()
    else:
        # 如果没有逗号，按 'and' 分隔并提取第一个作者的姓氏
        first_author = authors.split(" and ")[0].strip()
        # 如果名字是 "FirstName LastName" 格式，提取姓氏
        if " " in first_author:
            first_author = first_author.split(" ")[-1].strip()
    
    return f"{first_author} et al."

def arxiv_to_url(journal):
    if "arXiv:" in journal:
        paper_id = journal.split("arXiv:")[1].strip()
        return f"https://arxiv.org/abs/{paper_id}"
    else:
        raise ValueError("输入的 journal 字段不包含有效的 arXiv 编号")

def get_month(month_str, MONTH_DICT):
    for key in MONTH_DICT:
        if key.lower() in month_str.lower():
            return MONTH_DICT[key]
    return "00"

BASE_URL = "arxiv_v2"

CONFERENCE_DICT = json.load(open("scripts/data/conference.json", "r"))
CONFERENCE_DICT = dict(sorted(CONFERENCE_DICT.items(), key=lambda item: len(item[0]), reverse=True))
sections_dir = f"{BASE_URL}/sections"
list_ = ["analysis.tex", "deep_reasoning.tex", "feasible_reflection.tex", "extensive_exploration.tex", "future.tex", "resources.tex"]
TITLE_DICT = {"deep_reasoning.tex": "Deep Reasoning", "analysis.tex": "Analysis and Evaluation", "feasible_reflection.tex": "Feasible Reflection", "extensive_exploration.tex": "Extensive Exploration", "future.tex": "Future and Frontiers", "resources.tex": "Resources"}
FILE_DICT = {"analysis & explanation for long cot": "analysis.jpg", "deep reasoning format": "deep-reasoning-1.jpg", "deep reasoning learning": "deep-reasoning-2.png", "feedback": "feedback.png", "refinement": "refinement.png", "refinement": "refinement.png", "exploration scaling": "exploration-scaling.png", "external exploration": "external-exploration.png", "internal exploration": "internal-exploration.png"}
str_all = ""
with open(f'{BASE_URL}/ref.bib') as bibtex_file:
    parser = BibTexParser()
    bib_database = bibtexparser.load(bibtex_file, parser=parser)
data_dict = {x["ID"]: x for x in bib_database.entries}
section_counter = 0

for tex_file in list_:
    section_counter += 1
    if tex_file.endswith(".tex"):
        tex_path = os.path.join(sections_dir, tex_file)
        section_id = "-".join(TITLE_DICT[tex_file].lower().replace(" & ", " ").split(" "))
        str_all += f"""<h2 id="{section_id}">{section_counter}. {TITLE_DICT[tex_file]}</h2>\n"""
        if tex_file == "future.tex":
            str_all += f'\n<img src="./assets/images/future.jpg" style="width: 580pt">\n\n'
        with open(tex_path, encoding="utf-8") as f:
            data = f.read()
        # cite_data = extract_cite_from_subsubsections(data)
        cite_data = extract_cite_from_paragraph(data)
        
        
        
        res_dict = []
        MONTH_DICT = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        
        for subsection in cite_data.keys():
            for subsubsection in cite_data[subsection].keys():
                for paragraph, cites in cite_data[subsection][subsubsection].items():
                    seen_titles = set()  # 用于记录已经处理过的文章标题
                    for cite in cites:
                        entry = data_dict[cite]
                        author = format_author(entry["author"])
                        
                        if "journal" in entry and "arXiv:" in entry["journal"]:
                            year_month = entry["journal"].split("arXiv:")[1].split(".")[0]
                            time_str = f"20{year_month[:2]}.{year_month[2:]}"  # 生成类似 "2025.02"
                            url = arxiv_to_url(entry["journal"])
                            source = "arXiv"
                        elif "url" in entry:
                            year = entry.get("year", "")
                            month = get_month(entry.get("month", ""), MONTH_DICT)
                            time_str = f"{year}.{month}"
                            url = entry["url"]
                            source = "pdf"  # 假设非 arXiv 的 URL 是 PDF
                        else:
                            year = entry.get("year", "")
                            month = get_month(entry.get("month", ""), MONTH_DICT)
                            time_str = f"{year}.{month}"
                            url = ""
                            if "book_title" in entry:
                                book_title = entry.get('booktitle', "")
                            else:
                                book_title = entry.get('journal', "")
                            source = "unknown"
                            for key in CONFERENCE_DICT:
                                if key in book_title:
                                    source = CONFERENCE_DICT[key]
                                    break
                            
                            
                            # source = "unknown"
                        if url == "" and "howpublished" in entry:
                            url = entry.get("howpublished", "").strip("\\url{").strip("}")
                        if source == "unknown" and "github" in url:
                            source = "github"
                        if source == "unknown" and "notion" in url:
                            source = "notion"
                        if source == "unknown" and "anthropic" in url:
                            source = "anthropic"
                        if source == "unknown" and "huggingface" in url:
                            source = "huggingface"
                        title = format_title(entry["title"]).replace("\\", "")
                        title = title.replace("$^", "<sup>").replace("$", "</sup>")
                        # 检查标题是否已经存在于当前小章节中
                        if title in seen_titles:
                            continue  # 跳过重复的标题
                        seen_titles.add(title)  # 记录已处理的标题
                        
                        res_dict.append({
                            "subsection": subsection.replace("\\&", "&"),
                            "subsubsection": subsubsection.replace("\\&", "&"),
                            "paragraph": paragraph.replace("\\&", "&"),
                            "title": title,
                            "author": author,
                            "time": time_str,
                            "url": url,
                            "source": source
                        })

        # 按类型和时间排序
        res_dict.sort(key=lambda x: (x["subsection"], x["subsubsection"], x["paragraph"], x["time"]))
        
        def format_to_html(data, section_counter):
            subsection_counter = 0
            subsubsection_counter = 0
            formatted_lines = []
            current_type = None
            current_subsubsection = None
            current_paragraph = None
            
            for entry in data:
                title = entry['title']
                author = entry['author']
                time = entry['time']
                url = entry.get('url', '')
                
                source = entry['source']

                # 生成徽章的 URL 和标签
                if source == "arXiv":
                    badge_label = "arXiv"
                    badge_color = "red"
                    badge_message = time  # 显示时间（如 "2025.02"）
                elif source == "pdf":
                    badge_label = "PDF"
                    badge_color = "blue"
                    badge_message = time
                elif source == "github":
                    badge_label = "Github"
                    badge_color = "white"
                    badge_message = time
                elif source == "notion":
                    badge_label = "Notion"
                    badge_color = "white"
                    badge_message = time
                elif source == "huggingface":
                    badge_label = "Huggingface"
                    badge_color = "yellow"
                    badge_message = time
                elif source == "unknown":
                    print(f"No source: {entry['title']}")
                    badge_label = "Other Source"
                    badge_color = "lightgrey"
                    badge_message = time
                else:
                    badge_label = source
                    badge_color = "green"
                    badge_message = time.split(".")[0]
                # 构造徽章的图片链接
                badge_url = f"https://img.shields.io/badge/{badge_label}-{badge_message}-{badge_color}"
                
                # 如果有 URL，则包裹在 <a> 标签中
                if url:
                    badge_html = f'<a href="{url}" target="_blank"><img src="{badge_url}" alt="{badge_label} Badge"></a>'
                else:
                    print(f"No URL: {entry['title']}")
                    badge_html = f'<img src="{badge_url}" alt="{badge_label} Badge">'

                # 构造 HTML 列表项
                html_line = f'<li><i><b>{title}</b></i>, {author}, {badge_html}</li>'

                # 处理分组
                if entry["subsection"] != current_type:
                    if current_type is not None:
                        formatted_lines.append("</ul>")
                        formatted_lines.append("")
                        current_subsubsection = None
                    if entry['subsection'] != "***":
                        subsection_counter += 1
                        subsection_id = "-".join(entry['subsection'].lower().replace(" & ", " ").split(" "))
                        formatted_lines.append(f"""\n\n<h3 id="{subsection_id}">{section_counter}.{subsection_counter} {entry['subsection']}</h3>""")
                        if tex_file not in ["future.tex", "resources.tex"] and entry['subsection'].lower() not in ["long cot evaluations"]:
                            if entry['subsection'].lower() in FILE_DICT:
                                file_name = FILE_DICT[entry['subsection'].lower()]
                            else:
                                file_name = "-".join(entry['subsection'].lower().replace(" & ", " ").split(" "))+".png"
                            formatted_lines.append(f'<img src="./assets/images/{file_name}" style="width: 580pt">')
                    current_type = entry["subsection"]
                if entry["subsection"] + "/" + entry["subsubsection"] != current_subsubsection:
                    if current_subsubsection is not None:
                        formatted_lines.append("</ul>")
                        formatted_lines.append("")
                        current_subsubsection = None
                    if entry['subsubsection'] != "***":
                        subsubsection_counter += 1
                        subsubsection_id = "-".join(entry['subsubsection'].lower().replace(" & ", " ").split(" "))
                        formatted_lines.append(f"""<h4 id="{subsubsection_id}">{section_counter}.{subsection_counter}.{subsubsection_counter} {entry['subsubsection']}</h4>""")
                    current_subsubsection = entry["subsection"] + "/" + entry["subsubsection"]
                if entry["subsection"] + "/" + entry["subsubsection"] + "/" + entry['paragraph'] != current_paragraph:
                    if current_paragraph is not None:
                        formatted_lines.append("</ul>")
                        formatted_lines.append("")
                    if entry['paragraph'] != "***":
                        formatted_lines.append(f"<b>{entry['paragraph']}</b>")
                    formatted_lines.append("<ul>")
                    current_paragraph = entry["subsection"] + "/" + entry["subsubsection"] + "/" + entry['paragraph']
                formatted_lines.append(html_line)
            
            formatted_lines.append("</ul>")
            return "\n".join(formatted_lines)

        html_str = format_to_html(res_dict, section_counter)
        str_all += html_str + "\n"

# 写入文件
file_path = "scripts/output/paper.html"
try:
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str_all)
    print(f"内容已成功写入文件：{file_path}")
except Exception as e:
    print(f"写入文件时出错：{e}")