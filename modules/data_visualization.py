# modules/data_visualization.py

"""
Modul untuk visualisasi data analitik
Menyediakan fungsi-fungsi untuk membuat grafik dan insight dari data analitik
"""

import os
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
from modules.analytics import get_daily_stats, get_weekly_stats, generate_dashboard_data

# Pastikan direktori visualisasi ada
if not os.path.exists("data/visualizations"):
    os.makedirs("data/visualizations")

def plot_daily_interactions(username, days=30, save=True, show=False):
    """
    Plot interaksi harian
    
    Args:
        username (str): Username akun JTRADE
        days (int): Jumlah hari yang akan divisualisasikan
        save (bool): Jika True, simpan grafik ke file
        show (bool): Jika True, tampilkan grafik
        
    Returns:
        str: Path ke file grafik jika save=True
    """
    end_date = datetime.datetime.now()
    
    # Kumpulkan data
    dates = []
    incoming = []
    outgoing = []
    
    for i in range(days-1, -1, -1):
        date = (end_date - datetime.timedelta(days=i))
        date_str = date.strftime("%Y-%m-%d")
        dates.append(date)
        
        stats = get_daily_stats(username, date_str)
        if "message" not in stats:  # Jika ada data
            incoming.append(stats["incoming_messages"])
            outgoing.append(stats["outgoing_messages"])
        else:
            incoming.append(0)
            outgoing.append(0)
    
    # Buat plot
    plt.figure(figsize=(12, 6))
    plt.plot(dates, incoming, 'b-', label='Pesan Masuk')
    plt.plot(dates, outgoing, 'r-', label='Pesan Keluar')
    plt.fill_between(dates, incoming, alpha=0.3, color='blue')
    plt.fill_between(dates, outgoing, alpha=0.3, color='red')
    
    plt.title(f'Interaksi Harian - {username}')
    plt.xlabel('Tanggal')
    plt.ylabel('Jumlah Pesan')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Format tanggal pada sumbu x
    plt.gcf().autofmt_xdate()
    
    # Tampilkan atau simpan
    if save:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/visualizations/{username}_daily_{timestamp}.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        
        if not show:
            plt.close()
        
        return filename
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return None

def plot_intent_distribution(username, days=30, save=True, show=False):
    """
    Plot distribusi intent dari interaksi
    
    Args:
        username (str): Username akun JTRADE
        days (int): Jumlah hari yang akan divisualisasikan
        save (bool): Jika True, simpan grafik ke file
        show (bool): Jika True, tampilkan grafik
        
    Returns:
        str: Path ke file grafik jika save=True
    """
    # Dapatkan data dashboard
    dashboard = generate_dashboard_data(username, days)
    
    # Extract intent distribution
    intents = dashboard["trends"]["intent_distribution"]
    
    if not intents:
        return "No intent data available"
    
    # Sort intents by count
    sorted_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 8 intents, group others
    if len(sorted_intents) > 8:
        top_intents = sorted_intents[:7]
        other_count = sum(count for _, count in sorted_intents[7:])
        if other_count > 0:
            top_intents.append(("Others", other_count))
    else:
        top_intents = sorted_intents
    
    # Extract labels and values for pie chart
    labels = [intent for intent, _ in top_intents]
    values = [count for _, count in top_intents]
    
    # Create pie chart
    plt.figure(figsize=(10, 8))
    explode = [0.1 if i == 0 else 0 for i in range(len(labels))]  # Explode the largest segment
    
    colors = plt.cm.tab10.colors[:len(labels)]
    patches, texts, autotexts = plt.pie(
        values, 
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        shadow=True,
        startangle=90
    )
    
    # Make text properties better
    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_color('white')
    
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title(f'Distribusi Intent - {username} ({days} hari terakhir)', fontsize=16)
    
    # Tampilkan atau simpan
    if save:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/visualizations/{username}_intents_{timestamp}.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        
        if not show:
            plt.close()
        
        return filename
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return None

def plot_weekly_comparison(username, weeks=4, save=True, show=False):
    """
    Plot perbandingan mingguan
    
    Args:
        username (str): Username akun JTRADE
        weeks (int): Jumlah minggu yang akan dibandingkan
        save (bool): Jika True, simpan grafik ke file
        show (bool): Jika True, tampilkan grafik
        
    Returns:
        str: Path ke file grafik jika save=True
    """
    end_date = datetime.datetime.now()
    
    # Data untuk setiap minggu
    weekly_data = []
    week_labels = []
    
    for i in range(weeks):
        week_end = end_date - datetime.timedelta(days=i*7)
        week_start = week_end - datetime.timedelta(days=6)
        
        stats = get_weekly_stats(username, week_end.strftime("%Y-%m-%d"))
        weekly_data.append([
            stats["incoming_messages"],
            stats["outgoing_messages"]
        ])
        
        week_labels.append(f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}")
    
    # Reverse untuk urutan kronologis
    weekly_data.reverse()
    week_labels.reverse()
    
    # Membuat bar chart
    plt.figure(figsize=(12, 6))
    
    width = 0.35
    x = np.arange(len(week_labels))
    
    plt.bar(x - width/2, [week[0] for week in weekly_data], width, label='Incoming')
    plt.bar(x + width/2, [week[1] for week in weekly_data], width, label='Outgoing')
    
    plt.title(f'Perbandingan Mingguan - {username}')
    plt.xlabel('Periode')
    plt.ylabel('Jumlah Pesan')
    plt.xticks(x, week_labels, rotation=45)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Tampilkan atau simpan
    if save:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/visualizations/{username}_weekly_{timestamp}.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        
        if not show:
            plt.close()
        
        return filename
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return None

