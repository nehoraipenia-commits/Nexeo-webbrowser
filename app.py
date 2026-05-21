import os
import json
import time
import re
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Permet les requêtes Cross-Origin si le frontend tourne sur un autre port

DB_FILE = 'database.json'

# English stop words to clean query search indexing (Basic NLP)
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
    'will', 'just', 'don', 'should', 'now'
}

DEFAULT_DATABASE = [
    {
        "id": 1,
        "title": "Artificial Intelligence and its Future in 2026",
        "url": "https://www.future-tech.org/artificial-intelligence-2026",
        "description": "What are the major advances in generative AI this year? Full analysis of LLMs, software engineering automation, and autonomous agent workflows in daily life.",
        "category": "web",
        "tags": ["ai", "tech", "future", "artificial intelligence", "agent", "llm"],
        "date": "2026-04-10",
        "author": "Sarah Laporte",
        "image": "https://images.unsplash.com/photo-1677442136019-21780efad99a"
    },
    {
        "id": 2,
        "title": "Traditional French Crêpes Recipe and Secret Cooking Tips",
        "url": "https://www.breizh-cuisine.com/traditional-crepes-recipe",
        "description": "Discover the secret to a light, delicious French crêpe batter. Professional pastry chef tips on selecting fine flour, butter seasoning, and cooking times.",
        "category": "web",
        "tags": ["recipe", "cooking", "crepes", "french", "food", "dessert"],
        "date": "2025-08-15",
        "author": "Jean-Yves Le Gall",
        "image": "https://images.unsplash.com/photo-1519676867240-f03562e64548"
    },
    {
        "id": 3,
        "title": "Mars Exploration: NASA Confirms Ancient River Networks",
        "url": "https://www.space-mag.com/nasa-mars-rivers-discovery",
        "description": "The Perseverance rover has gathered critical sediment samples proving that a vast, complex hydrological network existed on Mars billions of years ago.",
        "category": "news",
        "tags": ["mars", "nasa", "space", "science", "astronomy", "perseverance"],
        "date": "2026-05-12",
        "author": "Dr. Pierre Valo",
        "image": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9"
    },
    {
        "id": 4,
        "title": "Mastering Modern JavaScript Quickly in 2026",
        "url": "https://www.codeacademy.com/courses/modern-javascript-es15",
        "description": "Learn JavaScript from scratch. Step-by-step guide exploring ES15 features, asynchronous operations with async/await, and browser-side reactive frameworks.",
        "category": "web",
        "tags": ["javascript", "code", "development", "web", "programming", "es15"],
        "date": "2026-01-20",
        "author": "Marc Dupont",
        "image": "https://images.unsplash.com/photo-1579468118864-1b9ea3c0db4a"
    },
    {
        "id": 5,
        "title": "History: The Night of August 4, 1789 and the End of Privileges",
        "url": "https://www.history-france.org/revolution/night-august-4-1789",
        "description": "A comprehensive historical study of the National Assembly session that abolished feudal rights and privileges, marking a major turning point of the French Revolution.",
        "category": "web",
        "tags": ["history", "france", "revolution", "archives", "culture"],
        "date": "2023-11-04",
        "author": "Elise Martin",
        "image": "https://images.unsplash.com/photo-1513151233558-d860c5398176"
    },
    {
        "id": 6,
        "title": "Top 10 Most Beautiful Hiking Trails on the French Riviera",
        "url": "https://www.provence-escape.com/hiking-french-riviera-esterel",
        "description": "From the red volcanic cliffs of the Esterel to the coastal paths of Saint-Jean-Cap-Ferrat, plan your next nature excursion between sea and mountains.",
        "category": "web",
        "tags": ["french riviera", "hiking", "nature", "travel", "provence", "sport"],
        "date": "2025-06-02",
        "author": "Julie Brunet",
        "image": "https://images.unsplash.com/photo-1533105079780-92b9be482077"
    }
]

def load_db():
    """Charge la base de données depuis le fichier JSON ou l'initialise."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DATABASE, f, ensure_ascii=False, indent=4)
        return DEFAULT_DATABASE
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DATABASE

def save_db(data):
    """Sauvegarde les documents dans la base de données JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def tokenize(text):
    """Nettoie, normalise et découpe le texte en jetons."""
    if not text:
        return []
    text = text.lower()
    # Supprime les accents basiques
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    # Supprime la ponctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    return [t for t in tokens if len(t) > 1]

def calculate_score(query_tokens, doc):
    """Calcule le score de pertinence d'un document par rapport à la requête."""
    score = 0
    matched = False

    title_tokens = tokenize(doc.get('title', ''))
    desc_tokens = tokenize(doc.get('description', ''))
    url_tokens = tokenize(doc.get('url', ''))
    tag_tokens = [t.lower() for t in doc.get('tags', [])]

    for token in query_tokens:
        # Correspondance exacte/partielle du titre (Poids fort: 15)
        title_matches = sum(1 for t in title_tokens if token in t or t in token)
        if title_matches > 0:
            score += title_matches * 15
            matched = True

        # Correspondance dans les tags (Poids important: 10)
        tag_matches = sum(1 for t in tag_tokens if token in t or t in token)
        if tag_matches > 0:
            score += tag_matches * 10
            matched = True

        # Correspondance dans l'URL (Poids moyen: 4)
        url_matches = sum(1 for t in url_tokens if token in t)
        if url_matches > 0:
            score += url_matches * 4
            matched = True

        # Correspondance dans la description (Poids faible: 2)
        desc_matches = sum(1 for t in desc_tokens if token in t or t in token)
        if desc_matches > 0:
            score += desc_matches * 2
            matched = True

    return score if matched else 0

