import json
import os
import MetaTrader5 as mt5

CAMINHO_LOGIN_SALVO = "login_salvo.json"

def salvar_login(server, login, password):
    dados = {
        "server": server,
        "login": login,
        "password": password
    }
    with open(CAMINHO_LOGIN_SALVO, "w") as f:
        json.dump(dados, f)

def carregar_login():
    if os.path.exists(CAMINHO_LOGIN_SALVO):
        with open(CAMINHO_LOGIN_SALVO, "r") as f:
            return json.load(f)
    return None

def conectar_mt5(server, login, password):
    if not mt5.initialize(server=server, login=int(login), password=password):
        return False
    return True

def verificar_conta_real():
    info = mt5.account_info()
    if info is None:
        return False
    return info.trade_mode == 0  # 0 = Conta Real

def obter_saldo():
    conta = mt5.account_info()
    if conta:
        return conta.balance
    return 0.0

# Novas funções de utilidade para análise de mercado
def calcular_resultado_financeiro(preco_entrada, preco_saida, volume, tipo_ordem):
    """Calcula resultado financeiro da operação"""
    if tipo_ordem == mt5.ORDER_TYPE_BUY:
        return (preco_saida - preco_entrada) * volume
    else:
        return (preco_entrada - preco_saida) * volume

def verificar_horario_mercado(ativo):
    """Verifica se o mercado está aberto para o ativo"""
    info = mt5.symbol_info(ativo)
    if info is None:
        return False, "Ativo não encontrado"
    
    if not info.visible:
        return False, "Ativo não está visível"
        
    tick = mt5.symbol_info_tick(ativo)
    if tick is None:
        return False, "Não foi possível obter cotação"
        
    if tick.bid == 0 or tick.ask == 0:
        return False, "Mercado fechado"
        
    spread = (tick.ask - tick.bid) / info.point
    if spread > 50:  # Spread máximo aceitável
        return False, f"Spread muito alto ({spread:.1f} pontos)"
        
    return True, "Mercado aberto"

def calcular_posicao_ideal(ativo, risco_percentual=1.0):
    """Calcula o tamanho ideal da posição baseado no risco"""
    try:
        conta = mt5.account_info()
        if conta is None:
            return 0.0
            
        info = mt5.symbol_info(ativo)
        if info is None:
            return 0.0
            
        # Calcula o valor em risco
        valor_conta = conta.equity
        valor_risco = valor_conta * (risco_percentual / 100)
        
        # Calcula o volume baseado no valor em risco
        tick_value = info.trade_tick_value
        if tick_value == 0:
            return 0.0
            
        volume = round(valor_risco / tick_value, 2)
        
        # Ajusta para os limites do ativo
        volume = max(info.volume_min, min(volume, info.volume_max))
        
        return volume
        
    except Exception as e:
        print(f"Erro ao calcular posição: {str(e)}")
        return 0.0

def verificar_drawdown(max_drawdown_percentual=5.0):
    """Verifica se atingiu o drawdown máximo permitido"""
    try:
        conta = mt5.account_info()
        if conta is None:
            return True, 0.0
            
        drawdown = ((conta.balance - conta.equity) / conta.balance) * 100
        
        return drawdown > max_drawdown_percentual, drawdown
        
    except Exception as e:
        print(f"Erro ao verificar drawdown: {str(e)}")
        return True, 0.0

def formatar_preco(preco, digitos=5):
    """Formata o preço com o número correto de casas decimais"""
    return f"{preco:.{digitos}f}"
