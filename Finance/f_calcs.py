import math, logging

def js_round(n):
    return int(n + 0.5) if n - int(n) == 0.5 else round(n)

def round_to_nearest_50(amount):
    return js_round(amount / 100) * 100

# def round_to_nearest_50(amount):
#     if isinstance(amount, float):
#         # Separate the integer and decimal parts
#         integer_part = int(amount)
#         decimal_part = amount - integer_part
#         if decimal_part > 0:
#             return amount
#     return round(amount / 100) * 100

def calculate_price(pobj, precio_unitario, cantidad, cin=False):
    d_total = round(float(precio_unitario) * float(cantidad))
    d_total_sin_iva = 0
    p_exenta = float(pobj.exenta)
    p_g5 = float(pobj.g5)
    p_g10 = float(pobj.g10)
    prop_iva = 0
    tasa_iva = 0
    exenta = 0
    base_gravada = 0
    base_gravada_5 = 0
    base_gravada_10 = 0
    gravada_5 = 0
    gravada_10 = 0
    iva_5 = 0
    iva_10 = 0
    iva = 0
    
    if p_g5 > 0:
        #prop_iva = round(float(p_g5) / 100, 3)
        prop_iva = float(p_g5)
        #tasa_iva = round((float(pobj.porcentaje_iva.porcentaje) / 100) * p_g5 + 1, 3)
        tasa_iva = pobj.porcentaje_iva.porcentaje
        logging.info(f"Calculo base_gravada e iva: p_g5={p_g5}, prop_iva={prop_iva}, tasa_iva={tasa_iva}")
    if p_g10 > 0:
        #prop_iva = round(float(p_g10) / 100, 3)
        prop_iva = float(p_g10)
        #tasa_iva = round((float(pobj.porcentaje_iva.porcentaje) / 100) * p_g10 + 1, 3)
        tasa_iva = pobj.porcentaje_iva.porcentaje
        logging.info(f"Calculo base_gravada e iva: p_g10={p_g10}, prop_iva={prop_iva}, tasa_iva={tasa_iva}")
    
    if tasa_iva > 0:
        # d_total_sin_iva = round(d_total / tasa_iva)
        # base_gravada = round(d_total - d_total_sin_iva)
        # iva = round(d_total_sin_iva * prop_iva)
        # if (p_g10 > 0):
        #     base_gravada = round((d_total * prop_iva)/1.1)
        #     iva = round((d_total * prop_iva)/11)
        # base_gravada = (100 * d_total * prop_iva) / (10000+tasa_iva*prop_iva)
        # base_gravada = (100 * d_total * prop_iva) / (10000+tasa_iva*prop_iva)
        # iva =  (base_gravada * tasa_iva)/100
        if cin:
            d_total += iva
        base_gravada = (100 * d_total * prop_iva) / (10000+tasa_iva*prop_iva)
        iva =  (base_gravada * tasa_iva)/100
        logging.info(f'Calculando base_gravada e iva: d_total={d_total}, prop_iva={prop_iva}, tasa_iva={tasa_iva}, base_gravada={base_gravada}, iva={iva}')
        if p_g5 > 0:
            base_gravada_5 = base_gravada
            iva_5 = iva
            gravada_5 = base_gravada + iva
        
        if p_g10 > 0:
            base_gravada_10 = base_gravada
            iva_10 = iva
            gravada_10 = base_gravada + iva
        logging.info(f'Calculando base_gravada e iva por tasa: base_gravada_5={base_gravada_5}, iva_5={iva_5}, gravada_5={gravada_5}, base_gravada_10={base_gravada_10}, iva_10={iva_10}, gravada_10={gravada_10}')
    
    if p_exenta:
        #exenta = d_total - (base_gravada + iva)
        exenta = (100 * d_total * (100 - prop_iva)) / (10000 + tasa_iva * prop_iva)
        logging.info(f'Calculando exenta: d_total={d_total}, prop_iva={prop_iva}, tasa_iva={tasa_iva}, exenta={exenta}')
    
    precio_unitario_siniva = d_total_sin_iva / cantidad    
    
    logging.info(f"""
    Calculando precio
        % EXENTA = {p_exenta}
        % G5 = {p_g5}
        % G10 = {p_g10}
        TASA IVA = {tasa_iva}
        PU = {precio_unitario}
        EXE = {exenta}
        G5 = {gravada_5}
        BASE_G5 = {base_gravada_5}
        I5 = {iva_5}
        G10 = {gravada_10}
        BASE_G10 = {base_gravada_10}
        I10 = {iva_10}
        PUS = {precio_unitario_siniva}
        EXE + G5 + G10 = {exenta + gravada_5 + gravada_10}
        IVA5 + IVA10 = {iva_5 + iva_10}
        BASE_GRAVADA = {base_gravada_5 + base_gravada_10}
    """)
    return {
        'exenta': exenta,
        'iva_5': iva_5,
        'gravada_5': gravada_5,
        'base_gravada_5': base_gravada_5,
        'iva_10': iva_10,
        'gravada_10': gravada_10,
        'base_gravada_10': base_gravada_10,
        'precio_unitario_siniva': precio_unitario_siniva,
        'precio_unitario': precio_unitario,
        'afecto': gravada_10+gravada_5,
        'total_iva': iva_10+iva_5,
        'total_operacion': (gravada_10+gravada_5)+exenta
    }    