def generate_report(username, period=30, include_plots=True):
    """
    Generate laporan analitik lengkap
    
    Args:
        username (str): Username akun JTRADE
        period (int): Jumlah hari yang akan dianalisis
        include_plots (bool): Jika True, sertakan visualisasi dalam laporan
        
    Returns:
        dict: Data laporan dan paths ke visualisasi
    """
    # Generate dashboard data
    dashboard = generate_dashboard_data(username, period)
    
    # Buat visualisasi jika diminta
    plots = {}
    if include_plots:
        plots["daily_interactions"] = plot_daily_interactions(username, period)
        plots["intent_distribution"] = plot_intent_distribution(username, period)
        plots["weekly_comparison"] = plot_weekly_comparison(username, (period // 7) + 1)
    
    # Tambahkan beberapa insight
    insights = []
    
    # Insight 1: Volume interaksi
    if dashboard["summary"]["total_interactions"] > 0:
        daily_avg = dashboard["summary"]["total_interactions"] / period
        insights.append({
            "type": "volume",
            "text": f"Rata-rata {daily_avg:.1f} interaksi per hari dari {dashboard['summary']['total_interactions']} total."
        })
    
    # Insight 2: Intent terpopuler
    if dashboard["trends"]["top_intents"]:
        top_intent = dashboard["trends"]["top_intents"][0]
        insights.append({
            "type": "intent",
            "text": f"Intent paling umum adalah '{top_intent[0]}' dengan {top_intent[1]} kemunculan."
        })
    
    # Insight 3: Tren mingguan
    if len(dashboard["trends"]["daily"]) >= 14:
        recent_week = sum(day["interactions"] for day in dashboard["trends"]["daily"][-7:])
        prev_week = sum(day["interactions"] for day in dashboard["trends"]["daily"][-14:-7])
        
        if prev_week > 0:
            change_pct = ((recent_week - prev_week) / prev_week) * 100
            trend_text = "naik" if change_pct > 0 else "turun"
            insights.append({
                "type": "trend",
                "text": f"Interaksi {trend_text} {abs(change_pct):.1f}% dibanding minggu sebelumnya."
            })
    
    # Gabungkan semua menjadi laporan
    report = {
        "dashboard": dashboard,
        "plots": plots,
        "insights": insights,
        "generated_at": datetime.datetime.now().isoformat()
    }
    
    return report

def save_report(report, format="json"):
    """
    Simpan laporan ke file
    
    Args:
        report (dict): Data laporan
        format (str): Format file ('json' atau 'html')
        
    Returns:
        str: Path ke file laporan
    """
    # Pastikan direktori ada
    if not os.path.exists("data/reports"):
        os.makedirs("data/reports")
    
    username = report["dashboard"]["username"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format.lower() == "json":
        filename = f"data/reports/{username}_report_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4)
        return filename
    
    elif format.lower() == "html":
        filename = f"data/reports/{username}_report_{timestamp}.html"
        
        # Create simple HTML report
        with open(filename, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Analitik Report - {username}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
        .insight {{ background-color: #f8f9fa; padding: 10px; border-left: 4px solid #3498db; margin-bottom: 10px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .summary-item {{ text-align: center; padding: 20px; background-color: #f1f2f6; border-radius: 8px; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .summary-label {{ font-size: 14px; color: #7f8c8d; }}
        img {{ max-width: 100%; height: auto; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>JTRADE Analytics Report</h1>
        <p>Username: <strong>{username}</strong></p>
        <p>Periode: {report["dashboard"]["period"]["start"]} - {report["dashboard"]["period"]["end"]} ({report["dashboard"]["period"]["days"]} hari)</p>
        <p>Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="card">
            <h2>Ringkasan</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{report["dashboard"]["summary"]["total_interactions"]}</div>
                    <div class="summary-label">Total Interaksi</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{report["dashboard"]["summary"]["incoming_messages"]}</div>
                    <div class="summary-label">Pesan Masuk</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{report["dashboard"]["summary"]["outgoing_messages"]}</div>
                    <div class="summary-label">Pesan Keluar</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Insights</h2>
            """)
            
            # Add insights
            for insight in report["insights"]:
                f.write(f'<div class="insight">{insight["text"]}</div>\n')
            
            # Add plots if available
            if "plots" in report and report["plots"]:
                f.write("""
        </div>
        
        <div class="card">
            <h2>Visualisasi</h2>
                """)
                
                for plot_name, plot_path in report["plots"].items():
                    if plot_path and isinstance(plot_path, str):
                        # Use relative path for HTML
                        rel_path = os.path.relpath(plot_path, "data/reports")
                        f.write(f'<h3>{plot_name.replace("_", " ").title()}</h3>\n')
                        f.write(f'<img src="../{rel_path}" alt="{plot_name}">\n')
            
            # Close HTML
            f.write("""
        </div>
    </div>
</body>
</html>
            """)
            
        return filename
    
    else:
        raise ValueError(f"Format '{format}' tidak didukung. Gunakan 'json' atau 'html'.")
