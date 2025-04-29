import tkinter as tk
from tkinter import ttk
from datetime import datetime

class MultiAssetLogSystem:
    def __init__(self):
        self.logs = {}
        self.interfaces = {}
        self.tabs = None
        self.notebook = None

    def criar_interface_logs(self, parent, ativos):
        """Create tabbed interface for multiple asset logs"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Create tab for each asset
        for ativo in ativos:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=ativo)

            # Create text widget for logs
            text_log = tk.Text(
                frame,
                height=15,
                bg='#1E1E1E',
                fg='white',
                insertbackground='white',
                relief="flat",
                font=("Consolas", 11),
                padx=15,
                pady=15
            )
            text_log.pack(side="left", fill="both", expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, command=text_log.yview)
            scrollbar.pack(side="right", fill="y")
            text_log.config(yscrollcommand=scrollbar.set)

            # Store interface reference
            self.interfaces[ativo] = text_log
            self.logs[ativo] = []

        # Create combined view tab
        combined_frame = ttk.Frame(self.notebook)
        self.notebook.add(combined_frame, text="Visão Geral")

        combined_log = tk.Text(
            combined_frame,
            height=15,
            bg='#1E1E1E',
            fg='white',
            insertbackground='white',
            relief="flat",
            font=("Consolas", 11),
            padx=15,
            pady=15
        )
        combined_log.pack(side="left", fill="both", expand=True)

        combined_scrollbar = ttk.Scrollbar(combined_frame, command=combined_log.yview)
        combined_scrollbar.pack(side="right", fill="y")
        combined_log.config(yscrollcommand=combined_scrollbar.set)

        self.interfaces['combined'] = combined_log

    def logar(self, ativo, mensagem):
        """Log message for specific asset"""
        if ativo not in self.logs:
            self.logs[ativo] = []

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {mensagem}\n"
        
        # Add to asset specific log
        if ativo in self.interfaces:
            self.interfaces[ativo].insert("end", log_entry)
            self.interfaces[ativo].see("end")
            self.logs[ativo].append(log_entry)

        # Add to combined view with asset identifier
        if 'combined' in self.interfaces:
            combined_entry = f"[{timestamp}] [{ativo}] {mensagem}\n"
            self.interfaces['combined'].insert("end", combined_entry)
            self.interfaces['combined'].see("end")

    def limpar_logs(self, ativo=None):
        """Clear logs for specific asset or all assets"""
        if ativo and ativo in self.interfaces:
            self.interfaces[ativo].delete(1.0, "end")
            self.logs[ativo] = []
        elif ativo is None:
            for interface in self.interfaces.values():
                interface.delete(1.0, "end")
            self.logs = {k: [] for k in self.logs}
