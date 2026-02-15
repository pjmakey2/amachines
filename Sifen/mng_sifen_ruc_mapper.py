import os
import logging
import requests
import zipfile
import pandas as pd
from io import BytesIO
from django.conf import settings
from Sifen.models import Clientes
from celery import current_app
from boltons.iterutils import chunked

logger = logging.getLogger(__name__)


class RMap:
    """
    RUC Mapper - Downloads and syncs RUC data from DNIT Paraguay
    """

    RUC_URLS = [
        'https://www.dnit.gov.py/documents/20123/2241042/ruc0.zip/1e935f39-094f-8810-8b40-b5352d5005e2?t=1762428520265',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc1.zip/52bf8d21-f91a-07c3-4f65-20789f0cd336?t=1762428521193',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc2.zip/d46e4c40-4917-af1f-499d-8f4568255bb1?t=1762428522089',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc3.zip/32da974f-b020-9ea0-8f02-d86589b8647e?t=1762428523017',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc4.zip/72aee4cd-3044-a0a8-1e3e-cef0b1bb959c?t=1762428523945',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc5.zip/089e1883-637e-798d-ba72-df6ce2909186?t=1762428524830',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc6.zip/2a4651ef-fad1-20a9-95d7-c463e0a0796f?t=1762428525778',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc7.zip/285f049e-6336-4bbb-b01e-08ca9c24c5f5?t=1762428526796',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc8.zip/45172c11-56b1-4efd-7234-8ec393a320ba?t=1762428527725',
        'https://www.dnit.gov.py/documents/20123/2241042/ruc9.zip/7119717e-1824-2d55-88c0-d516fc6cafe7?t=1762428528667',
    ]

    COLUMN_NAMES = ['RUC', 'NOMBREFACTURA', 'DV', 'RUC_VIEJO', 'ESTADO', 'EMPTY']

    def __init__(self):
        self.download_dir = os.path.join(settings.BASE_DIR, 'Sifen', 'rf', 'ruc_data')
        os.makedirs(self.download_dir, exist_ok=True)

    def download_and_extract_zip(self, url, file_index):
        """
        Download a zip file and extract its contents
        """
        logger.info(f'Downloading ruc{file_index}.zip from {url}')

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(self.download_dir)
                txt_files = [f for f in zip_file.namelist() if f.endswith('.txt')]
                logger.info(f'Extracted files: {txt_files}')
                return txt_files

        except Exception as e:
            logger.error(f'Error downloading/extracting ruc{file_index}.zip: {str(e)}')
            return []

    def read_txt_to_dataframe(self, txt_file_path):
        """
        Read a pipe-delimited txt file into a DataFrame
        """
        logger.info(f'Reading {txt_file_path}')

        try:
            df = pd.read_csv(
                txt_file_path,
                sep='|',
                quotechar='"',
                names=self.COLUMN_NAMES,
                encoding='utf-8',
                dtype={
                    'RUC': str,
                    'NOMBREFACTURA': str,
                    'DV': str,
                    'RUC_VIEJO': str,
                    'ESTADO': str
                },
                keep_default_na=False,
                on_bad_lines='skip'
            )

            # Remove empty rows
            df = df[df['RUC'].str.strip() != '']

            logger.info(f'Loaded {len(df)} records from {txt_file_path}')
            return df

        except Exception as e:
            logger.error(f'Error reading {txt_file_path}: {str(e)}')
            return pd.DataFrame()

    def sync_to_database(self, df):
        """
        Sync DataFrame records to Clientes model using bulk operations
        """
        logger.info(f'Syncing {len(df)} records to database')

        created_count = 0
        updated_count = 0
        error_count = 0

        # Convert DataFrame to list of dicts
        records = df.to_dict('records')

        # Process in chunks of 1500
        for chunk in chunked(records, 1500):
            logger.info(f'Processing chunk of {len(chunk)} records')

            try:
                # Prepare data
                rucs_in_chunk = []
                records_to_create = []
                records_to_update = []

                for row in chunk:
                    try:
                        ruc = str(row['RUC']).strip()
                        if not ruc:
                            continue

                        # Try to convert DV to integer
                        try:
                            dv = int(row['DV'])
                        except (ValueError, TypeError):
                            dv = 0

                        rucs_in_chunk.append(ruc)

                        # Store processed data
                        row['processed_ruc'] = ruc
                        row['processed_dv'] = dv
                        row['processed_nombre'] = row['NOMBREFACTURA'].strip()
                        row['processed_estado'] = row['ESTADO'].strip()

                    except Exception as e:
                        logger.error(f'Error preparing record: {str(e)}')
                        error_count += 1

                # Get existing records in one query
                existing_rucs = set(
                    Clientes.objects.filter(pdv_ruc__in=rucs_in_chunk)
                    .values_list('pdv_ruc', flat=True)
                )

                # Get existing records for update
                existing_records = {
                    obj.pdv_ruc: obj
                    for obj in Clientes.objects.filter(pdv_ruc__in=existing_rucs)
                }

                # Separate into create and update
                for row in chunk:
                    if 'processed_ruc' not in row:
                        continue

                    ruc = row['processed_ruc']

                    if ruc in existing_records:
                        # Update existing
                        obj = existing_records[ruc]
                        obj.pdv_ruc_dv = row['processed_dv']
                        obj.pdv_nombrefantasia = row['processed_nombre']
                        obj.pdv_nombrefactura = row['processed_nombre']
                        obj.pdv_ruc_estado = row['processed_estado']
                        records_to_update.append(obj)
                    else:
                        # Create new
                        records_to_create.append(
                            Clientes(
                                pdv_ruc=ruc,
                                pdv_ruc_dv=row['processed_dv'],
                                pdv_nombrefantasia=row['processed_nombre'],
                                pdv_nombrefactura=row['processed_nombre'],
                                pdv_ruc_estado=row['processed_estado']
                            )
                        )

                # Bulk create
                if records_to_create:
                    Clientes.objects.bulk_create(records_to_create, ignore_conflicts=True)
                    created_count += len(records_to_create)
                    logger.info(f'Bulk created {len(records_to_create)} records')

                # Bulk update
                if records_to_update:
                    Clientes.objects.bulk_update(
                        records_to_update,
                        ['pdv_ruc_dv', 'pdv_nombrefantasia', 'pdv_nombrefactura', 'pdv_ruc_estado']
                    )
                    updated_count += len(records_to_update)
                    logger.info(f'Bulk updated {len(records_to_update)} records')

            except Exception as e:
                logger.error(f'Error processing chunk: {str(e)}')
                error_count += len(chunk)

        logger.info(f'Sync complete: {created_count} created, {updated_count} updated, {error_count} errors')
        return created_count, updated_count, error_count

    def sync_rucs(self, *args, **kwargs):
        """
        Main method to download, extract, and sync RUC data using Celery tasks
        """
        logger.info('Starting RUC sync process')

        tasks_sent = []
        total_records = 0

        # Download and extract all files
        for idx, url in enumerate(self.RUC_URLS):
            txt_files = self.download_and_extract_zip(url, idx)

            # Read each extracted txt file
            for txt_file in txt_files:
                txt_path = os.path.join(self.download_dir, txt_file)
                df = self.read_txt_to_dataframe(txt_path)

                if not df.empty:
                    # Remove duplicates in this dataframe (keep last occurrence)
                    df = df.drop_duplicates(subset=['RUC'], keep='last')
                    logger.info(f'Sending {len(df)} records from {txt_file} to Celery task')

                    # Convert DataFrame to dict for serialization
                    df_dict = df.to_dict('records')

                    # Send task to Celery
                    task = current_app.send_task(
                        'Sifen.tasks.sync_database',
                        args=[df_dict]
                    )
                    tasks_sent.append(task.id)
                    total_records += len(df)
                    logger.info(f'Task {task.id} sent for {txt_file}')

        logger.info(f'RUC sync process completed: {len(tasks_sent)} tasks sent, {total_records} total records')
        return {
            'tasks_sent': len(tasks_sent),
            'task_ids': tasks_sent,
            'total_records': total_records
        }
