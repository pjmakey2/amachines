#!/bin/bash
#TOCA3D - TESTING
python manage.py \
    mng_sifen_mainline \
    --create_timbrado \
    --ruc 80163121 \
    --dv 1 \
    --timbrado 80163121 \
    --establecimiento 1\
    --inicio "2025-11-12" \
    --fcsc "ABCD0000000000000000000000000000"  \
    --scsc "EFGH0000000000000000000000000000" \
    --expd 1 1 1 1\
    --serie "ZZZ" "ZZZ" "ZZZ" "ZZZ"\
    --tipo "FE" "NC" "ND" "AF" \
    --nstart 1 1 1 1\
    --nend 100 100 100 100

#Crear numeros para tipos especificicos
python manage.py \
    mng_sifen_mainline \
    --generate_numbers_timbrado \
    --timbrado 80163121 \
    --establecimiento 1 \
    --expd 1\
    --serie "ZZZ" \
    --tipo "RC" \
    --nstart 1\
    --nend 100