# modules/rag_engine.py

"""
Modul RAG (Retrieval-Augmented Generation) untuk JTRADE AUTORESPONDER.AI
Meningkatkan respons dengan mengambil informasi relevan dari knowledge base
"""

import os
import json
import numpy as np
from pathlib import Path

# Pastikan direktori diperlukan ada
KB_DIR = "data/knowledge_base"
EMBED_CACHE_DIR = "data/embeddings"

for dir_path in [KB_DIR, EMBED_CACHE_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

class RAGEngine:
    def __init__(self, embedding_cache_file="data/embeddings/cache.json"):
        """
        Inisialisasi RAG Engine
        """
        self.embedding_cache_file = embedding_cache_file
        self.embeddings = {}
        self.knowledge_data = {}
        
        # Buat direktori untuk cache embeddings jika belum ada
        os.makedirs(os.path.dirname(embedding_cache_file), exist_ok=True)
        
        # Load embeddings dari cache jika ada
        if os.path.exists(embedding_cache_file):
            try:
                with open(embedding_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Konversi string JSON menjadi array numpy
                    self.embeddings = {k: np.array(v) for k, v in cache_data.items()}
                print(f"Loaded {len(self.embeddings)} embeddings from cache")
            except Exception as e:
                print(f"Error loading embeddings: {e}")
        
        # Load knowledge base
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """
        Memuat semua file knowledge base
        """
        for file_path in Path(KB_DIR).glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.knowledge_data[file_path.stem] = data
                print(f"Loaded knowledge base: {file_path.stem}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    def create_simple_embedding(self, text):
        """
        Fungsi sederhana untuk membuat embedding dari teks
        Dalam produksi, gunakan sentence-transformers atau OpenAI embeddings API
        """
        import hashlib
        text_hash = hashlib.md5(text.encode()).digest()
        # Menghasilkan vector 128-dimensi
        return np.array([float(b % 10) for b in text_hash] + [0] * (128 - len(text_hash)), dtype=np.float32)
    
    def cosine_similarity(self, v1, v2):
        """
        Menghitung cosine similarity antara dua vektor
        """
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        return dot_product / (norm_v1 * norm_v2)
    
    def index_knowledge_base(self):
        """
        Mengindeks knowledge base dengan embeddings
        """
        for kb_name, kb_data in self.knowledge_data.items():
            # Flatten knowledge base
            flat_content = self._flatten_dict(kb_data, prefix=kb_name)
            
            # Generate embedding untuk setiap bagian konten
            for key, text in flat_content.items():
                if isinstance(text, str) and len(text) > 10:
                    self.embeddings[key] = self.create_simple_embedding(text)
        
        # Simpan embeddings ke cache
        self._save_embeddings()
        print(f"Indexed {len(self.embeddings)} items from knowledge base")
    
    def _flatten_dict(self, d, prefix="", result=None):
        """
        Flatten nested dict untuk diindeks dengan embedding
        """
        if result is None:
            result = {}
        
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            
            if isinstance(v, dict):
                self._flatten_dict(v, key, result)
            elif isinstance(v, list):
                # Untuk list, tambahkan sebagai joined text jika elemen string
                if all(isinstance(item, str) for item in v):
                    result[key] = " ".join(v)
                # Untuk list yang berisi dict, proses tiap item
                elif any(isinstance(item, dict) for item in v):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            self._flatten_dict(item, f"{key}[{i}]", result)
                        else:
                            result[f"{key}[{i}]"] = str(item)
                else:
                    # Simple list of non-string items
                    result[key] = str(v)
            else:
                result[key] = str(v)
        
        return result
    
    def _save_embeddings(self):
        """
        Menyimpan embeddings ke file cache
        """
        cache_data = {k: v.tolist() for k, v in self.embeddings.items()}
        
        with open(self.embedding_cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def retrieve(self, query, top_k=3):
        """
        Mengambil informasi relevan dengan query
        
        Args:
            query (str): Query pengguna
            top_k (int): Jumlah hasil teratas
            
        Returns:
            list: Daftar item relevan dengan skor
        """
        if not self.embeddings:
            print("No embeddings found. Indexing knowledge base...")
            self.index_knowledge_base()
        
        query_embedding = self.create_simple_embedding(query)
        
        # Hitung similarity untuk semua item
        similarities = []
        for key, embedding in self.embeddings.items():
            score = self.cosine_similarity(query_embedding, embedding)
            similarities.append((key, score))
        
        # Urutkan berdasarkan similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Ambil top_k hasil
        top_results = similarities[:top_k]
        
        # Format hasil
        results = []
        for key, score in top_results:
            # Ekstrak teks dari knowledge base
            text = self._get_text_by_key(key)
            if text:
                results.append({
                    "key": key,
                    "text": text,
                    "score": float(score)
                })
        
        return results
    
    def _get_text_by_key(self, key):
        """
        Mendapatkan teks dari knowledge base berdasarkan key path
        """
        parts = key.split('.')
        kb_name = parts[0]
        
        if kb_name not in self.knowledge_data:
            return None
        
        # Navigate through nested structure
        current = self.knowledge_data[kb_name]
        for part in parts[1:]:
            # Handle array indexing
            if '[' in part and ']' in part:
                idx_part = part.split('[')
                part_name = idx_part[0]
                idx = int(idx_part[1].split(']')[0])
                
                if part_name in current and isinstance(current[part_name], list):
                    if idx < len(current[part_name]):
                        current = current[part_name][idx]
                    else:
                        return None
                else:
                    return None
            else:
                if part in current:
                    current = current[part]
                else:
                    return None
        
        return str(current)

    def augment_prompt(self, persona, query, intent, max_tokens=500):
        """
        Memperkaya prompt dengan informasi relevan dari knowledge base
        
        Args:
            persona (dict): Informasi persona
            query (str): Query dari pengguna
            intent (dict): Intent yang terdeteksi
            max_tokens (int): Estimasi batas token
            
        Returns:
            str: Bagian prompt dengan augmentasi
        """
        # Expand query with intent and persona context
        expanded_query = query
        if intent:
            intent_keywords = " ".join(intent.keys())
            expanded_query = f"{query} {intent_keywords}"
        
        # Add persona context to query
        persona_context = persona.get("context", "")
        persona_query = f"{expanded_query} {persona_context}"
        
        # Retrieve relevant info
        retrieved_info = self.retrieve(persona_query, top_k=3)
        
        # Format for prompt
        if retrieved_info:
            context_parts = ["Informasi relevan dari knowledge base:"]
            char_count = 0
            
            for info in retrieved_info:
                item_text = f"- {info['text']}"
                # Estimate token count (~4 chars per token)
                if (char_count + len(item_text)) / 4 > max_tokens:
                    break
                    
                context_parts.append(item_text)
                char_count += len(item_text)
            
            return "\n".join(context_parts)
        
        return ""