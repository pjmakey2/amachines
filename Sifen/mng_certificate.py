"""
Manager para gestión de certificados digitales SIFEN.

Maneja:
- Encriptación/desencriptación de contraseñas
- Procesamiento de archivos PKCS#12 (.p12 o .pfx)
- Extracción de archivos PEM y KEY usando openssl
- Extracción de información del certificado (titular, emisor, fechas)

Nota: Los formatos .p12 y .pfx son equivalentes (ambos son PKCS#12).
"""
import os
import subprocess
import tempfile
import logging
import hashlib
import base64
import json
from datetime import datetime, timezone as dt_timezone
from typing import Tuple, Optional, Dict, Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509

from Sifen.models import Certificate, Business
from OptsIO.io_json import from_json

logger = logging.getLogger(__name__)


class CertificateManager:
    """Manager para operaciones con certificados digitales."""

    def __init__(self):
        # Usar SECRET_KEY de Django como base para la clave de encriptación
        # En producción, debería usarse una clave específica
        self.cipher_key = self._derive_key()

    def _derive_key(self) -> bytes:
        """Deriva una clave Fernet de 32 bytes desde SECRET_KEY."""
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        return base64.urlsafe_b64encode(key)

    def encrypt_password(self, password: str) -> str:
        """Encripta una contraseña para almacenamiento seguro."""
        fernet = Fernet(self.cipher_key)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        """Desencripta una contraseña almacenada."""
        fernet = Fernet(self.cipher_key)
        decrypted = fernet.decrypt(encrypted_password.encode())
        return decrypted.decode()

    def process_certificate(self, certificate) -> Tuple[bool, str]:
        """
        Procesa un certificado PFX: genera PEM y KEY, extrae información.

        Args:
            certificate: Instancia del modelo Certificate

        Returns:
            Tuple de (success, message)
        """
        try:
            # Desencriptar password
            password = self.decrypt_password(certificate.pfx_password_encrypted)

            # Obtener path del PFX
            pfx_path = certificate.pfx_file.path

            # Generar PEM y KEY usando openssl
            pem_content, key_content, error = self._extract_pem_key(pfx_path, password)

            if error:
                certificate.estado = 'error'
                certificate.error_mensaje = error
                certificate.save()
                return False, error

            # Guardar archivos generados
            base_name = os.path.splitext(os.path.basename(pfx_path))[0]

            # Guardar PEM
            pem_filename = f"{certificate.businessobj.ruc}_{base_name}.pem"
            certificate.pem_file.save(pem_filename, ContentFile(pem_content))

            # Guardar KEY
            key_filename = f"{certificate.businessobj.ruc}_{base_name}.key"
            certificate.key_file.save(key_filename, ContentFile(key_content))

            # Extraer información del certificado
            cert_info = self._extract_certificate_info(pem_content)

            if cert_info:
                certificate.titular = cert_info.get('titular')
                certificate.emisor = cert_info.get('emisor')
                certificate.numero_serie = cert_info.get('numero_serie')
                certificate.fecha_emision = cert_info.get('fecha_emision')
                certificate.fecha_vencimiento = cert_info.get('fecha_vencimiento')

                # Verificar si está vencido
                if cert_info.get('fecha_vencimiento'):
                    now_utc = datetime.now(dt_timezone.utc)
                    fecha_venc = cert_info['fecha_vencimiento']
                    # Asegurar que fecha_venc tenga timezone
                    if fecha_venc.tzinfo is None:
                        fecha_venc = fecha_venc.replace(tzinfo=dt_timezone.utc)
                    if fecha_venc < now_utc:
                        certificate.estado = 'vencido'
                    else:
                        certificate.estado = 'activo'
                else:
                    certificate.estado = 'activo'
            else:
                certificate.estado = 'activo'

            certificate.error_mensaje = None
            certificate.save()

            return True, "Certificado procesado exitosamente"

        except Exception as e:
            logger.exception("Error procesando certificado")
            certificate.estado = 'error'
            certificate.error_mensaje = str(e)
            certificate.save()
            return False, str(e)

    def _extract_pem_key(self, pfx_path: str, password: str) -> Tuple[bytes, bytes, Optional[str]]:
        """
        Extrae archivos PEM y KEY de un archivo PFX usando openssl.

        Args:
            pfx_path: Ruta al archivo PFX
            password: Contraseña del PFX

        Returns:
            Tuple de (pem_content, key_content, error_message)
        """
        pem_content = None
        key_content = None

        try:
            # Crear archivos temporales para salida
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as pem_tmp:
                pem_tmp_path = pem_tmp.name
            with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as key_tmp:
                key_tmp_path = key_tmp.name

            try:
                # Extraer KEY (clave privada) - usar -legacy para compatibilidad
                key_cmd = [
                    'openssl', 'pkcs12',
                    '-legacy',
                    '-in', pfx_path,
                    '-out', key_tmp_path,
                    '-nocerts',
                    '-nodes',
                    '-password', f'pass:{password}'
                ]

                result = subprocess.run(
                    key_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    # Intentar sin -legacy para versiones antiguas de openssl
                    key_cmd.remove('-legacy')
                    result = subprocess.run(
                        key_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode != 0:
                        return None, None, f"Error extrayendo KEY: {result.stderr}"

                # Extraer PEM (certificado)
                pem_cmd = [
                    'openssl', 'pkcs12',
                    '-legacy',
                    '-in', pfx_path,
                    '-out', pem_tmp_path,
                    '-nokeys',
                    '-clcerts',
                    '-password', f'pass:{password}'
                ]

                result = subprocess.run(
                    pem_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    # Intentar sin -legacy
                    pem_cmd.remove('-legacy')
                    result = subprocess.run(
                        pem_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode != 0:
                        return None, None, f"Error extrayendo PEM: {result.stderr}"

                # Leer contenidos
                with open(pem_tmp_path, 'rb') as f:
                    pem_content = f.read()
                with open(key_tmp_path, 'rb') as f:
                    key_content = f.read()

                # Limpiar contenido de KEY (quitar headers adicionales de openssl)
                key_content = self._clean_key_content(key_content)
                pem_content = self._clean_pem_content(pem_content)

                return pem_content, key_content, None

            finally:
                # Limpiar archivos temporales
                if os.path.exists(pem_tmp_path):
                    os.unlink(pem_tmp_path)
                if os.path.exists(key_tmp_path):
                    os.unlink(key_tmp_path)

        except subprocess.TimeoutExpired:
            return None, None, "Timeout procesando certificado"
        except Exception as e:
            logger.exception("Error extrayendo PEM/KEY")
            return None, None, str(e)

    def _clean_key_content(self, content: bytes) -> bytes:
        """Limpia el contenido del KEY, dejando solo la clave privada."""
        lines = content.decode('utf-8', errors='ignore').split('\n')
        clean_lines = []
        in_key = False

        for line in lines:
            if '-----BEGIN' in line and 'PRIVATE KEY' in line:
                in_key = True
            if in_key:
                clean_lines.append(line)
            if '-----END' in line and 'PRIVATE KEY' in line:
                break

        return '\n'.join(clean_lines).encode('utf-8')

    def _clean_pem_content(self, content: bytes) -> bytes:
        """Limpia el contenido del PEM, dejando solo el certificado."""
        lines = content.decode('utf-8', errors='ignore').split('\n')
        clean_lines = []
        in_cert = False

        for line in lines:
            if '-----BEGIN CERTIFICATE-----' in line:
                in_cert = True
            if in_cert:
                clean_lines.append(line)
            if '-----END CERTIFICATE-----' in line:
                break

        return '\n'.join(clean_lines).encode('utf-8')

    def _extract_certificate_info(self, pem_content: bytes) -> Optional[Dict[str, Any]]:
        """
        Extrae información del certificado desde el contenido PEM.

        Args:
            pem_content: Contenido del archivo PEM

        Returns:
            Diccionario con información del certificado
        """
        try:
            cert = x509.load_pem_x509_certificate(pem_content, default_backend())

            # Extraer CN del subject (titular)
            titular = None
            for attr in cert.subject:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    titular = attr.value
                    break

            # Extraer emisor
            emisor = None
            for attr in cert.issuer:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    emisor = attr.value
                    break
            if not emisor:
                for attr in cert.issuer:
                    if attr.oid == x509.oid.NameOID.ORGANIZATION_NAME:
                        emisor = attr.value
                        break

            # Extraer fechas - usar los atributos correctos según versión de cryptography
            try:
                # cryptography >= 42.0 usa not_valid_before_utc
                fecha_emision = cert.not_valid_before_utc
                fecha_vencimiento = cert.not_valid_after_utc
            except AttributeError:
                # cryptography < 42.0 usa not_valid_before (naive datetime)
                fecha_emision = cert.not_valid_before
                fecha_vencimiento = cert.not_valid_after

            # Asegurar que sean timezone aware (UTC)
            if fecha_emision.tzinfo is None:
                fecha_emision = fecha_emision.replace(tzinfo=dt_timezone.utc)
            if fecha_vencimiento.tzinfo is None:
                fecha_vencimiento = fecha_vencimiento.replace(tzinfo=dt_timezone.utc)

            return {
                'titular': titular,
                'emisor': emisor,
                'numero_serie': str(cert.serial_number),
                'fecha_emision': fecha_emision,
                'fecha_vencimiento': fecha_vencimiento,
            }

        except Exception as e:
            logger.exception("Error extrayendo info del certificado")
            return None

    def validate_pfx(self, pfx_path: str, password: str) -> Tuple[bool, str]:
        """
        Valida que un archivo PFX sea correcto y la contraseña sea válida.

        Args:
            pfx_path: Ruta al archivo PFX
            password: Contraseña a validar

        Returns:
            Tuple de (is_valid, message)
        """
        try:
            # Intentar leer el PFX con la contraseña
            cmd = [
                'openssl', 'pkcs12',
                '-legacy',
                '-in', pfx_path,
                '-noout',
                '-password', f'pass:{password}'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # Intentar sin -legacy
                cmd.remove('-legacy')
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    if 'mac verify failure' in result.stderr.lower():
                        return False, "Contraseña incorrecta"
                    return False, f"Archivo PFX inválido: {result.stderr}"

            return True, "Certificado válido"

        except subprocess.TimeoutExpired:
            return False, "Timeout validando certificado"
        except Exception as e:
            return False, str(e)

    def get_active_certificate_for_business(self, business):
        """
        Obtiene el certificado activo predeterminado para una empresa.

        Args:
            business: Instancia del modelo Business

        Returns:
            Instancia de Certificate o None
        """
        # Primero buscar el predeterminado
        cert = Certificate.objects.filter(
            businessobj=business,
            es_predeterminado=True,
            estado='activo'
        ).first()

        if cert:
            return cert

        # Si no hay predeterminado, buscar cualquier activo
        return Certificate.objects.filter(
            businessobj=business,
            estado='activo'
        ).first()


# Singleton para uso global
certificate_manager = CertificateManager()


class MCertificate:
    """
    Clase para operaciones CRUD de certificados desde la UI.

    Esta clase es invocada desde el frontend a traves del sistema IoM.
    """

    def _clean_kwargs(self, kwargs):
        """Limpia kwargs para que sea serializable (remueve request con FILES)."""
        clean = {k: v for k, v in kwargs.items() if k != 'request'}
        return clean

    def save_certificate(self, *args, **kwargs) -> tuple:
        """
        Guarda un nuevo certificado o actualiza uno existente.

        Parametros esperados en uc_fields:
        - id: ID del certificado (opcional, para edicion)
        - nombre: Nombre descriptivo
        - businessobj_id: ID de la empresa
        - pfx_file: Archivo PFX (en request.FILES)
        - pfx_password: Contrasena del PFX
        - es_predeterminado: Boolean
        """
        request = kwargs.get('request')
        q = kwargs.get('qdict', {})
        uc_fields = from_json(q.get('uc_fields', {}))
        userobj = kwargs.get('userobj')

        try:
            cert_id = uc_fields.get('id')
            nombre = uc_fields.get('nombre', '').strip()
            business_id = uc_fields.get('businessobj_id')
            es_predeterminado = str(uc_fields.get('es_predeterminado', 'false')).lower() == 'true'
            pfx_password = uc_fields.get('pfx_password', '')

            # Kwargs limpio para returns (sin request que tiene FILES no serializables)
            ckwargs = self._clean_kwargs(kwargs)

            # Validaciones basicas
            if not nombre:
                return {'error': 'El nombre del certificado es requerido'}, args, ckwargs

            if not business_id:
                return {'error': 'Debe seleccionar una empresa'}, args, ckwargs

            # Obtener business
            try:
                business = Business.objects.get(pk=business_id)
            except Business.DoesNotExist:
                return {'error': 'La empresa seleccionada no existe'}, args, ckwargs

            # Obtener archivo PFX si se subio
            files = kwargs.get('files', {})
            pfx_file = files.get('pfx_file')

            # Crear o actualizar certificado
            if cert_id:
                # Edicion
                try:
                    certificate = Certificate.objects.get(pk=cert_id)
                except Certificate.DoesNotExist:
                    return {'error': 'Certificado no encontrado'}, args, ckwargs

                certificate.nombre = nombre
                certificate.businessobj = business
                certificate.es_predeterminado = es_predeterminado
                certificate.actualizado_usuario = userobj.username if userobj else None

                # Si se sube nuevo archivo, reprocesar
                if pfx_file and pfx_password:
                    certificate.pfx_file = pfx_file
                    certificate.pfx_password_encrypted = certificate_manager.encrypt_password(pfx_password)
                    certificate.estado = 'pendiente'
                    certificate.pem_file = None
                    certificate.key_file = None
                    certificate.error_mensaje = None

                certificate.save()

                # Procesar si esta pendiente
                if certificate.estado == 'pendiente':
                    success, message = certificate_manager.process_certificate(certificate)
                    if not success:
                        return {'warning': f'Certificado guardado pero hubo un error al procesar: {message}'}, args, ckwargs

                return {'success': 'Certificado actualizado exitosamente'}, args, ckwargs

            else:
                # Creacion - requiere archivo y password
                if not pfx_file:
                    return {'error': 'Debe seleccionar un archivo PFX/P12'}, args, ckwargs

                if not pfx_password:
                    return {'error': 'Debe ingresar la contrasena del certificado'}, args, ckwargs

                # Crear certificado
                certificate = Certificate(
                    nombre=nombre,
                    businessobj=business,
                    pfx_file=pfx_file,
                    pfx_password_encrypted=certificate_manager.encrypt_password(pfx_password),
                    es_predeterminado=es_predeterminado,
                    estado='pendiente',
                    cargado_usuario=userobj.username if userobj else None,
                )
                certificate.save()

                # Procesar certificado
                success, message = certificate_manager.process_certificate(certificate)
                if not success:
                    return {'warning': f'Certificado guardado pero hubo un error al procesar: {message}'}, args, ckwargs

                return {'success': 'Certificado cargado y procesado exitosamente'}, args, ckwargs

        except Exception as e:
            logger.exception("Error guardando certificado")
            ckwargs = self._clean_kwargs(kwargs)
            return {'error': f'Error al guardar certificado: {str(e)}'}, args, ckwargs

    def delete_certificates(self, *args, **kwargs) -> tuple:
        """
        Elimina uno o mas certificados.

        Parametros esperados en qdict:
        - ids: Lista JSON de IDs a eliminar
        """
        q = kwargs.get('qdict', {})
        ids_str = q.get('ids', '[]')

        try:
            ids = json.loads(ids_str)
        except json.JSONDecodeError:
            return {'error': 'IDs invalidos'}, args, kwargs

        if not ids:
            return {'error': 'No se especificaron certificados para eliminar'}, args, kwargs

        try:
            deleted_count = 0
            for cert_id in ids:
                try:
                    cert = Certificate.objects.get(pk=cert_id)
                    # Eliminar archivos fisicos si existen
                    if cert.pfx_file:
                        try:
                            cert.pfx_file.delete(save=False)
                        except Exception:
                            pass
                    if cert.pem_file:
                        try:
                            cert.pem_file.delete(save=False)
                        except Exception:
                            pass
                    if cert.key_file:
                        try:
                            cert.key_file.delete(save=False)
                        except Exception:
                            pass
                    cert.delete()
                    deleted_count += 1
                except Certificate.DoesNotExist:
                    continue

            return {'success': f'{deleted_count} certificado(s) eliminado(s)'}, args, kwargs

        except Exception as e:
            logger.exception("Error eliminando certificados")
            return {'error': f'Error al eliminar certificados: {str(e)}'}, args, kwargs

    def reprocess_certificates(self, *args, **kwargs) -> tuple:
        """
        Reprocesa uno o mas certificados (regenera PEM y KEY).

        Parametros esperados en qdict:
        - ids: Lista JSON de IDs a reprocesar
        """
        q = kwargs.get('qdict', {})
        ids_str = q.get('ids', '[]')

        try:
            ids = json.loads(ids_str)
        except json.JSONDecodeError:
            return {'error': 'IDs invalidos'}, args, kwargs

        if not ids:
            return {'error': 'No se especificaron certificados para reprocesar'}, args, kwargs

        try:
            processed = 0
            errors = []

            for cert_id in ids:
                try:
                    cert = Certificate.objects.get(pk=cert_id)

                    # Eliminar archivos PEM/KEY existentes
                    if cert.pem_file:
                        try:
                            cert.pem_file.delete(save=False)
                        except Exception:
                            pass
                    if cert.key_file:
                        try:
                            cert.key_file.delete(save=False)
                        except Exception:
                            pass

                    cert.pem_file = None
                    cert.key_file = None
                    cert.estado = 'pendiente'
                    cert.error_mensaje = None
                    cert.save()

                    success, message = certificate_manager.process_certificate(cert)
                    if success:
                        processed += 1
                    else:
                        errors.append(f'{cert.nombre}: {message}')

                except Certificate.DoesNotExist:
                    errors.append(f'ID {cert_id}: No encontrado')

            if errors:
                return {
                    'warning': f'{processed} procesado(s), {len(errors)} error(es): {"; ".join(errors[:3])}'
                }, args, kwargs

            return {'success': f'{processed} certificado(s) reprocesado(s) exitosamente'}, args, kwargs

        except Exception as e:
            logger.exception("Error reprocesando certificados")
            return {'error': f'Error al reprocesar certificados: {str(e)}'}, args, kwargs

    def verify_certificate(self, *args, **kwargs) -> tuple:
        """
        Verifica que un certificado este correctamente configurado.

        Parametros esperados en qdict:
        - id: ID del certificado a verificar
        """
        q = kwargs.get('qdict', {})
        cert_id = q.get('id')

        if not cert_id:
            return {'error': 'ID de certificado requerido'}, args, kwargs

        try:
            cert = Certificate.objects.get(pk=cert_id)

            checks = []

            # Verificar estado
            if cert.estado != 'activo':
                checks.append(f'Estado: {cert.estado} (esperado: activo)')

            # Verificar archivos
            if not cert.pem_file:
                checks.append('Archivo PEM no generado')
            if not cert.key_file:
                checks.append('Archivo KEY no generado')

            # Verificar vencimiento
            if cert.fecha_vencimiento:
                if cert.fecha_vencimiento < timezone.now():
                    checks.append('Certificado VENCIDO')
                elif cert.days_until_expiry() <= 30:
                    checks.append(f'Vence en {cert.days_until_expiry()} dias')

            # Intentar leer los archivos
            if cert.pem_file and cert.key_file:
                try:
                    with open(cert.pem_file.path, 'rb') as f:
                        pem_content = f.read()
                    with open(cert.key_file.path, 'rb') as f:
                        key_content = f.read()

                    if b'-----BEGIN CERTIFICATE-----' not in pem_content:
                        checks.append('Archivo PEM no contiene certificado valido')
                    if b'PRIVATE KEY' not in key_content:
                        checks.append('Archivo KEY no contiene clave privada valida')

                except FileNotFoundError as e:
                    checks.append(f'Archivo no encontrado: {str(e)}')
                except Exception as e:
                    checks.append(f'Error leyendo archivos: {str(e)}')

            if checks:
                return {'warning': 'Problemas encontrados: ' + '; '.join(checks)}, args, kwargs

            return {'success': 'Certificado verificado correctamente. Listo para firmar documentos.'}, args, kwargs

        except Certificate.DoesNotExist:
            return {'error': 'Certificado no encontrado'}, args, kwargs
        except Exception as e:
            logger.exception("Error verificando certificado")
            return {'error': f'Error al verificar certificado: {str(e)}'}, args, kwargs
