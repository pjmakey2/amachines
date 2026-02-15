#!/bin/bash
python $PROJECT_PATH/manage.py io_rfmainl --rf_foto_paquete_desconocidos
python $PROJECT_PATH/manage.py io_rfmainl --rf_foto_paquete_deposito
python $PROJECT_PATH/manage.py io_rfmainl --rf_foto_paquete_entregado
python $PROJECT_PATH/manage.py io_rfmainl --rf_foto_paquete_anulado
python $PROJECT_PATH/manage.py io_rfmainl --rf_awb_paquete