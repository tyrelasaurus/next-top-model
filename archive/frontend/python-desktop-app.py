#!/usr/bin/env python3
"""
Next Top Model - Elite Sports Analytics Desktop App
A standalone Python GUI application using tkinter
"""

import tkinter as tk
from tkinter import ttk, font
import json
from datetime import datetime
import random

class NextTopModelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Next Top Model - Elite Sports Analytics")
        self.root.geometry("1200x800")
        
        # Dark theme colors
        self.bg_color = "#0F0F17"
        self.fg_color = "#E5E7EB"
        self.accent_color = "#A855F7"
        self.secondary_color = "#EC4899"
        
        self.root.configure(bg=self.bg_color)
        
        # Mock data
        self.teams_data = [
            {"name": "Kansas City Chiefs", "score": 98.5, "wins": 49, "losses": 12, "trend": "↑"},
            {"name": "Philadelphia Eagles", "score": 94.2, "wins": 45, "losses": 14, "trend": "→"},
            {"name": "Buffalo Bills", "score": 91.8, "wins": 41, "losses": 16, "trend": "↑"},
            {"name": "Detroit Lions", "score": 89.3, "wins": 38, "losses": 17, "trend": "↑"},
            {"name": "Baltimore Ravens", "score": 86.7, "wins": 37, "losses": 19, "trend": "↓"},
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_font = font.Font(family="Arial", size=32, weight="bold")
        title = tk.Label(main_frame, text="Next Top Model", 
                        font=title_font, bg=self.bg_color, fg=self.accent_color)
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(main_frame, text="Elite Sports Analytics Platform",
                          font=("Arial", 14), bg=self.bg_color, fg=self.fg_color)
        subtitle.pack(pady=(0, 20))
        
        # Tab navigation
        tab_frame = tk.Frame(main_frame, bg=self.bg_color)
        tab_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.tabs = {}
        tab_names = ["🏆 Dashboard", "⭐ Rankings", "📊 Analytics"]
        
        for tab_name in tab_names:
            btn = tk.Button(tab_frame, text=tab_name, font=("Arial", 12, "bold"),
                           bg=self.accent_color, fg="white", bd=0, padx=20, pady=10,
                           command=lambda n=tab_name: self.switch_tab(n))
            btn.pack(side=tk.LEFT, padx=5)
            self.tabs[tab_name] = btn
        
        # Content area
        self.content_frame = tk.Frame(main_frame, bg="#1A1A2E", relief=tk.RAISED, bd=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Show dashboard by default
        self.show_dashboard()
        
    def switch_tab(self, tab_name):
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Update tab colors
        for name, btn in self.tabs.items():
            if name == tab_name:
                btn.configure(bg=self.secondary_color)
            else:
                btn.configure(bg=self.accent_color)
        
        # Show content
        if "Dashboard" in tab_name:
            self.show_dashboard()
        elif "Rankings" in tab_name:
            self.show_rankings()
        elif "Analytics" in tab_name:
            self.show_analytics()
            
    def show_dashboard(self):
        # Metrics grid
        metrics_frame = tk.Frame(self.content_frame, bg="#1A1A2E")
        metrics_frame.pack(fill=tk.X, padx=20, pady=20)
        
        metrics = [
            ("Elite Teams", "32", "NFL Franchises"),
            ("Games Analyzed", "52.8K", "Historical Data"),
            ("Players Tracked", "25.1K", "Active & Historical"),
            ("Model Accuracy", "94.2%", "Prediction Rate")
        ]
        
        for i, (label, value, desc) in enumerate(metrics):
            metric_frame = tk.Frame(metrics_frame, bg="#2D2D44", relief=tk.RAISED, bd=1)
            metric_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            metrics_frame.columnconfigure(i, weight=1)
            
            tk.Label(metric_frame, text=label, font=("Arial", 10), 
                    bg="#2D2D44", fg=self.accent_color).pack(pady=(10, 5))
            tk.Label(metric_frame, text=value, font=("Arial", 24, "bold"),
                    bg="#2D2D44", fg=self.fg_color).pack()
            tk.Label(metric_frame, text=desc, font=("Arial", 9),
                    bg="#2D2D44", fg="#9CA3AF").pack(pady=(5, 10))
        
        # Status
        status_frame = tk.Frame(self.content_frame, bg="#2D2D44", relief=tk.RAISED, bd=1)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = tk.Label(status_frame, text="● System Status: All Systems Operational",
                               font=("Arial", 14), bg="#2D2D44", fg="#10B981")
        status_label.pack(pady=20)
        
    def show_rankings(self):
        # Rankings list
        rankings_frame = tk.Frame(self.content_frame, bg="#1A1A2E")
        rankings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(rankings_frame, text="Elite Team Rankings", 
                font=("Arial", 20, "bold"), bg="#1A1A2E", fg=self.fg_color).pack(pady=(0, 20))
        
        # Create treeview for rankings
        columns = ("Rank", "Team", "Score", "Record", "Trend")
        tree = ttk.Treeview(rankings_frame, columns=columns, show="tree headings", height=10)
        
        # Define headings
        tree.heading("#0", text="", anchor=tk.W)
        tree.heading("Rank", text="Rank", anchor=tk.W)
        tree.heading("Team", text="Team", anchor=tk.W)
        tree.heading("Score", text="Model Score", anchor=tk.W)
        tree.heading("Record", text="Record", anchor=tk.W)
        tree.heading("Trend", text="Trend", anchor=tk.CENTER)
        
        # Configure column widths
        tree.column("#0", width=0, stretch=False)
        tree.column("Rank", width=80)
        tree.column("Team", width=300)
        tree.column("Score", width=150)
        tree.column("Record", width=150)
        tree.column("Trend", width=100)
        
        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2D2D44", foreground=self.fg_color,
                       fieldbackground="#2D2D44", borderwidth=0)
        style.configure("Treeview.Heading", background=self.accent_color, foreground="white")
        
        # Add data
        for i, team in enumerate(self.teams_data, 1):
            tree.insert("", tk.END, values=(
                f"#{i}",
                team["name"],
                f"{team['score']}",
                f"{team['wins']}-{team['losses']}",
                team["trend"]
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
    def show_analytics(self):
        analytics_frame = tk.Frame(self.content_frame, bg="#1A1A2E")
        analytics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(analytics_frame, text="📈", font=("Arial", 72), 
                bg="#1A1A2E", fg=self.accent_color).pack(pady=(50, 20))
        tk.Label(analytics_frame, text="Advanced Analytics Coming Soon",
                font=("Arial", 24, "bold"), bg="#1A1A2E", fg=self.fg_color).pack()
        tk.Label(analytics_frame, text="Predictive modeling and performance insights",
                font=("Arial", 14), bg="#1A1A2E", fg="#9CA3AF").pack(pady=(10, 0))

def main():
    root = tk.Tk()
    app = NextTopModelApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()