ivn = {

    calculate_price: (pobj, precio_unitario, cantidad) => {
        if (we.isDecimal(precio_unitario)) {
            d_total = parseFloat(precio_unitario) * parseFloat(cantidad);
        } else {
            d_total = Math.round(parseFloat(precio_unitario) * parseFloat(cantidad));
        }
        
        d_total_sin_iva = 0
        p_exenta = parseFloat(pobj.exenta);
        p_g5 = parseFloat(pobj.g5);
        p_g10 = parseFloat(pobj.g10);
        prop_iva = 0;
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
        console.log(p_g5, p_g10);
        if (p_g5 > 0) {
            //prop_iva = (parseFloat(p_g5)/100).toFixed(3)
            prop_iva = parseFloat(p_g5)
            //tasa_iva = ((parseFloat(pobj.porcentaje_iva__porcentaje)/100).toFixed(3) * p_g5 + 1).toFixed(3)
            tasa_iva = parseFloat(pobj.porcentaje_iva__porcentaje)
        }
        if (p_g10 > 0) {
            //prop_iva = (parseFloat(p_g10)/100).toFixed(3)
            prop_iva = parseFloat(p_g10)
            //tasa_iva = ((parseFloat(pobj.porcentaje_iva__porcentaje)/100).toFixed(3) * p_g10 + 1).toFixed(3)
            tasa_iva = parseFloat(pobj.porcentaje_iva__porcentaje)
        }
        //console.log(prop_iva, tasa_iva)
        if (tasa_iva > 0) {
            // d_total_sin_iva = Math.round(d_total/tasa_iva);
            // base_gravada = Math.round(d_total - d_total_sin_iva);
            // iva = Math.round(d_total_sin_iva*prop_iva);
            // console.log(iva, d_total_sin_iva, base_gravada);
            // if (p_g10 > 0) {
            //     base_gravada = Math.round((d_total * prop_iva)/1.1)
            //     iva = Math.round((d_total * prop_iva)/11)
            // }
            base_gravada = (100 * d_total * prop_iva) / (10000+tasa_iva*prop_iva)
            iva =  (base_gravada * tasa_iva)/100
            if (p_g5 > 0){
                base_gravada_5 = base_gravada
                iva_5 = iva
                gravada_5 = base_gravada+iva
            }
            if (p_g10 > 0){
                base_gravada_10 = base_gravada
                iva_10 = iva
                gravada_10 = base_gravada+iva
            }
        }
        
        if (p_exenta){
            //[100 * EA008 * (100 – E733)] / [10000 + (E734 *E733)]
            //exenta = 100 * d_total * (100 - (p_g5+p_g10)) / 10000 + (pobj.porcentaje_iva__porcentaje * (p_g5+p_g10))
            //exenta = d_total - (base_gravada+iva)
            //(100 * gCamItem['gValorItem']['gValorRestaItem']['dTotOpeItem'] * (100 - item['ivaBase'])) /(10000 + item['iva'] * item['ivaBase']);
            exenta = (100 * d_total * (100 - prop_iva)) / (10000 + tasa_iva * prop_iva)
        }
        precio_unitario_siniva = d_total_sin_iva/cantidad
        console.log(`
            Calculando precio
                PU = ${precio_unitario}
                EXE = ${exenta}
                G5 = ${gravada_5}
                BASE_G5 = ${base_gravada_5}
                I5 = ${iva_5}
                G10 = ${gravada_10}
                BASE_G10 = ${base_gravada_10}
                I10 = ${iva_10}
                PUS = ${precio_unitario_siniva}
                EXE + G5 + G10 = ${exenta + gravada_5 + gravada_10}
                IVA5 + IVA10 = ${iva_5 + iva_10}
                BASE_GRAVADA = ${base_gravada_5 + base_gravada_10}
        `)
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
    }
}

we = {
    isDecimal: (num) => {
        return !Number.isInteger(num);
    },
    round_two_decimal: (value) => {
        const strValue = value.toFixed(2);
        const decimalPart = strValue.split(".")[1];
        if (parseInt(decimalPart[1]) > 0) {
            return parseFloat(strValue.split(".")[0] + '.' + (parseInt(decimalPart[0]) + 1));
        }
        return value;
    },
}