def calculate_price_c(pobj, precio_unitario, cantidad, iin=False):
    d_total = float(precio_unitario * cantidad)
    p_exenta = float(pobj.exenta)
    p_g5 = float(pobj.g5)
    p_g10 = float(pobj.g10)
    exenta = 0
    iva_5 = 0
    gravada_5 = 0
    base_gravada_5 = 0
    iva_10 = 0
    gravada_10 = 0
    base_gravada_10 = 0
    precio_unitario_siniva = 0
    
    if p_exenta:
        exenta = d_total * (p_exenta / 100)
    
    if iin:
        if p_g5:
            base_gravada_5 = ((p_g5 / 100) * d_total) / (1 + ((pobj.porcentaje_iva / 100) * (p_g5 / 100)))
            iva_5 = base_gravada_5 * 0.05
            gravada_5 = base_gravada_5 + iva_5
        if p_g10:
            base_gravada_10 = ((p_g10 / 100) * d_total) / (1 + ((pobj.porcentaje_iva / 100) * (p_g10 / 100)))
            iva_10 = base_gravada_10 * 0.10
            gravada_10 = base_gravada_10 + iva_10
    else:
        if p_g5:
            base_gravada_5 = d_total * (p_g5 / 100)
            iva_5 = base_gravada_5 * 0.05
            gravada_5 = base_gravada_5 + iva_5
        if p_g10:
            base_gravada_10 = d_total * (p_g10 / 100)
            iva_10 = base_gravada_10 * 0.10
            gravada_10 = base_gravada_10 + iva_10
    
    exenta = int(exenta)
    gravada_5 = int(gravada_5)
    gravada_10 = int(gravada_10)
    precio_unitario = (exenta + gravada_5 + gravada_10)/cantidad
    precio_unitario_siniva = precio_unitario - (iva_10 + iva_5)
    
    logging.info(f"""
    Calculando precio
        PU = {precio_unitario}
        EXE = {exenta}
        G5 = {gravada_5}
        BASE_G5 = {base_gravada_5}
        I5 = {iva_5}
        G10 = {gravada_10}
        BASE_G10 = {base_gravada_10}
        I10 = {iva_10}
        PUS = {precio_unitario_siniva}
        EXE + G5 + G10 = {exenta + gravada_5 + gravada_10}
        IVA5 + IVA10 = {iva_5 + iva_10}
        BASE_GRAVADA = {base_gravada_5 + base_gravada_10}
    """)
    
    return {
        'exenta': exenta,
        'iva_5': iva_5,
        'gravada_5': gravada_5,
        'base_gravada_5': base_gravada_5,
        'iva_10': iva_10,
        'gravada_10': gravada_10,
        'base_gravada_10': base_gravada_10,
        'precio_unitario_siniva': precio_unitario_siniva,
        'precio_unitario': precio_unitario,
        'afecto': gravada_10+gravada_5
    }

    
def calculate_price_old(pobj, precio_unitario, cantidad):
    d_total = precio_unitario*cantidad
    p_exenta = float(pobj.exenta)
    p_g5 = float(pobj.g5)
    p_g10 = float(pobj.g10)
    exenta = 0
    iva_5 = 0
    gravada_5 = 0
    iva_10 = 0
    gravada_10 = 0
    precio_unitario_siniva = 0

    if p_exenta:
        exenta = (d_total * p_exenta) / 100
    if p_g5:
        gravada_5 = (d_total * p_g5) / 100
        iva_5 = gravada_5-(gravada_5/1.05)
    if p_g10:
        gravada_10 = (d_total * p_g10) / 100
        iva_10 = gravada_10-(gravada_10/1.1)

    precio_unitario_siniva = precio_unitario - (iva_10 + iva_5)
    logging.info(f"""
            Calculando precio
                PU = {precio_unitario}
                EXE = {exenta}
                G5 = {gravada_5}
                I5 = {iva_5}
                G10 = {gravada_10}
                I10 = {iva_10}
                PUS = {precio_unitario_siniva}
                EXE + G5 + G10 = {exenta+gravada_5+gravada_10}
                IVA5+IVA10 = {iva_5+iva_10}
    """)
    return {
        'exenta': exenta,
        'iva_5': iva_5,
        'gravada_5': gravada_5,
        'iva_10': iva_10,
        'gravada_10': gravada_10,
        'precio_unitario_siniva': precio_unitario_siniva,
        'afecto': gravada_10 + gravada_5
    }



def round_two_decimal(value):
    str_value = f"{value:.2f}"
    decimal_part = str_value.split(".")[1] 
    if int(decimal_part[1]) > 0:
        return float(f"{str_value.split('.')[0]}.{int(decimal_part[0])+1}")
    return value