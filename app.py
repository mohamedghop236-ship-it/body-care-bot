def get_exercise_gif(query_text: str):
    giphy_key = None
    try:
        if "GIPHY_API_KEY" in st.secrets:
            giphy_key = st.secrets["GIPHY_API_KEY"]
    except Exception:
        pass

    if not giphy_key:
        giphy_key = os.environ.get("GIPHY_API_KEY")

    # روابط احتياطية عامة وشائعة للياقة والتمارين
    fallback_gifs = {
        "ضغط": "https://media.giphy.com/media/7Yeze6y8B6q3e/giphy.gif",
        "push": "https://media.giphy.com/media/7Yeze6y8B6q3e/giphy.gif",
        "بلانك": "https://media.giphy.com/media/3o7TKV58in42Y5T2mY/giphy.gif",
        "plank": "https://media.giphy.com/media/3o7TKV58in42Y5T2mY/giphy.gif",
        "عقلة": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "pull": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    }

    lowered = query_text.lower()
    search_term = None
    for arabic_key, gif_url in fallback_gifs.items():
        if arabic_key in lowered:
            search_term = arabic_key
            break

    if giphy_key:
        import urllib.parse
        import urllib.request
        import json as _json

        term = "squat workout exercise"
        if "ضغط" in lowered or "push" in lowered:
            term = "push up workout exercise"
        elif "بلانك" in lowered or "plank" in lowered:
            term = "plank workout exercise"
        elif "عقلة" in lowered or "pull" in lowered:
            term = "pull up workout exercise"
        elif "معدة" in lowered or "abs" in lowered:
            term = "abs workout exercise"

        q = urllib.parse.quote(term)
        url = f"https://api.giphy.com/v1/gifs/search?api_key={giphy_key}&q={q}&limit=1&rating=g"
        try:
            with urllib.request.urlopen(url, timeout=6) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                if items:
                    return items[0]["images"]["original"]["url"]
        except Exception:
            pass

    if search_term in fallback_gifs:
        return fallback_gifs[search_term]

    return None
