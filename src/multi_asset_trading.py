import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import time
import threading
from datetime import datetime

class MultiAssetTrading:
    def __init__(self):
        self.estrategias = {}
        self.lock = threading.Lock()
        self.operando = True

    def adicionar_ativo(self, ativo, timeframe, lote, log_system):
        """Add new asset for trading"""
        with self.lock:
            if ativo not in self.estrategias:
                self.estrategias[ativo] = EstrategiaTrading(ativo, timeframe, lote, log_system)
                return True
            return False

    def remover_ativo(self, ativo):
        """Remove asset from trading"""
        with self.lock:
            if ativo in self.estrategias:
                self.estrategias[ativo].parar()
                del self.estrategias[ativo]
                return True
            return False

    def iniciar_todos(self):
        """Start trading for all assets"""
        self.operando = True
        for ativo, estrategia in self.estrategias.items():
            threading.Thread(target=estrategia.executar, daemon=True).start()

    def parar_todos(self):
        """Stop trading for all assets"""
        self.operando = False
        for estrategia in self.estrategias.values():
            estrategia.parar()

    def get_status(self, ativo):
        """Get trading status for specific asset"""
        return self.estrategias.get(ativo, None)

class EstrategiaTrading:
    def __init__(self, ativo, timeframe, lote, log_system):
        self.ativo = ativo
        self.timeframe = self.converter_timeframe(timeframe)
        self.lote = float(lote)
        self.operando = True
        self.log_system = log_system
        self.ticket_atual = None

        # Parâmetros otimizados para mais oportunidades
        self.rsi_sobrecomprado = 70  # RSI mais permissivo
        self.rsi_sobrevendido = 30
        self.bb_desvio = 1.8  # Bandas mais próximas para mais sinais
        self.atr_period = 10  # ATR mais sensível
        self.stoch_period = 10  # Estocástico mais sensível
        self.volume_threshold = 1.2  # Volume menos restritivo

        # Parâmetros de gestão de risco otimizados
        self.max_daily_loss = 3.0  # Proteção de capital mais rigorosa
        self.min_rr_ratio = 1.2  # Permite trades com menor reward
        self.max_positions = 3  # Limita posições por segurança
        self.trailing_stop = True
        self.breakeven_level = 0.3  # Breakeven mais rápido

    def converter_timeframe(self, tf):
        mapping = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        return mapping.get(tf, mt5.TIMEFRAME_M5)

    def executar(self):
        while self.operando:
            try:
                self.analisar_e_operar()
                time.sleep(5)
            except Exception as e:
                self.log_system.logar(self.ativo, f"❌ Erro na estratégia: {str(e)}")
                time.sleep(10)

    def parar(self):
        self.operando = False

    def analisar_e_operar(self):
        try:
            if self.operando:
                self.log_system.logar(self.ativo, "🔍 Iniciando análise de mercado...")

            barras = mt5.copy_rates_from_pos(self.ativo, self.timeframe, 0, 200)
            if barras is None or len(barras) < 100:
                self.log_system.logar(self.ativo, f"❌ Erro: Não foi possível carregar velas de {self.ativo}")
                return

            df = pd.DataFrame(barras)
            if df.isnull().any().any():
                self.log_system.logar(self.ativo, "❌ Erro: Dados inválidos ou nulos detectados")
                return

            # Cálculos básicos
            try:
                close = df['close'].values
                high = df['high'].values
                low = df['low'].values
                volume = df['tick_volume'].values

                if len(close) < 50:
                    self.log_system.logar(self.ativo, "❌ Erro: Dados insuficientes para análise")
                    return

                # Indicadores principais
                try:
                    ema9 = self.ema(close, 9)
                    ema21 = self.ema(close, 21)
                    ema50 = self.ema(close, 50)

                    macd_line, signal_line = self.macd(close)
                    rsi_valores = self.rsi(close, 14)
                    bb_superior, bb_medio, bb_inferior = self.bollinger_bands(close, 20, self.bb_desvio)
                    stoch_k, stoch_d = self.stochastic(high, low, close, self.stoch_period)
                    atr = self.atr(high, low, close, self.atr_period)
                    momentum = self.momentum(close, 10)

                    # Verificar indicadores
                    if any(map(np.isnan, [ema9[-1], ema21[-1], ema50[-1], macd_line[-1], rsi_valores[-1]])):
                        self.log_system.logar(self.ativo, "❌ Erro: Indicadores com valores inválidos")
                        return

                    # Volume analysis
                    volume_ma = float(np.mean(volume[-20:]))
                    volume_atual = float(volume[-1])
                    volume_alto = bool(volume_atual > (volume_ma * self.volume_threshold))

                    # Análise de sinais
                    try:
                        # Tendência com condições otimizadas
                        tendencia_alta = bool(np.all([
                            float(ema9[-1]) > float(ema21[-1]),  # EMA curta acima da média
                            float(close[-1]) > float(ema21[-1]),  # Preço acima da média
                            float(momentum[-1]) > 0,  # Momentum positivo
                            # Novas condições de força da tendência
                            float(close[-1]) > float(close[-2]),  # Último candle fechou em alta
                            float(low[-1]) > float(low[-2])  # Suporte crescente
                        ]))

                        tendencia_baixa = bool(np.all([
                            float(ema9[-1]) < float(ema21[-1]),  # EMA curta abaixo da média
                            float(close[-1]) < float(ema21[-1]),  # Preço abaixo da média
                            float(momentum[-1]) < 0,  # Momentum negativo
                            # Novas condições de força da tendência
                            float(close[-1]) < float(close[-2]),  # Último candle fechou em baixa
                            float(high[-1]) < float(high[-2])  # Resistência decrescente
                        ]))

                        # Força da tendência (usado para logging)
                        forca_tendencia = 0
                        if tendencia_alta:
                            forca_tendencia = sum([
                                float(ema9[-1]) > float(ema9[-2]),
                                float(ema21[-1]) > float(ema21[-2]),
                                float(close[-1]) > float(bb_medio[-1]),
                                float(stoch_k[-1]) > float(stoch_k[-2]),
                                volume_alto
                            ])
                        elif tendencia_baixa:
                            forca_tendencia = sum([
                                float(ema9[-1]) < float(ema9[-2]),
                                float(ema21[-1]) < float(ema21[-2]),
                                float(close[-1]) < float(bb_medio[-1]),
                                float(stoch_k[-1]) < float(stoch_k[-2]),
                                volume_alto
                            ])

                        # RSI com confirmação de reversão
                        rsi_compra = bool(np.all([
                            float(rsi_valores[-1]) < self.rsi_sobrevendido,
                            float(rsi_valores[-1]) > float(rsi_valores[-2]),
                            float(rsi_valores[-2]) > float(rsi_valores[-3])  # Confirmação de reversão
                        ]))

                        rsi_venda = bool(np.all([
                            float(rsi_valores[-1]) > self.rsi_sobrecomprado,
                            float(rsi_valores[-1]) < float(rsi_valores[-2]),
                            float(rsi_valores[-2]) < float(rsi_valores[-3])  # Confirmação de reversão
                        ]))

                        # MACD
                        macd_compra = bool(np.all([
                            float(macd_line[-1]) > float(signal_line[-1]),
                            float(macd_line[-1]) > float(macd_line[-2])
                        ]))

                        macd_venda = bool(np.all([
                            float(macd_line[-1]) < float(signal_line[-1]),
                            float(macd_line[-1]) < float(macd_line[-2])
                        ]))

                        # Sinais finais com condições otimizadas para mais oportunidades
                        sinal_compra = bool(np.all([
                            # Condição principal: Tendência OU (RSI + MACD)
                            tendencia_alta or (rsi_compra and macd_compra),
                            # Condições de confirmação (precisa atender pelo menos 2)
                            sum([
                                float(close[-1]) < float(bb_superior[-1]),  # Preço abaixo da banda superior
                                float(stoch_k[-1]) < 80,  # Estocástico não sobrecomprado
                                volume_alto,  # Volume significativo
                                float(momentum[-1]) > 0,  # Momentum positivo
                                float(ema9[-1]) > float(ema9[-2])  # EMA9 subindo
                            ]) >= 2,
                            self.verificar_horario_favoravel(),
                            self.verificar_risco_posicao()
                        ]))

                        sinal_venda = bool(np.all([
                            # Condição principal: Tendência OU (RSI + MACD)
                            tendencia_baixa or (rsi_venda and macd_venda),
                            # Condições de confirmação (precisa atender pelo menos 2)
                            sum([
                                float(close[-1]) > float(bb_inferior[-1]),  # Preço acima da banda inferior
                                float(stoch_k[-1]) > 20,  # Estocástico não sobrevendido
                                volume_alto,  # Volume significativo
                                float(momentum[-1]) < 0,  # Momentum negativo
                                float(ema9[-1]) < float(ema9[-2])  # EMA9 descendo
                            ]) >= 2,
                            self.verificar_horario_favoravel(),
                            self.verificar_risco_posicao()
                        ]))

                        # Log detalhado das condições com força da tendência
                        if self.operando and (tendencia_alta or tendencia_baixa):
                            direcao = "ALTA 📈" if tendencia_alta else "BAIXA 📉"
                            forca = "⭐" * forca_tendencia  # Visualização da força (1 a 5 estrelas)
                            
                            self.log_system.logar(self.ativo, f"📊 Análise Detalhada - Tendência de {direcao}")
                            self.log_system.logar(self.ativo, f"  • Força da Tendência: {forca} ({forca_tendencia}/5)")
                            self.log_system.logar(self.ativo, f"  • RSI: {rsi_valores[-1]:.2f} {'🔴' if rsi_valores[-1] > 70 else '🟢' if rsi_valores[-1] < 30 else '⚪'}")
                            self.log_system.logar(self.ativo, f"  • Estocástico K: {stoch_k[-1]:.2f} {'🔴' if stoch_k[-1] > 80 else '🟢' if stoch_k[-1] < 20 else '⚪'}")
                            self.log_system.logar(self.ativo, f"  • Momentum: {momentum[-1]:.2f} {'📈' if momentum[-1] > 0 else '📉'}")
                            self.log_system.logar(self.ativo, f"  • Volume: {'Alto ✅' if volume_alto else 'Normal ⚠️'}")
                            self.log_system.logar(self.ativo, f"  • MACD: {'Positivo ✅' if macd_line[-1] > signal_line[-1] else 'Negativo ❌'}")
                            
                            # Adiciona informações sobre possíveis sinais
                            if tendencia_alta and rsi_compra:
                                self.log_system.logar(self.ativo, "  • Possível oportunidade de COMPRA se confirmada ⏳")
                            elif tendencia_baixa and rsi_venda:
                                self.log_system.logar(self.ativo, "  • Possível oportunidade de VENDA se confirmada ⏳")

                        # Logs de sinais
                        if tendencia_alta and self.operando:
                            self.log_system.logar(self.ativo, "📈 Tendência de ALTA detectada - Aguardando confirmação")
                            if macd_compra or rsi_compra:
                                self.log_system.logar(self.ativo, "🎯 Confirmação técnica positiva")

                        if tendencia_baixa and self.operando:
                            self.log_system.logar(self.ativo, "📉 Tendência de BAIXA detectada - Aguardando confirmação")
                            if macd_venda or rsi_venda:
                                self.log_system.logar(self.ativo, "🎯 Confirmação técnica negativa")

                        # Execução otimizada com base na força da tendência
                        if sinal_compra:
                            self.log_system.logar(self.ativo, "✅ SINAL DE COMPRA CONFIRMADO")
                            # Ajusta SL e TP baseado na força da tendência
                            sl_multiplier = max(1.0, min(1.5, 1 + (forca_tendencia * 0.1)))  # 1.0 a 1.5
                            tp_multiplier = max(1.2, min(2.0, 1.2 + (forca_tendencia * 0.2)))  # 1.2 a 2.0
                            
                            sl_distance = atr[-1] * sl_multiplier
                            tp_distance = atr[-1] * self.min_rr_ratio * tp_multiplier
                            
                            self.log_system.logar(self.ativo, f"📊 Parâmetros de Entrada:")
                            self.log_system.logar(self.ativo, f"  • Força da Tendência: {'⭐' * forca_tendencia} ({forca_tendencia}/5)")
                            self.log_system.logar(self.ativo, f"  • Stop Loss: {sl_distance:.2f} pontos")
                            self.log_system.logar(self.ativo, f"  • Take Profit: {tp_distance:.2f} pontos")
                            
                            self.abrir_ordem(mt5.ORDER_TYPE_BUY, sl_distance, tp_distance)

                        elif sinal_venda:
                            self.log_system.logar(self.ativo, "✅ SINAL DE VENDA CONFIRMADO")
                            # Ajusta SL e TP baseado na força da tendência
                            sl_multiplier = max(1.0, min(1.5, 1 + (forca_tendencia * 0.1)))  # 1.0 a 1.5
                            tp_multiplier = max(1.2, min(2.0, 1.2 + (forca_tendencia * 0.2)))  # 1.2 a 2.0
                            
                            sl_distance = atr[-1] * sl_multiplier
                            tp_distance = atr[-1] * self.min_rr_ratio * tp_multiplier
                            
                            self.log_system.logar(self.ativo, f"📊 Parâmetros de Entrada:")
                            self.log_system.logar(self.ativo, f"  • Força da Tendência: {'⭐' * forca_tendencia} ({forca_tendencia}/5)")
                            self.log_system.logar(self.ativo, f"  • Stop Loss: {sl_distance:.2f} pontos")
                            self.log_system.logar(self.ativo, f"  • Take Profit: {tp_distance:.2f} pontos")
                            
                            self.abrir_ordem(mt5.ORDER_TYPE_SELL, sl_distance, tp_distance)

                    except Exception as e:
                        self.log_system.logar(self.ativo, f"❌ Erro no cálculo de sinais: {str(e)}")
                        return

                except Exception as e:
                    self.log_system.logar(self.ativo, f"❌ Erro no cálculo de indicadores: {str(e)}")
                    return

            except Exception as e:
                self.log_system.logar(self.ativo, f"❌ Erro nos cálculos básicos: {str(e)}")
                return

        except Exception as e:
            self.log_system.logar(self.ativo, f"❌ Erro na análise: {str(e)}")
            return

    def verificar_horario_favoravel(self):
        """Verifica se o horário atual é favorável para operar"""
        hora_atual = pd.Timestamp.now().time()
        # Horário estendido para mais oportunidades
        if (hora_atual >= pd.Timestamp('09:00').time() and
                hora_atual <= pd.Timestamp('17:30').time()):
            return True
        return False

    def verificar_risco_posicao(self):
        """Verifica se a posição atende aos critérios de risco"""
        posicoes = mt5.positions_total()
        if posicoes >= self.max_positions:
            if self.operando:
                self.log_system.logar(self.ativo, "⚠️ Máximo de posições atingido")
            return False

        saldo_inicial = mt5.account_info().balance
        saldo_atual = mt5.account_info().equity
        drawdown = (saldo_inicial - saldo_atual) / saldo_inicial * 100

        if drawdown > self.max_daily_loss:
            if self.operando:
                self.log_system.logar(self.ativo, f"⚠️ Máximo drawdown diário atingido: {drawdown:.2f}%")
            return False

        return True

    def abrir_ordem(self, tipo_ordem, sl_distance, tp_distance):
        tick = mt5.symbol_info_tick(self.ativo)
        if tick is None:
            if self.operando:
                self.log_system.logar(self.ativo, "❌ Erro ao obter cotação atual")
            return

        preco = tick.ask if tipo_ordem == mt5.ORDER_TYPE_BUY else tick.bid
        point = mt5.symbol_info(self.ativo).point

        sl = preco - sl_distance * point if tipo_ordem == mt5.ORDER_TYPE_BUY else preco + sl_distance * point
        tp = preco + tp_distance * point if tipo_ordem == mt5.ORDER_TYPE_BUY else preco - tp_distance * point

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.ativo,
            "volume": self.lote,
            "type": tipo_ordem,
            "price": preco,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": "Future MT5 Robo v2",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        resultado = mt5.order_send(request)

        if resultado.retcode != mt5.TRADE_RETCODE_DONE:
            if self.operando:
                self.log_system.logar(self.ativo, f"❌ Erro ao enviar ordem: {resultado.comment}")
        else:
            self.ticket_atual = resultado.order
            direcao = "COMPRA" if tipo_ordem == mt5.ORDER_TYPE_BUY else "VENDA"
            if self.operando:
                self.log_system.logar(self.ativo, f"✅ ORDEM DE {direcao} CONFIRMADA E EXECUTADA!")
                self.log_system.logar(self.ativo, f"📊 Detalhes da Ordem:")
                self.log_system.logar(self.ativo, f"  • Ticket: {self.ticket_atual}")
                self.log_system.logar(self.ativo, f"  • Preço: {preco:.5f}")
                self.log_system.logar(self.ativo, f"  • Stop Loss: {sl:.5f}")
                self.log_system.logar(self.ativo, f"  • Take Profit: {tp:.5f}")

    # Technical indicator methods remain the same as they are calculation utilities
    def ema(self, data, period):
        return pd.Series(data).ewm(span=period, adjust=False).mean().values

    def macd(self, data, short_period=12, long_period=26, signal_period=9):
        ema_short = self.ema(data, short_period)
        ema_long = self.ema(data, long_period)
        macd_line = ema_short - ema_long
        signal_line = self.ema(macd_line, signal_period)
        return macd_line, signal_line

    def rsi(self, data, period=14):
        delta = np.diff(data)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.convolve(gain, np.ones(period) / period, mode='valid')
        avg_loss = np.convolve(loss, np.ones(period) / period, mode='valid')

        rs = avg_gain / np.where(avg_loss == 0, 0.000001, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return np.concatenate([np.full(period - 1, 50), rsi])

    def bollinger_bands(self, data, period=20, num_std=2):
        sma = pd.Series(data).rolling(window=period).mean()
        std = pd.Series(data).rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return upper.values, sma.values, lower.values

    def stochastic(self, high, low, close, period=14, k_smooth=3, d_smooth=3):
        low_min = pd.Series(low).rolling(window=period).min()
        high_max = pd.Series(high).rolling(window=period).max()
        k = 100 * ((pd.Series(close) - low_min) / (high_max - low_min))
        k = k.rolling(window=k_smooth).mean()
        d = k.rolling(window=d_smooth).mean()
        return k.values, d.values

    def atr(self, high, low, close, period=14):
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.values

    def momentum(self, data, period=10):
        momentum = np.zeros_like(data)
        momentum[period:] = data[period:] - data[:-period]
        momentum[:period] = momentum[period]
        return momentum
