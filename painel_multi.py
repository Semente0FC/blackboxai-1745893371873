import tkinter as tk
from tkinter import ttk, messagebox
import MetaTrader5 as mt5
from utils import obter_saldo
from src.multi_asset_trading import MultiAssetTrading
from src.multi_asset_log_system import MultiAssetLogSystem
import threading
import time
from datetime import datetime

class PainelMultiAsset:
    def __init__(self, root):
        self.root = root
        self.root.title("Future MT5 Pro Trading - Multi Asset")

        # Theme colors
        self.dark_theme = {
            'bg_dark': '#0A0A0A',
            'bg_medium': '#1E1E1E',
            'bg_light': '#2D2D2D',
            'accent': '#00C853',
            'accent_hover': '#00E676',
            'warning': '#FFB300',
            'danger': '#FF3D00',
            'text': '#FFFFFF',
            'text_secondary': '#B3B3B3'
        }

        self.colors = self.dark_theme
        self.root.configure(bg=self.colors['bg_dark'])
        self.root.resizable(False, False)
        self.centralizar_janela(1200, 800)

        # Initialize trading system
        self.multi_trading = MultiAssetTrading()
        self.log_system = MultiAssetLogSystem()
        
        # Asset configurations
        self.asset_configs = []
        for i in range(4):
            self.asset_configs.append({
                'ativo': tk.StringVar(),
                'timeframe': tk.StringVar(value="M5"),
                'lote': tk.StringVar(value="0.10"),
                'status': "parado"
            })

        self.setup_ui()
        self.start_update_threads()

    def centralizar_janela(self, largura, altura):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

    def setup_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'], padx=20, pady=20)
        main_container.pack(fill="both", expand=True)

        # Header with balance
        self.setup_header(main_container)

        # Asset configuration panels
        self.setup_asset_panels(main_container)

        # Global controls
        self.setup_global_controls(main_container)

        # Log panel
        self.setup_log_panel(main_container)

    def setup_header(self, parent):
        header = tk.Frame(parent, bg=self.colors['bg_dark'])
        header.pack(fill="x", pady=(0, 20))

        # Title
        title_container = tk.Frame(header, bg=self.colors['bg_dark'])
        title_container.pack(side="left")

        tk.Label(
            title_container,
            text="📈",
            font=("Helvetica", 32),
            fg=self.colors['accent'],
            bg=self.colors['bg_dark']
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            title_container,
            text="FUTURE MT5 PRO MULTI-ASSET",
            font=("Helvetica", 24, "bold"),
            fg=self.colors['text'],
            bg=self.colors['bg_dark']
        ).pack(side="left")

        # Balance
        self.saldo_frame = tk.Frame(header, bg=self.colors['bg_light'], padx=15, pady=10)
        self.saldo_frame.pack(side="right")

        tk.Label(
            self.saldo_frame,
            text="SALDO",
            font=("Helvetica", 10, "bold"),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light']
        ).pack()

        self.saldo_label = tk.Label(
            self.saldo_frame,
            text="R$ 0.00",
            font=("Helvetica", 18, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['bg_light']
        )
        self.saldo_label.pack()

    def setup_asset_panels(self, parent):
        assets_container = tk.Frame(parent, bg=self.colors['bg_dark'])
        assets_container.pack(fill="x", pady=(0, 20))

        # Create 4 asset panels in a 2x2 grid
        for i in range(4):
            row = i // 2
            col = i % 2
            self.create_asset_panel(assets_container, i, row, col)

    def create_asset_panel(self, parent, index, row, col):
        panel = tk.Frame(parent, bg=self.colors['bg_medium'], padx=15, pady=15)
        panel.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Asset selection
        tk.Label(
            panel,
            text=f"Ativo {index + 1}",
            font=("Helvetica", 12, "bold"),
            fg=self.colors['text'],
            bg=self.colors['bg_medium']
        ).pack(anchor="w")

        combo_ativo = ttk.Combobox(
            panel,
            textvariable=self.asset_configs[index]['ativo'],
            width=20
        )
        combo_ativo.pack(pady=(5, 10))

        # Timeframe and lot size
        controls_frame = tk.Frame(panel, bg=self.colors['bg_medium'])
        controls_frame.pack(fill="x")

        ttk.Combobox(
            controls_frame,
            textvariable=self.asset_configs[index]['timeframe'],
            values=["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
            width=10
        ).pack(side="left", padx=(0, 5))

        tk.Entry(
            controls_frame,
            textvariable=self.asset_configs[index]['lote'],
            width=8
        ).pack(side="left", padx=5)

        # Individual start/stop button
        self.create_control_button(panel, index)

    def create_control_button(self, parent, index):
        btn = tk.Button(
            parent,
            text="▶ Iniciar",
            command=lambda: self.toggle_asset(index),
            font=("Helvetica", 10, "bold"),
            fg=self.colors['text'],
            bg=self.colors['accent'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text'],
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        btn.pack(pady=(10, 0))
        return btn

    def setup_global_controls(self, parent):
        controls = tk.Frame(parent, bg=self.colors['bg_medium'], padx=20, pady=15)
        controls.pack(fill="x", pady=(0, 20))

        # Update assets button
        tk.Button(
            controls,
            text="🔄 Atualizar Ativos",
            command=self.carregar_ativos,
            font=("Helvetica", 11, "bold"),
            fg=self.colors['text'],
            bg=self.colors['bg_light'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text'],
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side="left")

        # Global start/stop buttons
        tk.Button(
            controls,
            text="▶ Iniciar Todos",
            command=self.iniciar_todos,
            font=("Helvetica", 11, "bold"),
            fg=self.colors['text'],
            bg=self.colors['accent'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text'],
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side="right", padx=(0, 10))

        tk.Button(
            controls,
            text="⏹ Parar Todos",
            command=self.parar_todos,
            font=("Helvetica", 11, "bold"),
            fg=self.colors['text'],
            bg=self.colors['danger'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text'],
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side="right")

    def setup_log_panel(self, parent):
        # Create log interface for 4 assets
        ativos = [f"Ativo {i+1}" for i in range(4)]
        self.log_system.criar_interface_logs(parent, ativos)

    def carregar_ativos(self):
        try:
            symbols = mt5.symbols_get()
            lista_ativos = [symbol.name for symbol in symbols if symbol.visible]
            
            for config in self.asset_configs:
                combo = self.root.nametowidget(config['ativo']._name)
                combo['values'] = lista_ativos
                if lista_ativos:
                    combo.current(0)
            
            self.log_system.logar("Sistema", "✅ Ativos atualizados com sucesso!")
        except Exception as e:
            self.log_system.logar("Sistema", f"❌ Erro ao carregar ativos: {e}")

    def toggle_asset(self, index):
        config = self.asset_configs[index]
        ativo = config['ativo'].get().strip()
        
        if not self.validar_configuracao(index):
            return

        if config['status'] == "parado":
            self.iniciar_ativo(index)
        else:
            self.parar_ativo(index)

    def validar_configuracao(self, index):
        config = self.asset_configs[index]
        ativo = config['ativo'].get().strip()
        timeframe = config['timeframe'].get().strip()
        lote = config['lote'].get().strip()

        if not ativo:
            self.log_system.logar(f"Ativo {index+1}", "⚠️ Selecione um ativo para operar!")
            return False

        if not timeframe:
            self.log_system.logar(f"Ativo {index+1}", "⚠️ Selecione um timeframe para operar!")
            return False

        try:
            lote_float = float(lote)
            if lote_float <= 0:
                self.log_system.logar(f"Ativo {index+1}", "⚠️ O lote deve ser maior que zero!")
                return False
        except ValueError:
            self.log_system.logar(f"Ativo {index+1}", "❌ Valor de lote inválido!")
            return False

        return True

    def iniciar_ativo(self, index):
        config = self.asset_configs[index]
        ativo = config['ativo'].get().strip()
        
        # Validate market conditions
        info = mt5.symbol_info(ativo)
        if not self.validar_mercado(info, ativo, index):
            return

        # Start trading
        config['status'] = "operando"
        self.multi_trading.adicionar_ativo(
            ativo,
            config['timeframe'].get(),
            float(config['lote'].get()),
            self.log_system
        )
        
        self.log_system.logar(f"Ativo {index+1}", f"✅ Iniciando operações em {ativo}")

    def validar_mercado(self, info, ativo, index):
        if info is None:
            self.log_system.logar(f"Ativo {index+1}", f"❌ Ativo {ativo} não encontrado no MetaTrader 5.")
            return False

        if not info.visible:
            self.log_system.logar(f"Ativo {index+1}", f"⚠️ Ativo {ativo} não está visível no MT5!")
            return False

        if info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
            self.log_system.logar(f"Ativo {index+1}", f"❌ Ativo {ativo} não está liberado para operar!")
            return False

        tick = mt5.symbol_info_tick(ativo)
        if tick is None:
            self.log_system.logar(f"Ativo {index+1}", f"❌ Não foi possível obter preços do ativo {ativo}.")
            return False

        spread = (tick.ask - tick.bid) / info.point
        if spread > 50:  # Maximum acceptable spread
            self.log_system.logar(f"Ativo {index+1}", f"⚠️ Spread muito alto ({spread:.1f} pontos)!")
            return False

        if tick.bid == 0 or tick.ask == 0:
            self.log_system.logar(f"Ativo {index+1}", f"⚠️ Mercado FECHADO para {ativo}!")
            return False

        return True

    def parar_ativo(self, index):
        config = self.asset_configs[index]
        ativo = config['ativo'].get().strip()
        
        config['status'] = "parado"
        self.multi_trading.remover_ativo(ativo)
        self.log_system.logar(f"Ativo {index+1}", f"🛑 Operações paradas em {ativo}")

    def iniciar_todos(self):
        for i in range(4):
            if self.asset_configs[i]['status'] == "parado":
                self.iniciar_ativo(i)

    def parar_todos(self):
        for i in range(4):
            if self.asset_configs[i]['status'] == "operando":
                self.parar_ativo(i)

    def start_update_threads(self):
        threading.Thread(target=self.atualizar_saldo_loop, daemon=True).start()
        self.carregar_ativos()

    def atualizar_saldo_loop(self):
        while True:
            try:
                saldo = obter_saldo()
                self.saldo_label.config(text=f"R$ {saldo:.2f}")
            except:
                pass
            time.sleep(5)

if __name__ == "__main__":
    root = tk.Tk()
    app = PainelMultiAsset(root)
    root.mainloop()
