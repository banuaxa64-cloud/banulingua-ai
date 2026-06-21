import streamlit as st
import streamlit.components.v1 as components
import html
import os
import base64
import json
import requests

# ١. ڕێکخستنی سەرەتایی ئەپەکە
LOGO_PATH = "logo.png"
logo_base64 = None
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

page_icon = LOGO_PATH if os.path.exists(LOGO_PATH) else "🔮"
st.set_page_config(page_title="BanuLingua AI", page_icon=page_icon, layout="centered")

# ٢. ئایکۆن، manifest، viewport، و قەرەبووکردنەوەی شاشە بۆ مۆبایل
# (manifest واقیعی دروست دەکات بۆ ئەوەی ناو و لۆگۆی خۆمان لە هۆم سکرین دەربکەوێت)
manifest_js = ""
icon_links_js = ""
if logo_base64:
    manifest_js = f"""
    var manifestObj = {{
        name: "BanuLingua AI",
        short_name: "BanuLingua",
        start_url: ".",
        display: "standalone",
        background_color: "#1a1625",
        theme_color: "#8b5cf6",
        icons: [
            {{ src: "data:image/png;base64,{logo_base64}", sizes: "192x192", type: "image/png" }},
            {{ src: "data:image/png;base64,{logo_base64}", sizes: "512x512", type: "image/png" }}
        ]
    }};
    var manifestBlob = new Blob([JSON.stringify(manifestObj)], {{type: 'application/json'}});
    var manifestURL = URL.createObjectURL(manifestBlob);
    var existingManifest = window.parent.document.querySelector('link[rel="manifest"]');
    if (existingManifest) {{ existingManifest.setAttribute('href', manifestURL); }}
    else {{ addLink('manifest', manifestURL); }}
    """
    icon_links_js = f"""
    addLink("icon", "data:image/png;base64,{logo_base64}");
    addLink("apple-touch-icon", "data:image/png;base64,{logo_base64}");
    """

components.html(f"""
<script>
function addLink(rel, href) {{
    var link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    window.parent.document.head.appendChild(link);
}}
function addMeta(name, content) {{
    var existing = window.parent.document.querySelector('meta[name="' + name + '"]');
    if (existing) {{ existing.setAttribute('content', content); }}
    else {{
        var meta = document.createElement('meta');
        meta.name = name;
        meta.content = content;
        window.parent.document.head.appendChild(meta);
    }}
}}
{icon_links_js}
{manifest_js}
addMeta('apple-mobile-web-app-capable', 'yes');
addMeta('apple-mobile-web-app-title', 'BanuLingua AI');
addMeta('mobile-web-app-capable', 'yes');
addMeta('theme-color', '#8b5cf6');
addMeta('viewport', 'width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover, interactive-widget=resizes-content');

function pinToBottom() {{
    var chatEnd = window.parent.document.getElementById('chat-end');
    if (chatEnd) {{ chatEnd.scrollIntoView({{behavior: 'auto', block: 'end'}}); }}
}}
if (window.parent.visualViewport) {{
    window.parent.visualViewport.addEventListener('resize', pinToBottom);
    window.parent.visualViewport.addEventListener('scroll', pinToBottom);
}}
window.parent.document.addEventListener('focusin', function(e) {{
    if (e.target && (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT')) {{
        setTimeout(pinToBottom, 300);
    }}
}});
</script>
""", height=0, width=0)

