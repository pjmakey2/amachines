"""
Comando de Django management para crear el usuario administrador por defecto 'amadmin'
con contraseña autogenerada guardada en el archivo .amadmin
"""
import os
import secrets
import string
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea el usuario administrador por defecto "amadmin" con contraseña autogenerada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación del usuario si ya existe'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=20,
            help='Longitud de la contraseña (default: 20)'
        )

    def generate_password(self, length=20):
        """Genera una contraseña segura aleatoria."""
        # Caracteres permitidos: letras, números y algunos símbolos
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*'

        # Asegurar que la contraseña tenga al menos:
        # - 1 mayúscula, 1 minúscula, 1 número, 1 símbolo
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice('!@#$%^&*')
        ]

        # Completar el resto de la contraseña
        password += [secrets.choice(alphabet) for _ in range(length - 4)]

        # Mezclar los caracteres
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    def save_password_to_file(self, username, password):
        """Guarda la contraseña en el archivo .amadmin en la raíz del proyecto."""
        # Obtener la ruta raíz del proyecto (donde está manage.py)
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        amadmin_file = base_dir / '.amadmin'

        try:
            with open(amadmin_file, 'w') as f:
                f.write(f"Usuario: {username}\n")
                f.write(f"Contraseña: {password}\n")
                f.write(f"\n")
                f.write(f"IMPORTANTE: Este archivo contiene credenciales sensibles.\n")
                f.write(f"NO lo compartas ni lo subas al repositorio.\n")

            # Establecer permisos restrictivos (solo lectura/escritura para el propietario)
            os.chmod(amadmin_file, 0o600)

            return str(amadmin_file)
        except Exception as e:
            raise Exception(f"Error al guardar el archivo .amadmin: {e}")

    def handle(self, *args, **options):
        username = 'amadmin'
        force = options['force']
        password_length = options['length']

        # Verificar si el usuario ya existe
        user_exists = User.objects.filter(username=username).exists()

        if user_exists and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'El usuario "{username}" ya existe. '
                    f'Usa --force para recrearlo.'
                )
            )
            return

        # Generar contraseña
        password = self.generate_password(password_length)

        # Crear o actualizar usuario
        if user_exists and force:
            self.stdout.write(f'Eliminando usuario existente "{username}"...')
            User.objects.filter(username=username).delete()

        self.stdout.write(f'Creando usuario administrador "{username}"...')
        user = User.objects.create_superuser(
            username=username,
            email='admin@toca3d.local',
            password=password,
            first_name='Admin',
            last_name='Master'
        )

        # Guardar contraseña en archivo
        try:
            file_path = self.save_password_to_file(username, password)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Usuario "{username}" creado exitosamente!'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Credenciales guardadas en: {file_path}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ IMPORTANTE: Guarda estas credenciales en un lugar seguro.'
                )
            )
            self.stdout.write(f'\nUsuario: {username}')
            self.stdout.write(f'Contraseña: {password}')
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ El archivo .amadmin contiene credenciales sensibles.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ NO lo subas al repositorio (verificar .gitignore)'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ Error al guardar credenciales: {e}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    f'\nUsuario creado pero sin archivo de respaldo.'
                )
            )
            self.stdout.write(f'Credenciales (guárdalas manualmente):')
            self.stdout.write(f'Usuario: {username}')
            self.stdout.write(f'Contraseña: {password}')
