
# modules/analytics.py

"""
Modul untuk tracking dan analisis percakapan
Membantu memahami pola interaksi dan efektivitas persona
"""

import os
import json
import datetime
from modules.intent_detector import detect_intent

# Pastikan direktori analytics ada
if not os.path.exists("data/analytics"):
    os.makedirs("data/analytics")

def log_interaction(username, message_type, message, intent=None):
    """
    Mencatat interaksi untuk analisis
    
    Args:
        username (str): Username akun JTRADE
        message_type (str): 'incoming' atau 'outgoing'
        message (str): Isi pesan
        intent (dict, optional): Intent yang terdeteksi (hanya untuk pesan masuk)
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"data/analytics/{username}_{today}.json"
    
    # Jika intent tidak diberikan dan ini pesan masuk, deteksi intent
    if intent is None and message_type == "incoming":
        intent = detect_intent(message)
    
    # Informasi interaksi
    interaction = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": message_type,
        "content_length": len(message),
        "intent": intent if message_type == "incoming" else None
    }
    
    # Baca file yang ada atau buat baru
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"interactions": []}
    else:
        data = {"interactions": []}
    
    # Tambahkan interaksi baru
    data["interactions"].append(interaction)
    
    # Simpan kembali ke file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def get_daily_stats(username, date=None):
    """
    Mendapatkan statistik harian untuk sebuah akun
    
    Args:
        username (str): Username akun JTRADE
        date (str, optional): Tanggal dalam format YYYY-MM-DD
        
    Returns:
        dict: Statistik interaksi harian
    """
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    filename = f"data/analytics/{username}_{date}.json"
    
    if not os.path.exists(filename):
        return {"message": "No data available for this date"}
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Hitung statistik
    incoming = [i for i in data["interactions"] if i["type"] == "incoming"]
    outgoing = [i for i in data["interactions"] if i["type"] == "outgoing"]
    
    # Intent stats
    intent_counts = {}
    for interaction in incoming:
        if interaction.get("intent"):
            for intent_type in interaction["intent"].keys():
                if intent_type in intent_counts:
                    intent_counts[intent_type] += 1
                else:
                    intent_counts[intent_type] = 1
    
    stats = {
        "date": date,
        "total_interactions": len(data["interactions"]),
        "incoming_messages": len(incoming),
        "outgoing_messages": len(outgoing),
        "avg_incoming_length": sum([i["content_length"] for i in incoming]) / len(incoming) if incoming else 0,
        "avg_outgoing_length": sum([i["content_length"] for i in outgoing]) / len(outgoing) if outgoing else 0,
        "intent_distribution": intent_counts
    }
    
    return stats

def get_weekly_stats(username, end_date=None, days=7):
    """
    Mendapatkan statistik mingguan
    
    Args:
        username (str): Username akun JTRADE
        end_date (str, optional): Tanggal akhir periode dalam format YYYY-MM-DD
        days (int): Jumlah hari yang dihitung mundur dari end_date
        
    Returns:
        dict: Statistik interaksi mingguan
    """
    if end_date is None:
        end_date = datetime.datetime.now()
    else:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    # Inisialisasi statistik mingguan
    weekly_stats = {
        "period_start": (end_date - datetime.timedelta(days=days-1)).strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d"),
        "total_interactions": 0,
        "incoming_messages": 0,
        "outgoing_messages": 0,
        "daily_stats": [],
        "intent_distribution": {}
    }
    
    # Hitung untuk setiap hari
    for i in range(days-1, -1, -1):  # Mulai dari hari paling awal
        date = (end_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        daily = get_daily_stats(username, date)
        
        if "message" not in daily:  # Jika ada data
            weekly_stats["total_interactions"] += daily["total_interactions"]
            weekly_stats["incoming_messages"] += daily["incoming_messages"]
            weekly_stats["outgoing_messages"] += daily["outgoing_messages"]
            weekly_stats["daily_stats"].append({
                "date": date,
                "interactions": daily["total_interactions"]
            })
            
            # Gabungkan distribusi intent
            for intent, count in daily.get("intent_distribution", {}).items():
                if intent in weekly_stats["intent_distribution"]:
                    weekly_stats["intent_distribution"][intent] += count
                else:
                    weekly_stats["intent_distribution"][intent] = count
    
    # Hitung rata-rata jika ada data
    if weekly_stats["daily_stats"]:
        weekly_stats["daily_average"] = weekly_stats["total_interactions"] / len(weekly_stats["daily_stats"])
    else:
        weekly_stats["daily_average"] = 0
    
    return weekly_stats

def generate_dashboard_data(username, period_days=30):
    """
    Generate data untuk dashboard analisis
    
    Args:
        username (str): Username akun JTRADE
        period_days (int): Jumlah hari untuk periode analisis
        
    Returns:
        dict: Data untuk dashboard
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=period_days)
    
    dashboard = {
        "username": username,
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": period_days
        },
        "summary": {
            "total_interactions": 0,
            "incoming_messages": 0,
            "outgoing_messages": 0
        },
        "trends": {
            "daily": [],
            "intent_distribution": {},
            "response_times": []
        }
    }
    
    # Hitung untuk setiap hari
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        daily = get_daily_stats(username, date_str)
        
        if "message" not in daily:
            # Update summary
            dashboard["summary"]["total_interactions"] += daily["total_interactions"]
            dashboard["summary"]["incoming_messages"] += daily["incoming_messages"]
            dashboard["summary"]["outgoing_messages"] += daily["outgoing_messages"]
            
            # Add daily trend
            dashboard["trends"]["daily"].append({
                "date": date_str,
                "interactions": daily["total_interactions"],
                "incoming": daily["incoming_messages"],
                "outgoing": daily["outgoing_messages"]
            })
            
            # Update intent distribution
            for intent, count in daily.get("intent_distribution", {}).items():
                if intent in dashboard["trends"]["intent_distribution"]:
                    dashboard["trends"]["intent_distribution"][intent] += count
                else:
                    dashboard["trends"]["intent_distribution"][intent] = count
        
        current_date += datetime.timedelta(days=1)
    
    # Sort intent distribution
    dashboard["trends"]["top_intents"] = sorted(
        dashboard["trends"]["intent_distribution"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return dashboard

def export_analytics(username, format="json", period_days=30):
    """
    Export data analitik ke file
    
    Args:
        username (str): Username akun JTRADE
        format (str): Format export ('json' atau 'csv')
        period_days (int): Jumlah hari untuk periode analisis
        
    Returns:
        str: Path ke file hasil export
    """
    dashboard = generate_dashboard_data(username, period_days)
    
    # Buat direktori export jika belum ada
    if not os.path.exists("data/export"):
        os.makedirs("data/export")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/export/{username}_analytics_{timestamp}"
    
    if format.lower() == "json":
        with open(f"{filename}.json", 'w') as f:
            json.dump(dashboard, f, indent=4)
        return f"{filename}.json"
    
    elif format.lower() == "csv":
        # Implementasi export CSV untuk data harian
        import csv
        with open(f"{filename}_daily.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Total Interactions", "Incoming Messages", "Outgoing Messages"])
            
            for day in dashboard["trends"]["daily"]:
                writer.writerow([
                    day["date"], 
                    day["interactions"], 
                    day["incoming"], 
                    day["outgoing"]
                ])
        
        # Implementasi export CSV untuk distribusi intent
        with open(f"{filename}_intents.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Intent", "Count"])
            
            for intent, count in dashboard["trends"]["intent_distribution"].items():
                writer.writerow([intent, count])
                
        return f"{filename}_daily.csv dan {filename}_intents.csv"
    
    else:
        raise ValueError(f"Format '{format}' tidak didukung. Gunakan 'json' atau 'csv'.")