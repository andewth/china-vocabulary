#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build single-file standalone.html — no separate vocabulary.json fetch."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")
VOCAB = os.path.join(ROOT, "vocabulary.json")
OUT = os.path.join(ROOT, "standalone.html")

MARKER_START = "// STANDALONE:LOAD_DATA:START"
MARKER_END = "// STANDALONE:LOAD_DATA:END"


def main():
    with open(VOCAB, encoding="utf-8") as f:
        vocab = json.load(f)
    vocab_js = json.dumps(vocab, ensure_ascii=False, separators=(",", ":"))

    load_data = f"""{MARKER_START}
let vocabulary = {vocab_js};
function loadData() {{
    const saved = localStorage.getItem("china_vocab_checklist");
    if (saved) {{
        try {{ checkedSet = new Set(JSON.parse(saved).checked || []); }} catch (_) {{}}
    }}
    setSaveStatus("ok", "บันทึกใน browser");
    render();
}}
loadData();
{MARKER_END}"""

    with open(INDEX, encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    skipping = False
    for line in lines:
        if line.strip() == MARKER_START:
            skipping = True
            out.append(load_data + "\n")
            continue
        if skipping:
            if line.strip() == MARKER_END:
                skipping = False
            continue
        if line.strip().startswith("let vocabulary = { chapters:"):
            continue
        if "async function fetchWithRetry" in line:
            skipping = True
            continue
        if skipping and line.strip() == "}" and "render();" in "".join(out[-5:]):
            skipping = False
            continue
        if "async function loadData()" in line:
            skipping = True
            continue
        if skipping and line.strip() == "}" and "render();" in lines[lines.index(line)-1]:
            skipping = False
            continue
        if line.strip().startswith("loadData().catch") or line.strip().startswith("try { loadData();"):
            continue
        if "standalone mode" in line or "ถ้าอยู่ในจีน" in line:
            continue
        out.append(line)

    html = "".join(out)
    if MARKER_START not in html:
        # First run: inject before closing script using simpler replacement
        html = _build_from_scratch()

    html = html.replace(
        "<title>HSK5 综合复习词汇手册 — China Focus</title>",
        "<title>HSK5 词汇 — Standalone</title>",
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Built {OUT} ({os.path.getsize(OUT) // 1024} KB)")


def _build_from_scratch():
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()
    with open(VOCAB, encoding="utf-8") as f:
        vocab_js = f.read().strip()

    start = html.index("<script>")
    end = html.rindex("</script>")
    head = html[: start + len("<script>\n")]
    tail = html[end:]

    body = f"""const CHAPTER_ORDER = ["人物","职业","爱情","社会","家庭","校园","旅行","商贸"];
const CHAPTER_TH = {{
    "人物": "บทที่ 1: 人物 (People)",
    "职业": "บทที่ 2: 职业 (Careers)",
    "爱情": "บทที่ 3: 爱情 (Love)",
    "社会": "บทที่ 4: 社会 (Society)",
    "家庭": "บทที่ 5: 家庭 (Family)",
    "校园": "บทที่ 6: 校园 (Campus)",
    "旅行": "บทที่ 7: 旅行 (Travel)",
    "商贸": "บทที่ 8: 商贸 (Business)"
}};

let vocabulary = {vocab_js};
let checkedSet = new Set();
let filterMode = "all";
let searchQuery = "";
let saveTimer = null;

function loadData() {{
    const saved = localStorage.getItem("china_vocab_checklist");
    if (saved) {{
        try {{ checkedSet = new Set(JSON.parse(saved).checked || []); }} catch (_) {{}}
    }}
    setSaveStatus("ok", "บันทึกใน browser");
    render();
}}

function setSaveStatus(type, msg) {{
    const el = document.getElementById("saveStatus");
    el.className = "status-dot " + type;
    el.textContent = msg;
}}

function saveChecklist() {{
    const data = {{ checked: [...checkedSet], updated_at: new Date().toISOString() }};
    localStorage.setItem("china_vocab_checklist", JSON.stringify(data));
    setSaveStatus("ok", "บันทึกแล้ว ✓");
}}

function toggleCheck(id, checked) {{
    if (checked) checkedSet.add(id);
    else checkedSet.delete(id);
    saveChecklist();
    updateProgress();
    const row = document.querySelector(`tr[data-id="${{id}}"]`);
    if (row) {{
        row.classList.toggle("checked", checked);
        if (filterMode === "unchecked" && checked) row.style.display = "none";
    }}
}}

function updateProgress() {{
    const total = vocabulary.words.length;
    const done = checkedSet.size;
    const pct = total ? Math.round((done / total) * 100) : 0;
    document.getElementById("progressText").textContent =
        `ท่องแล้ว ${{done}} / ${{total}} คำ (${{pct}}%)`;
    document.getElementById("progressFill").style.width = pct + "%";
}}

function wordMatches(w) {{
    if (filterMode === "unchecked" && checkedSet.has(w.id)) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return [w.word, w.pinyin, w.meaning_en, w.pos, w.chapter, w.chapter_en]
        .some(f => (f || "").toLowerCase().includes(q));
}}

function render() {{
    const byChapter = {{}};
    for (const w of vocabulary.words) {{
        (byChapter[w.chapter] ||= []).push(w);
    }}
    const tocList = document.getElementById("tocList");
    tocList.innerHTML = CHAPTER_ORDER.map((id) => {{
        const ch = vocabulary.chapters.find(c => c.id === id);
        const count = ch ? ch.count : (byChapter[id] || []).length;
        const done = (byChapter[id] || []).filter(w => checkedSet.has(w.id)).length;
        return `<li><a href="#ch-${{id}}">${{CHAPTER_TH[id] || id}}</a> — ${{done}}/${{count}}</li>`;
    }}).join("");
    const content = document.getElementById("content");
    content.innerHTML = CHAPTER_ORDER.map(id => {{
        const words = (byChapter[id] || []).filter(wordMatches);
        if (!words.length && (searchQuery || filterMode === "unchecked")) return "";
        const ch = vocabulary.chapters.find(c => c.id === id);
        const total = ch ? ch.count : (byChapter[id] || []).length;
        const done = (byChapter[id] || []).filter(w => checkedSet.has(w.id)).length;
        const rows = words.map(w => {{
            const isChecked = checkedSet.has(w.id);
            return `<tr data-id="${{w.id}}" class="${{isChecked ? "checked" : ""}}">
                <td class="check-cell">
                    <input type="checkbox" ${{isChecked ? "checked" : ""}}
                        onchange="toggleCheck('${{w.id}}', this.checked)" aria-label="ท่องแล้ว">
                    <span class="check-label">ท่องแล้ว</span>
                </td>
                <td>
                    <span class="num">${{w.num}}.</span>
                    <span class="word">${{esc(w.word)}}</span><br>
                    <span class="pinyin">${{esc(w.pinyin)}}</span>
                </td>
                <td><span class="pos">${{esc(w.pos)}}</span></td>
                <td><span class="meaning">${{esc(w.meaning_en)}}</span></td>
            </tr>`;
        }}).join("");
        return `<section id="ch-${{id}}">
            <h2 class="section-title">📚 ${{CHAPTER_TH[id] || id}}</h2>
            <div class="chapter-meta">ท่องแล้ว ${{done}} / ${{total}} คำ</div>
            <table>
                <thead><tr>
                    <th>✓</th><th>คำศัพท์ / พินอิน</th><th>ชนิดคำ</th><th>ความหมาย (ไทย)</th>
                </tr></thead>
                <tbody>${{rows || '<tr><td colspan="4" style="text-align:center;color:#718096">ไม่มีคำที่ตรงกับตัวกรอง</td></tr>'}}</tbody>
            </table>
        </section>`;
    }}).join("");
    updateProgress();
}}

function esc(s) {{
    return String(s || "")
        .replace(/&/g,"&amp;").replace(/</g,"&lt;")
        .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}}

document.getElementById("btnShowAll").onclick = () => {{ filterMode = "all"; render(); }};
document.getElementById("btnShowUnchecked").onclick = () => {{ filterMode = "unchecked"; render(); }};
document.getElementById("btnReset").onclick = () => {{
    if (confirm("รีเซ็ต checklist ทั้งหมด?")) {{
        checkedSet.clear();
        saveChecklist();
        render();
    }}
}};
document.getElementById("searchInput").oninput = (e) => {{
    searchQuery = e.target.value.trim();
    render();
}};

loadData();
"""
    return head + body + tail


if __name__ == "__main__":
    main()