def levenshtein_distance(s1, s2):
    """Calcule la distance d'édition pour la correction orthographique."""
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def check_spellcheck(query, db):
    """Cherche une suggestion de correction orthographique."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return None

    vocab = set()
    for doc in db:
        vocab.update(tokenize(doc.get('title', '')))
        vocab.update([t.lower() for t in doc.get('tags', [])])

    corrected_tokens = []
    any_correction = False

    for token in query_tokens:
        if token in vocab:
            corrected_tokens.append(token)
        else:
            best_match = token
            best_dist = 999
            for word in vocab:
                dist = levenshtein_distance(token, word)
                if dist < best_dist and dist <= 2:
                    best_dist = dist
                    best_match = word
            
            if best_match != token:
                corrected_tokens.append(best_match)
                any_correction = True
            else:
                corrected_tokens.append(token)

    return " ".join(corrected_tokens) if any_correction else None

@app.route('/')
def serve_index():
    """Sert le fichier frontend index.html."""
    return send_from_directory('.', 'index.html')

@app.route('/api/search', methods=['GET'])
def api_search():
    """Endpoint principal de recherche."""
    start_time = time.time()
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'web')
    sort_by = request.args.get('sort', 'relevance')
    time_filter = request.args.get('time', 'all')

    db = load_db()
    if not query:
        return jsonify({
            "results": db,
            "spellcheck": None,
            "searchTime": 0,
            "totalResults": len(db)
        })

    query_tokens = tokenize(query)
    scored_results = []

    for doc in db:
        score = calculate_score(query_tokens, doc)
        if score > 0:
            scored_results.append({**doc, "searchScore": score})

    # Filtrage de catégorie
    if category == 'web':
        # Web regroupe web et actualités (news)
        scored_results = [r for r in scored_results if r['category'] in ['web', 'news']]
    elif category in ['images', 'news']:
        scored_results = [r for r in scored_results if r['category'] == category]

    # Filtrage temporel
    if time_filter == 'recent':
        scored_results = [r for r in scored_results if r.get('date', '').startswith(('2025', '2026'))]
    elif time_filter == 'archived':
        scored_results = [r for r in scored_results if not r.get('date', '').startswith(('2025', '2026'))]

    # Tri
    if sort_by == 'relevance':
        # Tri principal par score, secondaire par date
        scored_results.sort(key=lambda x: (x['searchScore'], x.get('date', '')), reverse=True)
    elif sort_by == 'title_asc':
        scored_results.sort(key=lambda x: x.get('title', '').lower())
    elif sort_by == 'newest':
        scored_results.sort(key=lambda x: x.get('date', ''), reverse=True)

    search_duration = round(time.time() - start_time, 4)
    spellcheck_suggestion = check_spellcheck(query, db)

    return jsonify({
        "query": query,
        "results": scored_results,
        "spellcheck": spellcheck_suggestion,
        "searchTime": search_duration,
        "totalResults": len(scored_results)
    })

@app.route('/api/suggest', methods=['GET'])
def api_suggest():
    """Auto-complétion."""
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify([])

    db = load_db()
    suggestions = set()

    for doc in db:
        title = doc.get('title', '')
        if query in title.lower():
            suggestions.add(title)
        for tag in doc.get('tags', []):
            if query in tag.lower():
                suggestions.add(tag)

    return jsonify(list(suggestions)[:5])

@app.route('/api/index', methods=['POST'])
def api_index():
    """Endpoint d'indexation (Crawler) : Enregistre une nouvelle page."""
    data = request.json
    if not data or not data.get('title') or not data.get('url') or not data.get('content'):
        return jsonify({"error": "Missing mandatory data: title, url or content required."}), 400

    db = load_db()
    new_id = max([doc['id'] for doc in db]) + 1 if db else 1

    content = data.get('content', '')
    raw_tags_input = data.get('tags', '')
    
    # NLP basique pour extraire des mots clés
    extracted_keywords = [
        token for token in tokenize(content) 
        if token not in STOP_WORDS and len(token) > 3
    ]
    unique_keywords = list(dict.fromkeys(extracted_keywords))[:6]

    user_tags = [t.strip().lower() for t in raw_tags_input.split(',')] if raw_tags_input else []
    merged_tags = list(set(user_tags + unique_keywords))

    # Image par défaut de qualité si non fournie
    img_url = data.get('image') or "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800"

    new_doc = {
        "id": new_id,
        "title": data.get('title'),
        "url": data.get('url'),
        "description": content, # Description mapped to content
        "content": content,
        "category": data.get('category', 'web'),
        "tags": merged_tags,
        "date": time.strftime("%Y-%m-%d"),
        "author": data.get('author') or "Global Web Crawler",
        "image": img_url
    }

    db.append(new_doc)
    save_db(db)

    return jsonify({
        "message": "Page indexed successfully!",
        "document": new_doc,
        "extracted_keywords": unique_keywords
    })

@app.route('/api/document/<int:doc_id>', methods=['GET'])
def api_get_document(doc_id):
    """Informations détaillées d'un document spécifique."""
    db = load_db()
    doc = next((d for d in db if d['id'] == doc_id), None)
    if doc:
        return jsonify(doc)
    return jsonify({"error": "Document not found"}), 404

if __name__ == '__main__':
    load_db()
    print("--------------------------------------------------")
    print("INVENIO Search Engine Engine running on http://127.0.0.1:5000")
    print("--------------------------------------------------")
    app.run(host='127.0.0.1', port=5000, debug=True)