# ٣. ڕووکار: ڕەنگی مۆری ئاسوودەبەخش + شاشەی چەسپاو وەک ئەپێکی ڕاستەقینە
st.markdown("""
<style>
html, body {
    overscroll-behavior: none;
}
.stApp {
    background-color: var(--background-color);
    background-image: linear-gradient(135deg,
        rgba(167,139,250,0.12) 0%,
        rgba(196,181,253,0.06) 45%,
        rgba(221,214,254,0.10) 100%);
    height: 100dvh;
    overflow: hidden;
}
[data-testid="stMain"] {
    height: 100dvh;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
}
section[data-testid="stSidebar"] {
    background-color: rgba(139,92,246,0.07);
}
.stButton > button {
    background-color: #8b5cf6;
    color: #ffffff;
    border-radius: 10px;
    border: none;
}
.stButton > button:hover {
    background-color: #7c3aed;
    color: #ffffff;
}
[data-testid="stChatInput"] {
    border-radius: 16px;
}
h1, h2, h3 {
    color: #8b5cf6 !important;
}
.phonetic-guide {
    font-size: 0.8rem;
    opacity: 0.65;
    margin-top: 4px;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

if logo_base64:
    st.markdown(f"""
    <div style="position: sticky; top: 0; z-index: 999; background-color: var(--background-color);
                padding: 14px 0 10px 0; display: flex; align-items: center; gap: 16px;
                border-bottom: 1px solid rgba(139,92,246,0.25);">
        <img src="data:image/png;base64,{logo_base64}" style="width:56px;height:56px;border-radius:12px;">
        <span style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">BanuLingua AI</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="position: sticky; top: 0; z-index: 999; background-color: var(--background-color);
                padding: 14px 0 10px 0; border-bottom: 1px solid rgba(139,92,246,0.25);">
        <span style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">🔮 BanuLingua AI</span>
    </div>
    """, unsafe_allow_html=True)

# ٤. بیرگەی چاتەکە
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ٥. ڕێکخستنەکان لای چەپ
st.sidebar.header("⚙️ ڕێکخستن")
direction = st.sidebar.selectbox("ئاڕاستەی وەرگێڕان:", ["کوردی بۆ ئینگلیزی", "ئینگلیزی بۆ کوردی"])
english_style = st.sidebar.selectbox("شێوازی زمانی ئینگلیزی:", ["ئەمریکی (American)", "بەریتانی (British)", "سەرشەقام و بازاڕی (Slang)"])

API_KEY_FILE = "gemini_key.txt"

def load_saved_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_key(key):
    with open(API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key)

if "api_key" not in st.session_state:
    st.session_state.api_key = load_saved_key()

st.sidebar.markdown("---")
st.sidebar.markdown("🧠 **وەرگێڕانی زیرەک (خۆڕایی - Gemini)**")
api_key = st.sidebar.text_input("Gemini API Key:", type="password", value=st.session_state.api_key)
if api_key != st.session_state.api_key:
    st.session_state.api_key = api_key
    save_key(api_key)
st.sidebar.caption("API keyـی خۆڕایی لە aistudio.google.com وەربگرە - بەبێ کارتی بانکی. جارێک بینووسە، هەمیشە دەمێنێتەوە.")

if st.sidebar.button("🗑 سڕینەوەی مێژوو"):
    st.session_state.chat_history = []
    st.rerun()

# ٦. پیشاندانی نامەکان
for chat in st.session_state.chat_history:
    if chat["type"] == "user":
        st.markdown(f"""
        <div style='background-color: rgba(139,92,246,0.16); color: var(--text-color);
                    padding: 12px 16px; border-radius: 14px; margin-bottom: 10px;
                    direction: rtl; max-width: 85%; margin-left: auto;'>
            {html.escape(chat['text'])}
        </div>
        """, unsafe_allow_html=True)
    else:
        text_direction = "ltr" if "کوردی" in direction else "rtl"
        phonetic_html = ""
        if chat.get("phonetic"):
            phonetic_html = f"<div class='phonetic-guide' dir='rtl'>🔊 {html.escape(chat['phonetic'])}</div>"
        st.markdown(f"""
        <div style='background-color: rgba(196,181,253,0.20); color: var(--text-color);
                    padding: 12px 16px; border-radius: 14px; margin-bottom: 14px;
                    direction: {text_direction}; max-width: 85%; margin-right: auto;'>
            {html.escape(chat['text'])}
            {phonetic_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div id="chat-end"></div>', unsafe_allow_html=True)
st.markdown("""
<script>
    var chatEnd = window.parent.document.getElementById("chat-end");
    if (chatEnd) { chatEnd.scrollIntoView({behavior: "smooth", block: "end"}); }
</script>
""", unsafe_allow_html=True)


# ٧. وەرگێڕانی کۆنتێکستی + ئاوای خوێندنەوە بەکارهێنانی Gemini API (خۆڕایی)
def gemini_translate(text, direction, style):
    to_english = "کوردی بۆ ئینگلیزی" in direction
    if to_english:
        src, tgt = "سۆرانی کوردی", "ئینگلیزی"
    else:
        src, tgt = "ئینگلیزی", "سۆرانی کوردی بە ئەلفوبێی عەرەبی-کوردی"

    style_note = ""
    if to_english:
        if "British" in style:
            style_note = " بە شێوازی ئینگلیزی بەریتانی."
        elif "Slang" in style:
            style_note = " بە شێوازی نائەسمی و سەرشەقامی."
        else:
            style_note = " بە شێوازی ئینگلیزی ئەمریکی."

    phonetic_instruction = ""
    if to_english:
        phonetic_instruction = (
            " هەروەها ئاوای خوێندنەوەی دەقی ئینگلیزییەکە بنووسە بە پیتی کوردی (ئەلفوبێی عەرەبی-کوردی)، "
            "وەک نموونە بۆ وشەی hello بنووسە هێلۆ."
        )

    system_prompt = (
        f"تۆ وەرگێڕێکی پیشەیی و کۆنتێکستیت. دەقی بەکارهێنەر لە {src}ـەوە وەربگێڕە بۆ {tgt}."
        f"{style_note} وەرگێڕانەکە دەبێت سروشتی و ڕەوان بێت، نەک وشە-بە-وشە."
        f"{phonetic_instruction}"
        " وەڵامەکەت تەنها بە فۆرماتی JSON بنووسە بەم شێوەیە، هیچ شتێکی زیاتر، هیچ Markdown، هیچ ```:"
        ' {"translation": "دەقی وەرگێڕدراو", "phonetic": "ئاوای خوێندنەوە بە کوردی یان بەتاڵ ئەگەر پێویست نەبوو"}'
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={st.session_state.api_key}"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }
    resp = requests.post(url, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
        return parsed.get("translation", raw).strip(), parsed.get("phonetic", "").strip()
    except Exception:
        return raw, ""


user_input = st.chat_input("سڵاو، چۆنی؟... ڕستەکەت لێرە بنووسە")

if user_input:
    st.session_state.chat_history.append({"type": "user", "text": user_input})

    translated = None
    phonetic = ""
    if st.session_state.get("api_key"):
        try:
            translated, phonetic = gemini_translate(user_input, direction, english_style)
        except Exception:
            translated = None

    if translated is None:
        try:
            from translators import translate_text
            to_lang = "en" if "کوردی بۆ ئینگلیزی" in direction else "ckb"
            translated = translate_text(user_input, to_language=to_lang, translator="google")
            if to_lang == "en":
                if "Slang" in english_style:
                    translated = f"{translated} (Street style)"
                elif "British" in english_style:
                    translated = translated.replace("color", "colour").replace("flavor", "flavour")
        except Exception:
            if "کوردی بۆ ئینگلیزی" in direction:
                translated = f"Translation of '{user_input}' in {english_style} style"
            else:
                translated = f"وەرگێڕانی '{user_input}' بە شێوازی کوردی"

    st.session_state.chat_history.append({"type": "bot", "text": translated, "phonetic": phonetic})
    st.rerun()
