from functools import lru_cache

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

DEVICE = "cpu"
EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"
INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"

@lru_cache(maxsize=1)
def _load_indic_to_en():
    print("Loading IndicTrans2 (Indic to English)...")
    tokenizer = AutoTokenizer.from_pretrained(INDIC_EN_MODEL, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(INDIC_EN_MODEL, trust_remote_code=True).to(DEVICE)
    model.eval()
    return tokenizer, model

@lru_cache(maxsize=1)
def _load_en_to_indic():
    print("Loading IndicTrans2 (English to Indic)...")
    tokenizer = AutoTokenizer.from_pretrained(EN_INDIC_MODEL, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(EN_INDIC_MODEL, trust_remote_code=True).to(DEVICE)
    model.eval()
    return tokenizer, model

def translate_to_english(text: str, src_lang: str = "hin_Deva") -> str:
    if not text.strip():
        return ""
    tokenizer, model = _load_indic_to_en()

    # ✅ Manually format the input with language tags
    formatted_input = f"{src_lang} eng_Latn {text}"

    inputs = tokenizer(formatted_input, return_tensors="pt", truncation=True).to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=256, num_beams=4)

    return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

def translate_from_english(text: str, tgt_lang: str = "hin_Deva") -> str:
    if not text.strip():
        return ""
    tokenizer, model = _load_en_to_indic()

    # ✅ Manually format the input with language tags
    formatted_input = f"eng_Latn {tgt_lang} {text}"

    inputs = tokenizer(formatted_input, return_tensors="pt", truncation=True).to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=256, num_beams=4)

    return tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

def _cli():
    """CLI entry point for subprocess calls from the main venv."""
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["to_en", "from_en"], required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--lang", default="hin_Deva")
    args = parser.parse_args()

    if args.mode == "to_en":
        result = translate_to_english(args.text, args.lang)
    else:
        result = translate_from_english(args.text, args.lang)

    print(json.dumps({"result": result}, ensure_ascii=False))


if __name__ == "__main__":
    _cli()