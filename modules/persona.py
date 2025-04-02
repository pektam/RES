# modules/persona.py

"""
Modul untuk mengelola persona/identitas akun
Mengkombinasikan profil, konteks, kepribadian, dan gaya
"""

import os
import importlib.util
import json

def get_persona(username):
    """
    Dapatkan persona lengkap untuk username tertentu
    
    Args:
        username (str): Username akun JTRADE
        
    Returns:
        dict: Informasi persona termasuk profil, konteks, kepribadian, dan gaya
    """
    # Persona default jika tidak ditemukan
    persona = {
        "name": "CS JTRADE",
        "gender": "netral",
        "personality": "ramah dan profesional",
        "context": "investment_advisor",
        "style": "formal",
        "background": "memiliki pengetahuan luas tentang investasi",
        "goals": "membantu pengguna dalam menemukan investasi yang tepat"
    }
    
    # Coba muat profil jika ada
    profile_path = f"profil/{username}.py"
    if os.path.exists(profile_path):
        try:
            # Dynamically import the profile module
            spec = importlib.util.spec_from_file_location(f"profil.{username}", profile_path)
            profile_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(profile_module)
            
            # Get profile data
            if hasattr(profile_module, "get_profile"):
                profile_data = profile_module.get_profile()
                persona.update(profile_data)
        except Exception as e:
            print(f"Error loading profile for {username}: {e}")
    
    # Muat konteks jika ada
    context_type = persona.get("context", "investment_advisor")
    context_path = f"persona/contexts/{context_type}.py"
    if os.path.exists(context_path):
        try:
            spec = importlib.util.spec_from_file_location(f"persona.contexts.{context_type}", context_path)
            context_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(context_module)
            
            if hasattr(context_module, "get_context"):
                context_data = context_module.get_context()
                persona["context_details"] = context_data
        except Exception as e:
            print(f"Error loading context for {username}: {e}")
    
    # Muat kepribadian jika ada
    personality_traits = persona.get("personality", "ramah").lower().split(" ")[0]
    personality_path = f"persona/personalities/{personality_traits}.py"
    if os.path.exists(personality_path):
        try:
            spec = importlib.util.spec_from_file_location(f"persona.personalities.{personality_traits}", personality_path)
            personality_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(personality_module)
            
            if hasattr(personality_module, "get_personality"):
                personality_data = personality_module.get_personality()
                persona["personality_details"] = personality_data
        except Exception as e:
            print(f"Error loading personality for {username}: {e}")
    
    # Muat gaya komunikasi jika ada
    style_type = persona.get("style", "formal").lower()
    style_path = f"persona/styles/{style_type}.py"
    if os.path.exists(style_path):
        try:
            spec = importlib.util.spec_from_file_location(f"persona.styles.{style_type}", style_path)
            style_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(style_module)
            
            if hasattr(style_module, "get_style"):
                style_data = style_module.get_style()
                persona["style_details"] = style_data
        except Exception as e:
            print(f"Error loading style for {username}: {e}")
    
    return persona