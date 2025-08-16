import unicodedata, re, json, time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

# ===================== Categorias (carregadas de JSON) ===================== #
def load_categories(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

ACTION_CATEGORIES = load_categories("data/action_categories.json")
TARGET_CATEGORIES = load_categories("data/target_categories.json")
CONTEXT_CATEGORIES = load_categories("data/context_categories.json")

# ===================== Estrutura ===================== #
@dataclass
class TokenizedCommand:
    original_text: str
    normalized_text: str
    tokens: List[str]
    classified_tokens: List[Tuple[str, str]]
    action: Optional[str]
    target: Optional[str]
    context: Optional[str]
    confidence: float
    metadata: Dict[str, Any]

# ===================== Config ===================== #
def load_stopwords() -> set:
    try:
        with open("config/stopwords.json", encoding="utf-8") as f:
            return set(json.load(f).get("all", []))
    except Exception:
        return {"o", "a", "os", "as", "de", "do", "da", "no", "na", "por", "para", 
                "em", "com", "e", "ou", "um", "uma", "favor"}

STOPWORDS = load_stopwords()

# ===================== Funções Core ===================== #
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()

def tokenize(text: str) -> List[str]:
    return re.findall(r"[\w\-\.]+|https?://\S+|/\S+", text)

def remove_stopwords(tokens: List[str]) -> Tuple[List[str], List[str]]:
    return [t for t in tokens if t not in STOPWORDS], [t for t in tokens if t in STOPWORDS]


# ===================== Busca Local/Web ===================== #
import os
import requests

def search_local_app(token: str) -> Optional[str]:
    # Busca executáveis no PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for file in os.listdir(path):
                if token.lower() in file.lower():
                    return file
        except Exception:
            continue
    return None


import socket

def validate_website(token: str) -> bool:
    # Tenta acessar como domínio .com e .com.br
    for ext in [".com", ".com.br"]:
        url = f"https://{token}{ext}"
        try:
            import requests
            resp = requests.get(url, timeout=2)
            if resp.status_code < 400:
                return True
        except Exception:
            continue
    return False

def search_web_site(token: str) -> Optional[str]:
    # Busca e valida se existe como site
    if validate_website(token):
        return f"https://{token}.com"
    return None

def add_to_category(token: str, category: str, file_path: str):
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        if category not in data:
            data[category] = []
        if token not in data[category]:
            data[category].append(token)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def classify_token(token: str) -> Optional[str]:
    for cat, words in ACTION_CATEGORIES.items():
        if token in words: return f"ACTION_{cat}"
    for cat, words in TARGET_CATEGORIES.items():
        if token in words: return f"TARGET_{cat.rstrip('S')}"
    for cat, words in CONTEXT_CATEGORIES.items():
        if token in words: return f"CONTEXT_{cat}"

    # Primeiro tenta validar como site
    site_found = search_web_site(token)
    if site_found:
        add_to_category(token, "WEBSITES", "data/target_categories.json")
        TARGET_CATEGORIES["WEBSITES"].append(token)
        return "TARGET_WEBSITE"

    # Se não for site, tenta buscar como app local
    app_found = search_local_app(token)
    if app_found:
        add_to_category(token, "APPLICATIONS", "data/target_categories.json")
        TARGET_CATEGORIES["APPLICATIONS"].append(token)
        return "TARGET_APPLICATION"

    # Se não encontrar nada, pede caminho/link ao usuário
    print(f"[Assistente] Não encontrei '{token}' como site ou aplicativo.")
    caminho = input(f"Por favor, informe o caminho do aplicativo ou o link do site para '{token}': ")
    if caminho.startswith("http"):
        add_to_category(token, "WEBSITES", "data/target_categories.json")
        TARGET_CATEGORIES["WEBSITES"].append(token)
        return "TARGET_WEBSITE"
    else:
        add_to_category(token, "APPLICATIONS", "data/target_categories.json")
        TARGET_CATEGORIES["APPLICATIONS"].append(token)
        return "TARGET_APPLICATION"
    return None

def classify_tokens(tokens: List[str]) -> List[Tuple[str, str]]:
    return [(t, c) for t in tokens if (c := classify_token(t))]

def extract_main(classified: List[Tuple[str, str]]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    action = next((c.replace("ACTION_", "") for _, c in classified if c.startswith("ACTION_")), None)
    target = next((t for t, c in classified if c.startswith("TARGET_")), None)
    context = next((t for t, c in classified if c.startswith("CONTEXT_")), None)
    return action, target, context

def calculate_confidence(classified: List[Tuple[str, str]], total_tokens: int) -> float:
    score = 0.0
    cats = [c for _, c in classified]
    score += 0.4 * any(c.startswith("ACTION_") for c in cats)
    score += 0.4 * any(c.startswith("TARGET_") for c in cats)
    score += 0.1 * any(c.startswith("CONTEXT_") for c in cats)
    score -= 0.2 * (total_tokens - len(classified))
    return max(0.0, min(1.0, score))

# ===================== Pipeline ===================== #
def autotokenize(text: str) -> TokenizedCommand:
    start = time.time()
    norm = normalize(text)
    tokens = tokenize(norm)
    filtered, removed = remove_stopwords(tokens)
    classified = classify_tokens(filtered)
    action, target, context = extract_main(classified)
    confidence = calculate_confidence(classified, len(filtered))
    
    return TokenizedCommand(
        original_text=text,
        normalized_text=norm,
        tokens=filtered,
        classified_tokens=classified,
        action=action,
        target=target,
        context=context,
        confidence=confidence,
        metadata={
            "processing_time_ms": int((time.time() - start) * 1000),
            "tokens_removed": removed,
            "classification_method": "exact_match"
        }
    )

# ===================== Teste ===================== #
if __name__ == "__main__":
    from pprint import pprint
    pprint(autotokenize("abrir o YouTube no Chrome por favor"))
